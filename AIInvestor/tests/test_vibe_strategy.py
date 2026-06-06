"""§Vibe P1 — vendored 전략 엔진 + Azure 어댑팅 검증.

- ARDS 의 _load_state/_save_state 가 injected callback 으로 우회되는지
- AMQS strategy 가 합성 가격 데이터로 처음부터 끝까지 도는지
- Blob state load/save 가 mock azure client 와 함께 동작하는지
- runner.build_ards 가 상태를 Blob ↔ memory ↔ ARDS build 사이를 매개하는지
"""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from services.vibe import blob_state, runner
from services.vibe.ards import run as ards_run
from services.vibe.ards import classifier as ards_classifier
from services.vibe.amqs import strategy as amqs


# ──────────────────────────────────────────────────────────────────────────────
# ARDS — state injection
# ──────────────────────────────────────────────────────────────────────────────
class TestArdsStateInjection:
    def teardown_method(self) -> None:
        # 다른 테스트 영향 방지
        ards_run.configure_state_io(loader=None, saver=None)

    def test_loader_callback_overrides_file(self, tmp_path) -> None:
        injected = {"committed": "DOWNTREND", "since": "2026-01-01",
                    "candidate": None, "count": 0}
        ards_run.configure_state_io(loader=lambda: injected, saver=lambda s: None)
        out = ards_run._load_state()
        assert out == injected

    def test_saver_callback_overrides_file(self) -> None:
        captured: list[dict] = []
        ards_run.configure_state_io(
            loader=lambda: {"committed": None, "since": None,
                            "candidate": None, "count": 0},
            saver=lambda s: captured.append(dict(s)),
        )
        ards_run._save_state({"committed": "EXPANSION", "since": "2026-06-06",
                              "candidate": None, "count": 0})
        assert len(captured) == 1
        assert captured[0]["committed"] == "EXPANSION"

    def test_loader_returns_default_when_no_callback_no_file(self,
                                                              monkeypatch) -> None:
        ards_run.configure_state_io(loader=None, saver=None)
        # 파일이 없는 경로로 강제
        monkeypatch.setattr(ards_run.config, "STATE_JSON",
                            "data/_does_not_exist.json")
        state = ards_run._load_state()
        assert state == {"committed": None, "since": None,
                         "candidate": None, "count": 0}


# ──────────────────────────────────────────────────────────────────────────────
# ARDS — classifier raw_classify (pure logic, no IO)
# ──────────────────────────────────────────────────────────────────────────────
class TestArdsClassifier:
    # _measure 의 실제 출력 키와 동일하게 구성 (classifier.py:64-70)
    def _mk_measure(self, **overrides) -> dict:
        base = {
            "tape_dd": -3.0,
            "breadth": 60.0,
            "complex_dd": -4.0,
            "trend_broken": False,
            "idx_below_200": False,
            "idx_deadcross": False,
            "breadth_weak": False,
            "decline_score": 20.0,
            "oversold_score": 20.0,
            "idx_rsi": 50.0,
            "price_stress": 25.0,
        }
        base.update(overrides)
        return base

    def test_returns_valid_enum_value(self) -> None:
        m = self._mk_measure()
        result = ards_classifier.raw_classify(30.0, m, None)
        assert result in {"UPTREND_HEALTHY", "CORRECTION", "OVERSOLD_BOUNCE",
                          "DOWNTREND_DISTRIBUTION", "RECESSION_REBALANCE"}

    def test_recession_when_macro_high_and_stress(self) -> None:
        # 거시 침체 임계값(55) 초과 + 깊은 drawdown → RECESSION_REBALANCE
        m = self._mk_measure(tape_dd=-15.0, trend_broken=True,
                              breadth=20.0, breadth_weak=True)
        result = ards_classifier.raw_classify(80.0, m, None)
        assert result == "RECESSION_REBALANCE"

    def test_uptrend_healthy_when_calm(self) -> None:
        m = self._mk_measure()  # 기본값이 평온한 상태
        result = ards_classifier.raw_classify(20.0, m, None)
        assert result == "UPTREND_HEALTHY"


# ──────────────────────────────────────────────────────────────────────────────
# AMQS — end-to-end with synthetic prices (no network)
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_prices(tickers: list[str], n_days: int = 504,
                       seed: int = 42) -> pd.DataFrame:
    """결정적 가격 series 생성 — 각 티커에 약간씩 다른 trend + noise."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=datetime(2026, 6, 6), periods=n_days)
    cols = {}
    for i, t in enumerate(tickers):
        drift = 0.0003 + i * 0.00002
        vol = 0.012 + (i % 5) * 0.002
        rets = rng.normal(drift, vol, n_days)
        prices = 100.0 * np.exp(np.cumsum(rets))
        cols[t] = prices
    return pd.DataFrame(cols, index=dates)


class TestAmqsEndToEnd:
    def test_runs_with_synthetic_prices(self) -> None:
        tickers = list(amqs.AI_INFRA_TICKERS)
        # AMQS 가 QQQ/VIX 도 받으므로 함께 합성
        all_syms = tickers + ["__QQQ__", "__VIX__"]
        df_full = _synthetic_prices(all_syms, n_days=520)
        prices_df = df_full[tickers]
        qqq = df_full["__QQQ__"]
        # VIX 는 음수 수익률 → 가격 → 다시 양수화 + 범위 압축으로 VIX-like 시리즈로
        vix_returns = np.diff(np.log(df_full["__VIX__"].values), prepend=np.log(20.0))
        vix_synth = 18.0 + 4.0 * vix_returns.cumsum() / max(1.0,
                                                              vix_returns.std() * 30)
        vix = pd.Series(np.clip(vix_synth, 10.0, 60.0), index=df_full.index,
                        name="VIX")

        df, regime = amqs.run_amqs_ai_infra(
            prices=prices_df, qqq=qqq, vix=vix,
        )
        # 결과 형태 검증
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(tickers)  # 모든 티커 행 존재
        assert regime.label in {"RISK_ON", "RISK_OFF", "DEFENSIVE"}
        assert "total_100" in df.columns
        assert "signal" in df.columns
        # 신호값이 enum 안인지
        valid_signals = {"CENTER", "SATELLITE", "TACTICAL", "DIP_BUY",
                         "REDUCE", "EXIT"}
        for sig in df["signal"]:
            assert sig in valid_signals or sig == "" or sig is None
        # 점수가 0~100 범위
        for s in df["total_100"]:
            if s is not None and not (isinstance(s, float) and math.isnan(s)):
                assert 0 <= s <= 100

    def test_universe_count_19(self) -> None:
        assert len(amqs.AI_INFRA_TICKERS) == 19


# ──────────────────────────────────────────────────────────────────────────────
# Blob state helper — mocked azure clients
# ──────────────────────────────────────────────────────────────────────────────
class _FakeBlob:
    def __init__(self, body: bytes | None = None, raise_not_found: bool = False) -> None:
        self._body = body
        self._raise = raise_not_found
        self.uploaded: list[bytes] = []

    async def download_blob(self):
        if self._raise:
            from azure.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError()
        return self  # readall() lives on same object

    async def readall(self) -> bytes:
        return self._body or b""

    async def upload_blob(self, body, overwrite: bool = False) -> None:
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.uploaded.append(body)


class _FakeContainer:
    def __init__(self, blob: _FakeBlob) -> None:
        self._blob = blob

    async def create_container(self) -> None:
        pass

    def get_blob_client(self, path: str):
        return self._blob


class _FakeSvc:
    def __init__(self, blob: _FakeBlob) -> None:
        self._blob = blob
        self._container = _FakeContainer(blob)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    def get_blob_client(self, container: str, path: str):
        return self._blob

    def get_container_client(self, name: str):
        return self._container


class _FakeCreds:
    async def close(self) -> None:
        pass


class TestBlobState:
    def test_load_returns_default_when_blob_missing(self) -> None:
        blob = _FakeBlob(raise_not_found=True)
        svc = _FakeSvc(blob)
        # json.loads 전역 patching 은 azure SDK 내부 avro 파서까지 망가뜨림 →
        # default 반환만 결과로 검증.
        with patch("azure.identity.aio.DefaultAzureCredential",
                   return_value=_FakeCreds()), \
             patch("azure.storage.blob.aio.BlobServiceClient",
                   return_value=svc):
            result = asyncio.run(blob_state.load_json(
                "acct", "test.json", default={"x": 1},
            ))
        assert result == {"x": 1}

    def test_load_parses_existing_blob(self) -> None:
        payload = {"committed": "EXPANSION", "since": "2026-06-06"}
        blob = _FakeBlob(body=json.dumps(payload).encode("utf-8"))
        svc = _FakeSvc(blob)
        with patch("azure.identity.aio.DefaultAzureCredential",
                   return_value=_FakeCreds()), \
             patch("azure.storage.blob.aio.BlobServiceClient",
                   return_value=svc):
            result = asyncio.run(blob_state.load_json(
                "acct", "ards.json", default={},
            ))
        assert result == payload

    def test_save_writes_json(self) -> None:
        blob = _FakeBlob()
        svc = _FakeSvc(blob)
        with patch("azure.identity.aio.DefaultAzureCredential",
                   return_value=_FakeCreds()), \
             patch("azure.storage.blob.aio.BlobServiceClient",
                   return_value=svc):
            asyncio.run(blob_state.save_json(
                "acct", "out.json", {"a": 1, "b": "텍스트"},
            ))
        assert len(blob.uploaded) == 1
        loaded_back = json.loads(blob.uploaded[0].decode("utf-8"))
        assert loaded_back == {"a": 1, "b": "텍스트"}

    def test_load_handles_corrupt_blob_gracefully(self) -> None:
        blob = _FakeBlob(body=b"{ this is not json")
        svc = _FakeSvc(blob)
        with patch("azure.identity.aio.DefaultAzureCredential",
                   return_value=_FakeCreds()), \
             patch("azure.storage.blob.aio.BlobServiceClient",
                   return_value=svc):
            result = asyncio.run(blob_state.load_json(
                "acct", "corrupt.json", default={"fallback": True},
            ))
        assert result == {"fallback": True}


# ──────────────────────────────────────────────────────────────────────────────
# Runner — ARDS state Blob roundtrip
# ──────────────────────────────────────────────────────────────────────────────
class TestRunnerArdsStateRoundtrip:
    def test_state_flows_blob_to_ards_to_blob(self) -> None:
        """build_ards 가 (1) Blob 에서 상태 로드 → (2) ards_run.build 호출 시
        configure_state_io 가 주입한 loader 가 그 상태를 반환 → (3) ARDS 가
        _save_state 로 state 수정 → (4) saver callback 으로 memory 에 기록 →
        (5) Blob 에 최종 flush 되는지 검증."""
        initial = {"committed": "EXPANSION", "since": "2026-05-01",
                   "candidate": None, "count": 0}
        captured_state_after_build: dict = {}

        async def fake_load_json(account, path, *, default=None, credential=None):
            assert path == runner.ARDS_STATE_PATH
            return dict(initial)

        save_calls: list[tuple[str, dict]] = []

        async def fake_save_json(account, path, payload, credential=None):
            save_calls.append((path, payload))

        def fake_ards_build():
            # 이 시점에 loader 가 작동해야 함
            loaded = ards_run._load_state()
            assert loaded == initial
            # ARDS 내부에서 일어나는 일을 흉내: 상태 변경 후 save
            new_state = {**loaded, "committed": "CORRECTION",
                         "since": "2026-06-06"}
            ards_run._save_state(new_state)
            captured_state_after_build.update(new_state)
            return {"asof": "2026-06-06", "verdict": {"state": "CORRECTION"}}

        with patch.object(blob_state, "load_json", side_effect=fake_load_json), \
             patch.object(blob_state, "save_json", side_effect=fake_save_json), \
             patch.object(ards_run, "build", side_effect=fake_ards_build):
            result = asyncio.run(runner.build_ards("acct"))

        assert result["verdict"]["state"] == "CORRECTION"
        # Blob 에 state + signals 두 번 저장
        paths_saved = {p for p, _ in save_calls}
        assert runner.ARDS_STATE_PATH in paths_saved
        assert runner.ARDS_SIGNALS_PATH in paths_saved
        # 저장된 state 가 build() 안에서 수정된 최신값과 같은지
        saved_state = next(payload for p, payload in save_calls
                           if p == runner.ARDS_STATE_PATH)
        assert saved_state["committed"] == "CORRECTION"
        assert saved_state["since"] == "2026-06-06"
        # 끝난 후 callback 이 해제됐는지 (다음 호출 격리)
        assert ards_run._state_loader is None
        assert ards_run._state_saver is None


class TestRunnerBuildAmqs:
    def test_build_amqs_calls_strategy_and_persists(self) -> None:
        fake_payload = {"as_of": "2026-06-06T00:00:00+00:00",
                        "regime": {"label": "RISK_ON", "tradeable": True}}

        save_calls: list[tuple[str, dict]] = []

        async def fake_save_json(account, path, payload, credential=None):
            save_calls.append((path, payload))

        with patch.object(runner, "_amqs_build_sync",
                          return_value=fake_payload), \
             patch.object(blob_state, "save_json", side_effect=fake_save_json):
            result = asyncio.run(runner.build_amqs("acct"))

        assert result == fake_payload
        assert len(save_calls) == 1
        assert save_calls[0][0] == runner.AMQS_SIGNALS_PATH
        assert save_calls[0][1] == fake_payload


class TestRunnerCombinedSignals:
    def test_failure_of_one_engine_does_not_block_other(self) -> None:
        ards_payload = {"verdict": {"state": "EXPANSION"}}
        save_calls: list[tuple[str, dict]] = []

        async def fake_build_ards(account):
            return ards_payload

        async def fake_build_amqs(account, market_caps=None):
            raise RuntimeError("yfinance down")

        async def fake_save_json(account, path, payload, credential=None):
            save_calls.append((path, payload))

        with patch.object(runner, "build_ards", side_effect=fake_build_ards), \
             patch.object(runner, "build_amqs", side_effect=fake_build_amqs), \
             patch.object(blob_state, "save_json", side_effect=fake_save_json):
            out = asyncio.run(runner.build_combined_signals("acct"))

        assert out["ards"] == ards_payload
        assert out["amqs"] is None
        assert len(out["errors"]) == 1
        assert out["errors"][0]["engine"] == "amqs"
        # combined latest.json 은 저장됐어야 함
        assert any(p == runner.COMBINED_SIGNALS_PATH for p, _ in save_calls)
