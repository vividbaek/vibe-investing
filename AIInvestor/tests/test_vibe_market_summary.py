"""§Vibe — DeepSeek 시장 요약 (cron 2회/일) 테스트."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services.vibe import market_summary as ms


def _mk_config(**overrides) -> SimpleNamespace:
    base = dict(
        deepseek_api_key="dk",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        storage_account_name="acct",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _mk_snapshot(**overrides) -> dict:
    base = {
        "ts": "2026-06-06T10:12:22+00:00",
        "risk_score": 27,
        "risk_label": "RISK_OFF",
        "vix": 21.5,
        "indices": [
            {"ticker": "SPY", "name": "S&P 500", "price": 737.55, "chg_pct": -2.58},
            {"ticker": "QQQ", "name": "나스닥100", "price": 705.06, "chg_pct": -4.8},
        ],
        "sectors": [
            {"ticker": "XLK", "name": "기술", "chg_pct": -6.66},
            {"ticker": "XLF", "name": "금융", "chg_pct": 0.21},
            {"ticker": "XLP", "name": "필수소비재", "chg_pct": 1.71},
        ],
        "movers": {
            "gainers": [{"ticker": "COO", "chg_pct": 10.5},
                         {"ticker": "ABM", "chg_pct": 8.2}],
            "losers": [{"ticker": "PL", "chg_pct": -25.4},
                        {"ticker": "POET", "chg_pct": -18.1}],
        },
    }
    base.update(overrides)
    return base


class TestBuildUserPrompt:
    def test_includes_all_facts(self) -> None:
        snap = _mk_snapshot()
        p = ms._build_user_prompt(snap, "open")
        # 핵심 숫자 모두 포함
        assert "27/100" in p
        assert "RISK_OFF" in p
        assert "21.5" in p
        assert "-6.66" in p
        assert "COO" in p
        assert "PL" in p

    def test_kind_open_vs_close(self) -> None:
        snap = _mk_snapshot()
        p_open = ms._build_user_prompt(snap, "open")
        p_close = ms._build_user_prompt(snap, "close")
        assert "시작" in p_open
        assert "마감" in p_close

    def test_handles_empty_snapshot(self) -> None:
        # 부분적인 스냅샷도 깨지지 않게
        p = ms._build_user_prompt({}, "open")
        assert "—" in p  # 빈 자리 dash

    def test_no_advice_rule_present(self) -> None:
        p = ms._build_user_prompt(_mk_snapshot(), "open")
        assert "매수 / 매도" in p or "권한다 / 매수" in p
        assert "예측" in p


class TestRefreshMarketSummary:
    def test_skips_when_no_config(self) -> None:
        cfg = _mk_config(deepseek_api_key="")
        result = asyncio.run(ms.refresh_market_summary(cfg))
        assert result == {"skipped": "missing-config"}

    def test_skips_when_no_market_snapshot(self) -> None:
        async def fake_load(account, path, *, default=None, credential=None):
            return None

        with patch("services.vibe.blob_state.load_json", side_effect=fake_load):
            result = asyncio.run(ms.refresh_market_summary(_mk_config(),
                                                            kind="open"))
        assert result["skipped"] == "no-market-snapshot"
        assert result["kind"] == "open"

    def test_deepseek_failure_returns_error(self) -> None:
        snap = _mk_snapshot()

        async def fake_load(account, path, *, default=None, credential=None):
            return snap

        async def fake_call(api_key, base_url, model, prompt):
            raise RuntimeError("api down")

        with patch("services.vibe.blob_state.load_json", side_effect=fake_load), \
             patch.object(ms, "_call_deepseek", side_effect=fake_call):
            result = asyncio.run(ms.refresh_market_summary(_mk_config(),
                                                            kind="close"))
        assert result["error"] == "deepseek-failed"

    def test_empty_summary_returns_error(self) -> None:
        snap = _mk_snapshot()

        async def fake_load(account, path, *, default=None, credential=None):
            return snap

        async def fake_call(*a, **k):
            return "   "  # whitespace only

        with patch("services.vibe.blob_state.load_json", side_effect=fake_load), \
             patch.object(ms, "_call_deepseek", side_effect=fake_call):
            result = asyncio.run(ms.refresh_market_summary(_mk_config()))
        assert result["error"] == "empty-summary"

    def test_happy_path_saves_blob(self) -> None:
        snap = _mk_snapshot()
        saved: list[tuple] = []

        async def fake_load(account, path, *, default=None, credential=None):
            return snap

        async def fake_save(account, path, payload, credential=None):
            saved.append((path, payload))

        async def fake_call(api_key, base_url, model, prompt):
            return "기술주가 -6.66% 하락하며 시장이 위험 회피 분위기로 전환됐다. VIX 는 21.5 로 상승."

        with patch("services.vibe.blob_state.load_json", side_effect=fake_load), \
             patch("services.vibe.blob_state.save_json", side_effect=fake_save), \
             patch.object(ms, "_call_deepseek", side_effect=fake_call):
            result = asyncio.run(ms.refresh_market_summary(_mk_config(), kind="open"))

        assert result["skipped"] is False
        assert result["regime"] == "RISK_OFF"
        assert len(saved) == 1
        path, payload = saved[0]
        assert path == ms.SUMMARY_BLOB_PATH
        assert payload["kind"] == "open"
        assert payload["regime"] == "RISK_OFF"
        assert "기술주" in payload["summary_ko"]

    def test_auto_kind_picks_open_during_market(self) -> None:
        """UTC 14 시 (장 중) → 'open' 으로 분류."""
        snap = _mk_snapshot()
        captured: dict = {}

        async def fake_load(account, path, *, default=None, credential=None):
            return snap

        async def fake_save(*a, **k):
            pass

        async def fake_call(*a, **k):
            return "요약"

        from datetime import datetime, timezone
        fake_now = datetime(2026, 6, 6, 14, 0, tzinfo=timezone.utc)
        with patch("services.vibe.market_summary.datetime") as mock_dt, \
             patch("services.vibe.blob_state.load_json", side_effect=fake_load), \
             patch("services.vibe.blob_state.save_json", side_effect=fake_save), \
             patch.object(ms, "_call_deepseek", side_effect=fake_call):
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = asyncio.run(ms.refresh_market_summary(_mk_config(), kind="auto"))
        assert result["kind"] == "open"

    def test_auto_kind_picks_close_after_market(self) -> None:
        """UTC 22 시 (마감 후) → 'close'."""
        snap = _mk_snapshot()

        async def fake_load(*a, **k): return snap
        async def fake_save(*a, **k): pass
        async def fake_call(*a, **k): return "요약"

        from datetime import datetime, timezone
        fake_now = datetime(2026, 6, 6, 22, 0, tzinfo=timezone.utc)
        with patch("services.vibe.market_summary.datetime") as mock_dt, \
             patch("services.vibe.blob_state.load_json", side_effect=fake_load), \
             patch("services.vibe.blob_state.save_json", side_effect=fake_save), \
             patch.object(ms, "_call_deepseek", side_effect=fake_call):
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = asyncio.run(ms.refresh_market_summary(_mk_config(), kind="auto"))
        assert result["kind"] == "close"
