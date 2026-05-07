"""Prediction-market dashboard metrics.

Aggregates 9 metrics for the admin dashboard:
  1. participants_total          — distinct users with ≥1 prediction submission
  2. participation_points_total  — Σ matchup_participation credits
  3. user_points_total_lifetime  — Σ profiles[i].points_cumulative
  4. today_granted_points        — Σ today's positive point events (KST)
  5. today_burned_points         — Σ today's negative (deduct + penalty)
  6. burned_points_total         — all-time burned
  7. granted_points_total        — all-time granted
  8. user_points_balance_total   — Σ profiles[i].points_balance now
  9. holders ranking (top 1-99 + full CSV download)

Data sources:
  - Usage NDJSON (`logs/<KST_date>/...`): point_ledger writes events with
    tier="points_<event>_<reason>", llm_in=<signed amount>, llm_out=<balance>
  - User profile blobs (`users/<prefix>/<anon>.json`): points_balance,
    points_cumulative, display_name, tier

The aggregation scans all profile blobs and ~90 days of NDJSON logs. Cached
5 min in-process so repeated dashboard refreshes don't re-scan.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300  # 5 min
LOOKBACK_HOURS = 24 * 90  # 90 days for "all-time" approximation


@dataclass
class HolderRow:
    rank: int
    anon_short: str       # 8-char anon prefix (matches NDJSON convention)
    display_name: str
    balance: int          # points_balance
    cumulative: int       # points_cumulative
    tier: str
    tier_stage: int


@dataclass
class PMStats:
    participants_total: int = 0
    participation_points_total: int = 0
    user_points_total_lifetime: int = 0
    today_granted_points: int = 0
    today_burned_points: int = 0
    burned_points_total: int = 0
    granted_points_total: int = 0
    user_points_balance_total: int = 0
    user_count: int = 0
    as_of_kst: str = ""
    error: str = ""


_cache_stats: tuple[float, PMStats] | None = None
_cache_holders: tuple[float, list[HolderRow]] | None = None


def _kst_today_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()


def _kst_date_of(ts: str) -> str:
    """Convert an ISO UTC timestamp to its KST yyyy-mm-dd date string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=9)
        return dt.date().isoformat()
    except (ValueError, AttributeError):
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Profile scan
# ─────────────────────────────────────────────────────────────────────────────
async def _scan_profiles(svc) -> list[HolderRow]:
    """Read every user blob, return rows sorted by balance desc."""
    rows: list[HolderRow] = []
    container = svc.get_container_client("users")
    try:
        async for blob in container.list_blobs():
            if not blob.name.endswith(".json"):
                continue
            try:
                bc = container.get_blob_client(blob.name)
                body = await (await bc.download_blob()).readall()
                d = json.loads(body)
                anon = (d.get("anon_user_id") or "")[:8]
                rows.append(HolderRow(
                    rank=0,
                    anon_short=anon,
                    display_name=d.get("display_name", "") or f"User_{anon[:4]}",
                    balance=int(d.get("points_balance", 0) or 0),
                    cumulative=int(d.get("points_cumulative", 0) or 0),
                    tier=d.get("tier", "bronze") or "bronze",
                    tier_stage=int(d.get("tier_stage", 0) or 0),
                ))
            except Exception:
                logger.debug("profile parse failed: %s", blob.name, exc_info=True)
                continue
    except Exception:
        logger.exception("users container scan failed")
    rows.sort(key=lambda r: r.balance, reverse=True)
    for i, r in enumerate(rows):
        r.rank = i + 1
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Main compute
# ─────────────────────────────────────────────────────────────────────────────
async def compute_stats(storage_account_name: str, *, force: bool = False) -> PMStats:
    global _cache_stats
    now_mono = time.monotonic()
    if not force and _cache_stats is not None and (now_mono - _cache_stats[0]) < CACHE_TTL_SECONDS:
        return _cache_stats[1]

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    from .dashboard_aggregator import _read_logs_in_window

    today_kst = _kst_today_iso()
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            # Profile scan — balance + cumulative aggregates
            holders = await _scan_profiles(svc)
            user_count = len(holders)
            balance_total = sum(h.balance for h in holders)
            lifetime_total = sum(h.cumulative for h in holders)

            # NDJSON scan — point events
            events = await _read_logs_in_window(svc, LOOKBACK_HOURS)
    finally:
        await creds.close()

    granted_total = 0
    burned_total = 0
    today_granted = 0
    today_burned = 0
    matchup_anons: set[str] = set()
    participation_total = 0

    for e in events:
        tier = str(e.get("tier", ""))
        if not tier.startswith("points_"):
            continue
        amt = e.get("llm_in", 0)
        try:
            amt = int(amt)
        except (TypeError, ValueError):
            continue
        ts = e.get("ts", "")
        is_today = _kst_date_of(ts) == today_kst

        if amt > 0:
            granted_total += amt
            if is_today:
                today_granted += amt
        elif amt < 0:
            burned_total += -amt
            if is_today:
                today_burned += -amt

        # Matchup-scoped breakdown
        if "matchup" in tier:
            anon = str(e.get("anon", ""))
            if anon:
                matchup_anons.add(anon)
            if "participation" in tier and amt > 0:
                participation_total += amt

    snap = PMStats(
        participants_total=len(matchup_anons),
        participation_points_total=participation_total,
        user_points_total_lifetime=lifetime_total,
        today_granted_points=today_granted,
        today_burned_points=today_burned,
        burned_points_total=burned_total,
        granted_points_total=granted_total,
        user_points_balance_total=balance_total,
        user_count=user_count,
        as_of_kst=(datetime.now(timezone.utc) + timedelta(hours=9)).isoformat(timespec="seconds"),
    )
    _cache_stats = (now_mono, snap)

    # Also warm the holders cache since we already paid for the scan
    global _cache_holders
    _cache_holders = (now_mono, holders)
    return snap


async def get_holders(storage_account_name: str, *, force: bool = False) -> list[HolderRow]:
    """Return sorted holder rows. Reuses cache populated by compute_stats."""
    global _cache_holders
    now_mono = time.monotonic()
    if not force and _cache_holders is not None and (now_mono - _cache_holders[0]) < CACHE_TTL_SECONDS:
        return _cache_holders[1]

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            rows = await _scan_profiles(svc)
    finally:
        await creds.close()
    _cache_holders = (now_mono, rows)
    return rows


def holders_to_csv(rows: list[HolderRow]) -> bytes:
    """Full ranking as CSV bytes (admin download)."""
    lines = ["rank,anon_short,display_name,balance,cumulative,tier,tier_stage"]
    for r in rows:
        # CSV-safe display_name (strip commas/newlines)
        name = str(r.display_name).replace(",", " ").replace("\n", " ")
        lines.append(f"{r.rank},{r.anon_short},{name},{r.balance},{r.cumulative},{r.tier},{r.tier_stage}")
    return "\n".join(lines).encode("utf-8")
