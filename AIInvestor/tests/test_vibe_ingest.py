"""§Vibe P4 — ingest + search + track 단위 테스트.

ingest 는 CF Pages Functions (shared/ingest.ts) 와 동일 contract.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from unittest.mock import patch

import pytest

from services.vibe import ingest, search_track


# ──────────────────────────────────────────────────────────────────────────────
# HMAC / freshness
# ──────────────────────────────────────────────────────────────────────────────
class TestFreshTimestamp:
    def test_within_tolerance(self) -> None:
        now = 1_700_000_000
        assert ingest.is_fresh_timestamp(str(now - 100), now) is True

    def test_outside_tolerance(self) -> None:
        now = 1_700_000_000
        assert ingest.is_fresh_timestamp(str(now - 500), now) is False

    def test_invalid_format(self) -> None:
        assert ingest.is_fresh_timestamp("abc", 1_700_000_000) is False
        assert ingest.is_fresh_timestamp(None, 1_700_000_000) is False
        assert ingest.is_fresh_timestamp("", 1_700_000_000) is False

    def test_future_within_tolerance_ok(self) -> None:
        now = 1_700_000_000
        assert ingest.is_fresh_timestamp(str(now + 200), now) is True


class TestVerifySignature:
    def _sign(self, secret: str, ts: str, body: bytes) -> str:
        return hmac.new(secret.encode(), f"{ts}.".encode() + body,
                        hashlib.sha256).hexdigest()

    def test_valid_signature(self) -> None:
        body = b'{"ts":"x","market_summary":"","items":[]}'
        ts = "1700000000"
        sig = self._sign("secret", ts, body)
        assert ingest.verify_signature("secret", ts, body, sig) is True

    def test_wrong_secret(self) -> None:
        body = b'{}'
        ts = "1700000000"
        sig = self._sign("secret", ts, body)
        assert ingest.verify_signature("wrong", ts, body, sig) is False

    def test_wrong_body(self) -> None:
        ts = "1700000000"
        sig = self._sign("secret", ts, b'{"a":1}')
        assert ingest.verify_signature("secret", ts, b'{"a":2}', sig) is False

    def test_uppercase_sig_accepted(self) -> None:
        body = b'{}'
        ts = "1700000000"
        sig = self._sign("secret", ts, body)
        assert ingest.verify_signature("secret", ts, body, sig.upper()) is True

    def test_none_sig_rejected(self) -> None:
        assert ingest.verify_signature("secret", "1700000000", b'{}', None) is False

    def test_nonhex_sig_rejected(self) -> None:
        assert ingest.verify_signature("secret", "1700000000", b'{}',
                                        "zzzzzzz") is False


# ──────────────────────────────────────────────────────────────────────────────
# Payload validation
# ──────────────────────────────────────────────────────────────────────────────
class TestValidatePayload:
    def test_valid_minimal(self) -> None:
        ok, msg, normalized = ingest.validate_payload({
            "ts": "2026-06-06T00:00:00Z",
            "market_summary": "",
            "items": [],
        })
        assert ok is True
        assert msg == ""
        assert normalized["items"] == []

    def test_valid_with_items(self) -> None:
        ok, msg, normalized = ingest.validate_payload({
            "ts": "2026-06-06T00:00:00Z",
            "market_summary": "장 상승",
            "items": [{
                "id": "abc", "ts": 1700000000, "title_ko": "T",
                "summary_ko": "S", "category": "AI", "tickers": ["NVDA"],
                "source": "Reuters", "url": "https://x",
            }],
        })
        assert ok is True
        assert len(normalized["items"]) == 1
        assert normalized["items"][0]["category"] == "AI"

    def test_invalid_root(self) -> None:
        ok, msg, _ = ingest.validate_payload("not a dict")
        assert ok is False and "object" in msg

    def test_missing_market_summary(self) -> None:
        ok, msg, _ = ingest.validate_payload({"items": []})
        assert ok is False and "market_summary" in msg

    def test_items_not_array(self) -> None:
        ok, msg, _ = ingest.validate_payload({"market_summary": "",
                                              "items": {"oops": True}})
        assert ok is False

    def test_item_missing_id(self) -> None:
        ok, msg, _ = ingest.validate_payload({
            "market_summary": "",
            "items": [{"title_ko": "no id"}],
        })
        assert ok is False and "id" in msg

    def test_unknown_category_becomes_기타(self) -> None:
        ok, _, normalized = ingest.validate_payload({
            "market_summary": "",
            "items": [{"id": "x", "category": "MadeUp",
                       "title_ko": "T", "summary_ko": "S"}],
        })
        assert ok is True
        assert normalized["items"][0]["category"] == "기타"


# ──────────────────────────────────────────────────────────────────────────────
# Merge into existing
# ──────────────────────────────────────────────────────────────────────────────
class TestMergeIntoExisting:
    def test_merges_new_into_existing(self) -> None:
        existing = {"ts": "old", "market_summary": "이전",
                    "items": [{"id": "1", "ts": 1700000000,
                               "title_ko": "old", "summary_ko": "",
                               "category": "AI", "tickers": [],
                               "source": "", "url": ""}]}
        new = {"ts": "new", "market_summary": "최신",
               "items": [{"id": "2", "ts": 1700000100,
                          "title_ko": "new", "summary_ko": "",
                          "category": "AI", "tickers": [],
                          "source": "", "url": ""}]}
        merged = ingest.merge_into_existing(existing, new)
        ids = {it["id"] for it in merged["items"]}
        assert ids == {"1", "2"}
        assert merged["market_summary"] == "최신"
        assert merged["ts"] == "new"

    def test_new_overwrites_same_id(self) -> None:
        existing = {"items": [{"id": "1", "ts": 1, "title_ko": "old",
                               "summary_ko": "", "category": "AI",
                               "tickers": [], "source": "", "url": ""}]}
        new = {"market_summary": "", "items": [{
            "id": "1", "ts": 2, "title_ko": "new", "summary_ko": "",
            "category": "AI", "tickers": [], "source": "", "url": "",
        }]}
        merged = ingest.merge_into_existing(existing, new)
        items_by_id = {it["id"]: it for it in merged["items"]}
        assert items_by_id["1"]["title_ko"] == "new"

    def test_empty_summary_keeps_existing(self) -> None:
        existing = {"market_summary": "유지", "items": []}
        new = {"market_summary": "", "items": []}
        merged = ingest.merge_into_existing(existing, new)
        assert merged["market_summary"] == "유지"

    def test_caps_at_max_items(self) -> None:
        existing_items = [{"id": str(i), "ts": i, "title_ko": "x",
                           "summary_ko": "", "category": "AI",
                           "tickers": [], "source": "", "url": ""}
                          for i in range(150)]
        existing = {"market_summary": "", "items": existing_items}
        new = {"market_summary": "", "items": []}
        merged = ingest.merge_into_existing(existing, new)
        assert len(merged["items"]) == ingest.MAX_ITEMS_KEPT

    def test_handles_none_existing(self) -> None:
        new = {"ts": "x", "market_summary": "최신",
               "items": [{"id": "a", "ts": 1, "title_ko": "T",
                          "summary_ko": "", "category": "AI",
                          "tickers": [], "source": "", "url": ""}]}
        merged = ingest.merge_into_existing(None, new)
        assert len(merged["items"]) == 1


# ──────────────────────────────────────────────────────────────────────────────
# handle_ingest_news — end-to-end with mocked Blob
# ──────────────────────────────────────────────────────────────────────────────
def _sign(secret: str, ts: str, body: bytes) -> str:
    return hmac.new(secret.encode(), f"{ts}.".encode() + body,
                    hashlib.sha256).hexdigest()


class TestHandleIngestNews:
    def test_no_secret_returns_500(self) -> None:
        status, body = asyncio.run(ingest.handle_ingest_news(
            "acct", "", "1700000000", "abc", b"{}",
        ))
        assert status == 500
        assert body["error"] == "ingest_not_configured"

    def test_stale_timestamp_returns_401(self) -> None:
        status, body = asyncio.run(ingest.handle_ingest_news(
            "acct", "secret", "1000000000", "abc", b"{}",
            now_sec=1700000000,
        ))
        assert status == 401
        assert "timestamp" in body["error"]

    def test_bad_signature_returns_401(self) -> None:
        ts = "1700000000"
        status, body = asyncio.run(ingest.handle_ingest_news(
            "acct", "secret", ts, "0" * 64, b'{"market_summary":"","items":[]}',
            now_sec=int(ts),
        ))
        assert status == 401
        assert "signature" in body["error"]

    def test_invalid_json_returns_400(self) -> None:
        ts = "1700000000"
        body = b"not json"
        sig = _sign("secret", ts, body)
        status, resp = asyncio.run(ingest.handle_ingest_news(
            "acct", "secret", ts, sig, body, now_sec=int(ts),
        ))
        assert status == 400
        assert resp["error"] == "invalid_json"

    def test_invalid_payload_returns_400(self) -> None:
        ts = "1700000000"
        body = json.dumps({"market_summary": 123, "items": []}).encode()
        sig = _sign("secret", ts, body)
        status, resp = asyncio.run(ingest.handle_ingest_news(
            "acct", "secret", ts, sig, body, now_sec=int(ts),
        ))
        assert status == 400

    def test_happy_path_persists_and_returns_count(self) -> None:
        ts = "1700000000"
        body_dict = {
            "ts": "2026-06-06T00:00:00Z",
            "market_summary": "장 상승",
            "items": [
                {"id": "a", "ts": 1700000000, "title_ko": "T", "summary_ko": "S",
                 "category": "AI", "tickers": ["NVDA"], "source": "R", "url": "u"},
                {"id": "b", "ts": 1700000001, "title_ko": "T2",
                 "summary_ko": "S2", "category": "반도체", "tickers": [],
                 "source": "R", "url": "u"},
            ],
        }
        body = json.dumps(body_dict, ensure_ascii=False).encode()
        sig = _sign("secret", ts, body)

        saved: list = []

        async def fake_save(account, path, payload, credential=None):
            saved.append((path, payload))

        async def fake_load(account, path, *, default=None, credential=None):
            return None

        with patch("services.vibe.blob_state.save_json", side_effect=fake_save), \
             patch("services.vibe.blob_state.load_json", side_effect=fake_load):
            status, resp = asyncio.run(ingest.handle_ingest_news(
                "acct", "secret", ts, sig, body, now_sec=int(ts),
            ))
        assert status == 200
        assert resp == {"ok": True, "ingested": 2}
        assert len(saved) == 1
        assert saved[0][0] == ingest.NEWS_BLOB_PATH
        assert len(saved[0][1]["items"]) == 2


# ──────────────────────────────────────────────────────────────────────────────
# search_track helpers
# ──────────────────────────────────────────────────────────────────────────────
class TestNormalizeTicker:
    def test_uppercases(self) -> None:
        assert search_track.normalize_ticker("nvda") == "NVDA"

    def test_strips_whitespace(self) -> None:
        assert search_track.normalize_ticker("  AAPL  ") == "AAPL"

    def test_too_long_rejected(self) -> None:
        assert search_track.normalize_ticker("A" * 20) is None

    def test_invalid_chars_rejected(self) -> None:
        assert search_track.normalize_ticker("NVDA;DROP") is None
        assert search_track.normalize_ticker("a b") is None

    def test_allows_special_index_chars(self) -> None:
        assert search_track.normalize_ticker("^GSPC") == "^GSPC"
        assert search_track.normalize_ticker("BRK-B") == "BRK-B"

    def test_empty_returns_none(self) -> None:
        assert search_track.normalize_ticker("") is None
        assert search_track.normalize_ticker("   ") is None


class TestExtractSignalsForTicker:
    def test_returns_empty_when_no_payload(self) -> None:
        assert search_track.extract_signals_for_ticker(None, "NVDA") == []

    def test_extracts_ards_complex_row(self) -> None:
        payload = {
            "ards": {"complex": [{"ticker": "NVDA", "decline_score": 30,
                                  "oversold_score": 20, "rsi14": 55,
                                  "dd_from_high": -5}]},
            "amqs": {"metrics": []},
        }
        result = search_track.extract_signals_for_ticker(payload, "NVDA")
        assert len(result) == 1
        assert result[0]["strategy"] == "ARDS"

    def test_extracts_amqs_row(self) -> None:
        payload = {
            "ards": None,
            "amqs": {"metrics": [{"ticker": "NVDA", "signal": "CENTER",
                                  "total_100": 85.5, "weight": 0.15,
                                  "reason": "강세"}]},
        }
        result = search_track.extract_signals_for_ticker(payload, "NVDA")
        assert len(result) == 1
        assert result[0]["strategy"] == "AMQS"
        assert result[0]["signal"] == "CENTER"

    def test_extracts_both_strategies(self) -> None:
        payload = {
            "ards": {"indices": [{"ticker": "^GSPC", "decline_score": 10}]},
            "amqs": {"metrics": []},
        }
        result = search_track.extract_signals_for_ticker(payload, "^GSPC")
        assert len(result) == 1
        assert result[0]["ticker"] == "^GSPC"

    def test_unknown_ticker_empty(self) -> None:
        payload = {"ards": {"complex": [{"ticker": "AAPL"}]}, "amqs": {}}
        assert search_track.extract_signals_for_ticker(payload, "MSFT") == []


# ──────────────────────────────────────────────────────────────────────────────
# track — in-memory DAU/AU
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _clear_track_state():
    search_track._dau_today.clear()
    search_track._all_users.clear()
    yield
    search_track._dau_today.clear()
    search_track._all_users.clear()


class TestRecordVisit:
    def test_same_user_counted_once_per_day(self) -> None:
        async def noop(*a, **k):
            pass

        with patch.object(search_track, "_append_ndjson", side_effect=noop):
            r1 = asyncio.run(search_track.record_visit("acct", "1.1.1.1",
                                                       "UA", "salt"))
            r2 = asyncio.run(search_track.record_visit("acct", "1.1.1.1",
                                                       "UA", "salt"))
        assert r1["dau"] == 1
        assert r2["dau"] == 1  # same IP/UA → 같은 hash → 누적 안 늘림
        assert r2["total_au"] == 1

    def test_different_users_increase_dau(self) -> None:
        async def noop(*a, **k):
            pass

        with patch.object(search_track, "_append_ndjson", side_effect=noop):
            asyncio.run(search_track.record_visit("acct", "1.1.1.1", "UA", "s"))
            r = asyncio.run(search_track.record_visit("acct", "2.2.2.2", "UA", "s"))
        assert r["dau"] == 2
        assert r["total_au"] == 2

    def test_append_failure_does_not_block(self) -> None:
        async def failing(*a, **k):
            raise RuntimeError("blob down")

        with patch.object(search_track, "_append_ndjson", side_effect=failing):
            r = asyncio.run(search_track.record_visit("acct", "1.1.1.1",
                                                      "UA", "salt"))
        assert r["dau"] == 1  # 메모리 카운트는 진행
