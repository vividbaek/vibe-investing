"""§Vibe P4 — search + track helpers.

search:
  - signals/latest.json (P2 cron 산출) 에서 해당 ticker 의 ARDS+AMQS 신호 추출
  - 검색 로그는 append-blob NDJSON (users-style)

track:
  - 익명 user_hash = SHA-256(IP + UA + date + salt)
  - append-blob NDJSON 에 date,user_hash 적재
  - DAU/total_au 는 module-level dict (per-instance, eventual consistency)
  - 정확한 글로벌 집계는 다음 P6 timer 에서 NDJSON 을 일1회 reduce
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Module-level DAU/AU 캐시 (per Function instance — eventual consistency)
_dau_today: dict[str, set[str]] = {}    # {YYYY-MM-DD: {user_hash, ...}}
_all_users: set[str] = set()             # 누적 (instance 시작 후 본 hash)

TICKER_RX = re.compile(r"^[A-Z0-9.^-]+$")


def _user_hash(ip: str, ua: str, date_str: str, salt: str) -> str:
    return hashlib.sha256(
        f"{ip}|{ua}|{date_str}|{salt}".encode("utf-8")
    ).hexdigest()


def _user_hash_undated(ip: str, ua: str, salt: str) -> str:
    return hashlib.sha256(f"{ip}|{ua}|{salt}".encode("utf-8")).hexdigest()


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ──────────────────────────────────────────────────────────────────────────────
# search
# ──────────────────────────────────────────────────────────────────────────────
def normalize_ticker(q: str) -> str | None:
    """검색 입력 → 정규화된 ticker. 잘못된 형식이면 None."""
    if not q:
        return None
    t = q.strip().upper()
    if not t or len(t) > 12 or not TICKER_RX.match(t):
        return None
    return t


def extract_signals_for_ticker(signals_payload: dict[str, Any] | None,
                                ticker: str) -> list[dict[str, Any]]:
    """combined signals/latest.json 에서 해당 ticker 의 ARDS/AMQS 행 추출."""
    if not signals_payload:
        return []
    out: list[dict[str, Any]] = []
    ards = signals_payload.get("ards") or {}
    # ARDS-X 는 complex/indices/groups 에 ticker 가 흩어져 있음
    for key in ("indices", "complex"):
        for row in ards.get(key, []):
            if isinstance(row, dict) and row.get("ticker") == ticker:
                out.append({
                    "strategy": "ARDS",
                    "ticker": ticker,
                    "decline_score": row.get("decline_score"),
                    "oversold_score": row.get("oversold_score"),
                    "rsi14": row.get("rsi14"),
                    "dd_from_high": row.get("dd_from_high"),
                })
                break
    amqs = signals_payload.get("amqs") or {}
    for row in amqs.get("metrics", []):
        if isinstance(row, dict) and row.get("ticker") == ticker:
            out.append({
                "strategy": "AMQS",
                "ticker": ticker,
                "signal": row.get("signal"),
                "total_100": row.get("total_100"),
                "weight": row.get("weight"),
                "reason": row.get("reason"),
            })
            break
    return out


async def append_search_log(account_name: str, ticker: str,
                             ip: str, ua: str, salt: str) -> None:
    """검색 한 건을 NDJSON append blob 에 적재. 실패는 swallow."""
    today = _today_utc()
    uh = _user_hash(ip, ua, today, salt)
    line = (f'{{"ts":"{_now_iso()}","date":"{today}",'
            f'"ticker":"{ticker}","user_hash":"{uh}"}}\n')
    try:
        await _append_ndjson(account_name, f"searches/{today}.ndjson",
                              line.encode("utf-8"))
    except Exception:
        logger.warning("vibe.search: append log failed", exc_info=True)


# ──────────────────────────────────────────────────────────────────────────────
# track (DAU/AU)
# ──────────────────────────────────────────────────────────────────────────────
def _instance_track(ip: str, ua: str, salt: str) -> tuple[int, int]:
    """per-instance: 오늘 DAU set + 누적 set 갱신, 현재 카운트 반환."""
    today = _today_utc()
    day_h = _user_hash(ip, ua, today, salt)
    all_h = _user_hash_undated(ip, ua, salt)
    _dau_today.setdefault(today, set()).add(day_h)
    _all_users.add(all_h)
    return len(_dau_today[today]), len(_all_users)


async def record_visit(account_name: str, ip: str, ua: str,
                        salt: str) -> dict[str, int]:
    """방문 1건 적재 + DAU/total_au 반환 (per-instance estimate)."""
    today = _today_utc()
    day_h = _user_hash(ip, ua, today, salt)
    all_h = _user_hash_undated(ip, ua, salt)
    dau, total = _instance_track(ip, ua, salt)
    line = (f'{{"ts":"{_now_iso()}","date":"{today}",'
            f'"day_hash":"{day_h}","all_hash":"{all_h}"}}\n')
    try:
        await _append_ndjson(account_name, f"users/{today}.ndjson",
                              line.encode("utf-8"))
    except Exception:
        logger.warning("vibe.track: append failed", exc_info=True)
    return {"dau": dau, "total_au": total}


# ──────────────────────────────────────────────────────────────────────────────
# Append-blob NDJSON helper
# ──────────────────────────────────────────────────────────────────────────────
async def _append_ndjson(account_name: str, path: str, payload: bytes) -> None:
    from azure.core.exceptions import ResourceExistsError
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient

    from . import blob_state

    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(blob_state.CONTAINER)
            try:
                await container.create_container()
            except Exception:
                pass
            bc = container.get_blob_client(path)
            try:
                await bc.create_append_blob()
            except ResourceExistsError:
                pass
            await bc.append_block(payload)
    finally:
        if hasattr(creds, "close"):
            await creds.close()
