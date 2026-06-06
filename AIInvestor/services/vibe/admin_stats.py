"""§Vibe — admin dashboard 통계 (대시보드 섹션이 폴링).

- 각 cron 의 마지막 실행 결과를 vibe/admin/cron-status.json 에 기록
- 캐시 히트율 (per-path) 은 api_cache.get_cache_stats() 가 즉시 반환
- 최신 산출물 (signals/market/news) 의 timestamp 도 함께 노출

dashboard.html 의 별도 섹션이 fetch → 렌더.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CRON_STATUS_PATH = "admin/cron-status.json"

# Module-level 누적 카운터 (per-instance, dashboard 표시용)
_endpoint_counters: dict[str, int] = {}


def record_endpoint_hit(name: str) -> None:
    """vibe HTTP endpoint 호출 횟수 누적."""
    _endpoint_counters[name] = _endpoint_counters.get(name, 0) + 1


def get_endpoint_counters() -> dict[str, int]:
    return dict(_endpoint_counters)


async def record_cron_run(account_name: str, cron_name: str,
                           result: dict[str, Any]) -> None:
    """cron 한 번 실행 결과를 Blob 의 cron-status.json 에 upsert. 실패 swallow."""
    from . import blob_state

    try:
        current = await blob_state.load_json(account_name, CRON_STATUS_PATH,
                                              default={"crons": {}})
    except Exception:
        logger.warning("vibe.admin: cron status load failed", exc_info=True)
        current = {"crons": {}}

    if not isinstance(current, dict) or not isinstance(current.get("crons"), dict):
        current = {"crons": {}}

    current["crons"][cron_name] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result": result,
    }
    current["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        await blob_state.save_json(account_name, CRON_STATUS_PATH, current)
    except Exception:
        logger.warning("vibe.admin: cron status save failed", exc_info=True)


async def build_admin_stats(account_name: str) -> dict[str, Any]:
    """dashboard 가 fetch 하는 단일 페이로드."""
    from . import api_cache, blob_state

    cron_status = await blob_state.load_json(
        account_name, CRON_STATUS_PATH, default={"crons": {}}
    )

    # 최신 산출물 timestamps
    signals = await blob_state.load_json(
        account_name, "signals/latest.json", default=None)
    market = await blob_state.load_json(
        account_name, "market/latest.json", default=None)
    news = await blob_state.load_json(
        account_name, "news/summary-latest.json", default=None)
    summary = await blob_state.load_json(
        account_name, "market-summary/latest.json", default=None)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cache": api_cache.get_cache_stats(),
        "endpoints": get_endpoint_counters(),
        "crons": (cron_status or {}).get("crons", {}),
        "artifacts": {
            "signals_ts": (signals or {}).get("as_of") if signals else None,
            "market_ts": (market or {}).get("ts") if market else None,
            "news_ts": (news or {}).get("ts") if news else None,
            "market_summary_ts": (summary or {}).get("ts") if summary else None,
            "market_summary_kind": (summary or {}).get("kind") if summary else None,
            "signals_size": len(((signals or {}).get("ards") or {}).get("complex") or []) if signals else 0,
            "news_items": len((news or {}).get("items") or []) if news else 0,
        },
    }
