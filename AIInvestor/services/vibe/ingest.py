"""§Vibe P4 — POST /api/vibe/ingest/news.

Cloudflare Pages Functions (functions/api/ingest/news.ts) 와 동일 contract:
  - X-Timestamp(unix sec), X-Signature = hex(HMAC_SHA256(secret, "<ts>.<body>"))
  - |now - ts| ≤ 300s
  - 카테고리 화이트리스트 동일 (거시경제|실적|반도체|AI|금리|지정학|기타)

저장:
  - news/summary-latest.json: { ts, market_summary, items: [...] }
  - items 는 batch 간 merge (id 로 dedupe, 최신 100 건 keep)
  - market_summary 는 비어있지 않은 batch 만 갱신
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

TIMESTAMP_TOLERANCE_SEC = 300
NEWS_BLOB_PATH = "news/summary-latest.json"
MAX_ITEMS_KEPT = 100

ALLOWED_CATEGORIES = {"거시경제", "실적", "반도체", "AI", "금리", "지정학", "기타"}


# ──────────────────────────────────────────────────────────────────────────────
# HMAC verification (ingest 와 동일 로직)
# ──────────────────────────────────────────────────────────────────────────────
def is_fresh_timestamp(timestamp: str | None, now_sec: int,
                       tolerance_sec: int = TIMESTAMP_TOLERANCE_SEC) -> bool:
    if not timestamp:
        return False
    s = timestamp.strip()
    if not s.isdigit() or len(s) > 15:
        return False
    try:
        ts = int(s)
    except ValueError:
        return False
    return abs(now_sec - ts) <= tolerance_sec


def verify_signature(secret: str, timestamp: str, raw_body: bytes,
                     provided_sig: str | None) -> bool:
    if not provided_sig:
        return False
    sig = provided_sig.strip().lower()
    if not all(c in "0123456789abcdef" for c in sig):
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


# ──────────────────────────────────────────────────────────────────────────────
# Payload validation (validateNewsPayload 와 등가)
# ──────────────────────────────────────────────────────────────────────────────
def _as_str(v: Any) -> str:
    if isinstance(v, str):
        return v
    if v is None:
        return ""
    return str(v)


def validate_payload(obj: Any) -> tuple[bool, str, dict[str, Any]]:
    """(ok, error_msg, normalized) — error_msg 는 ok=True 시 ""."""
    if not isinstance(obj, dict):
        return False, "body must be a JSON object", {}
    if not isinstance(obj.get("market_summary"), str):
        return False, "market_summary must be a string", {}
    items = obj.get("items")
    if not isinstance(items, list):
        return False, "items must be an array", {}

    out_items: list[dict[str, Any]] = []
    for i, raw in enumerate(items):
        if not isinstance(raw, dict):
            return False, f"items[{i}] must be an object", {}
        rid = _as_str(raw.get("id")).strip()
        if not rid:
            return False, f"items[{i}].id is required", {}
        category = _as_str(raw.get("category"))
        if category not in ALLOWED_CATEGORIES:
            category = "기타"
        tickers = raw.get("tickers") or []
        if not isinstance(tickers, list):
            tickers = []
        out_items.append({
            "id": rid,
            "ts": raw.get("ts") if isinstance(raw.get("ts"), (int, float)) else _as_str(raw.get("ts")),
            "title_ko": _as_str(raw.get("title_ko")),
            "summary_ko": _as_str(raw.get("summary_ko")),
            "category": category,
            "tickers": [_as_str(t) for t in tickers if t],
            "source": _as_str(raw.get("source")),
            "url": _as_str(raw.get("url")),
        })

    return True, "", {
        "ts": _as_str(obj.get("ts")),
        "market_summary": obj["market_summary"],
        "items": out_items,
    }


# ──────────────────────────────────────────────────────────────────────────────
# RMW merge
# ──────────────────────────────────────────────────────────────────────────────
def _ts_sort_key(it: dict[str, Any]) -> float:
    """ts 를 정렬 키로. 문자열 ISO 면 datetime.fromisoformat 우회, int 면 그대로."""
    t = it.get("ts")
    if isinstance(t, (int, float)):
        return float(t)
    if isinstance(t, str) and t:
        try:
            from datetime import datetime
            return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def merge_into_existing(existing: dict[str, Any] | None,
                        new_payload: dict[str, Any]) -> dict[str, Any]:
    """기존 blob 의 items + 새 payload 의 items 를 dedupe (id) + 최신 N 건 keep.

    market_summary 는 새 payload 가 비어있지 않으면 교체, 아니면 기존 유지.
    ts 는 항상 새 payload 의 값.
    """
    existing = existing or {}
    existing_items = existing.get("items") or []
    if not isinstance(existing_items, list):
        existing_items = []

    by_id: dict[str, dict[str, Any]] = {}
    for it in existing_items:
        if isinstance(it, dict) and it.get("id"):
            by_id[str(it["id"])] = it
    for it in new_payload.get("items", []):
        by_id[str(it["id"])] = it  # new wins

    merged = sorted(by_id.values(), key=_ts_sort_key, reverse=True)[:MAX_ITEMS_KEPT]

    new_summary = new_payload.get("market_summary", "")
    summary = new_summary if new_summary.strip() else existing.get("market_summary", "")

    return {
        "ts": new_payload.get("ts") or existing.get("ts", ""),
        "market_summary": summary,
        "items": merged,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────
async def handle_ingest_news(
    account_name: str,
    secret: str,
    timestamp_header: str | None,
    signature_header: str | None,
    raw_body: bytes,
    *,
    now_sec: int | None = None,
) -> tuple[int, dict[str, Any]]:
    """(status_code, response_body). HTTP layer 가 직접 wrap."""
    if not secret:
        return 500, {"ok": False, "error": "ingest_not_configured"}
    now_sec = now_sec if now_sec is not None else int(time.time())

    if not is_fresh_timestamp(timestamp_header, now_sec):
        return 401, {"ok": False, "error": "invalid_or_stale_timestamp"}
    if not verify_signature(secret, timestamp_header, raw_body, signature_header):
        return 401, {"ok": False, "error": "invalid_signature"}

    try:
        parsed = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 400, {"ok": False, "error": "invalid_json"}

    ok, msg, normalized = validate_payload(parsed)
    if not ok:
        return 400, {"ok": False, "error": msg}

    try:
        from . import api_cache, blob_state
        existing = await blob_state.load_json(account_name, NEWS_BLOB_PATH, default=None)
        merged = merge_into_existing(existing, normalized)
        await blob_state.save_json(account_name, NEWS_BLOB_PATH, merged)
        # 다음 GET /api/vibe/news 호출이 stale 캐시 안 보게 invalidate
        api_cache.memo_for(NEWS_BLOB_PATH).invalidate()
    except Exception as exc:
        logger.exception("vibe.ingest: persist failed")
        return 500, {"ok": False, "error": "persist_failed", "detail": str(exc)[:200]}

    return 200, {"ok": True, "ingested": len(normalized["items"])}
