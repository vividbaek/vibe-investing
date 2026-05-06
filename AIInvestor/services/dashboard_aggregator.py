"""§17.3 dashboard aggregator — reads logs/* NDJSON, writes aggregated JSON.

Runs from a Timer Trigger every 15 minutes. Output:
  dashboard/24h.json   — last 24h totals
  dashboard/7d.json    — last 7d totals

Each JSON has:
  {
    "generated_at": "...",
    "window": "24h",
    "total": 412,
    "tier_counts": {"commentary_hit": 280, "snapshot_hit": 70, "live": 50, ...},
    "tier_pct":    {"commentary_hit": 68.0, ...},
    "p50_by_tier": {"commentary_hit": 1100, ...},
    "top_tickers": [["NVDA", 88], ["AAPL", 64], ...],
    "language_dist": {"ko": 71, "en": 18, ...},
    "persona_dist":  {"buffett": 47, "wood": 32, "dalio": 21},
    "llm_total_in": 12000, "llm_total_out": 8400
  }
"""

from __future__ import annotations

import json
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

logger = logging.getLogger(__name__)

LOGS_CONTAINER = "logs"
DASHBOARD_CONTAINER = "dashboard"


def _percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return int(s[f])
    return int(s[f] + (s[c] - s[f]) * (k - f))


async def _read_logs_in_window(
    svc: BlobServiceClient, hours: int,
) -> list[dict]:
    """Read all logs/yyyy/mm/dd/HH.ndjson blobs covering the last `hours` hours."""
    container = svc.get_container_client(LOGS_CONTAINER)
    now = datetime.now(timezone.utc)
    earliest = now - timedelta(hours=hours)
    events: list[dict] = []

    async for blob in container.list_blobs(name_starts_with=""):
        # Cheap path filter — parse "logs/yyyy/mm/dd/HH.ndjson" → datetime
        try:
            parts = blob.name.split("/")
            blob_dt = datetime(
                int(parts[0]), int(parts[1]), int(parts[2]),
                int(parts[3].split(".")[0]),
                tzinfo=timezone.utc,
            )
            if blob_dt < earliest - timedelta(hours=1):
                continue
        except (ValueError, IndexError):
            continue

        try:
            client = container.get_blob_client(blob.name)
            stream = await client.download_blob()
            body = await stream.readall()
            for line in body.decode("utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    ts = datetime.fromisoformat(evt["ts"].replace("Z", "+00:00"))
                    if ts >= earliest:
                        events.append(evt)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        except Exception:
            logger.exception("failed reading log blob %s", blob.name)

    return events


def _aggregate(events: list[dict], window_label: str) -> dict[str, Any]:
    if not events:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "window": window_label,
            "total": 0,
            "tier_counts": {},
            "tier_pct": {},
            "p50_by_tier": {},
            "top_tickers": [],
            "language_dist": {},
            "persona_dist": {},
            "llm_total_in": 0,
            "llm_total_out": 0,
        }

    tier_counts: dict[str, int] = {}
    tier_durations: dict[str, list[int]] = {}
    ticker_counts: dict[str, int] = {}
    lang_counts: dict[str, int] = {}
    persona_counts: dict[str, int] = {}
    llm_in_total = 0
    llm_out_total = 0

    for e in events:
        tier = e.get("tier", "unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        d = e.get("duration_ms")
        if isinstance(d, (int, float)):
            tier_durations.setdefault(tier, []).append(int(d))
        tk = e.get("ticker")
        if tk:
            ticker_counts[tk] = ticker_counts.get(tk, 0) + 1
        lng = e.get("lang")
        if lng:
            lang_counts[lng] = lang_counts.get(lng, 0) + 1
        prs = e.get("persona")
        if prs:
            persona_counts[prs] = persona_counts.get(prs, 0) + 1
        llm_in_total += int(e.get("llm_in", 0) or 0)
        llm_out_total += int(e.get("llm_out", 0) or 0)

    total = len(events)
    tier_pct = {k: round(v / total * 100, 1) for k, v in tier_counts.items()} if total else {}
    p50_by_tier = {k: _percentile(v, 0.5) for k, v in tier_durations.items()}
    top_tickers = sorted(ticker_counts.items(), key=lambda x: -x[1])[:20]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": window_label,
        "total": total,
        "tier_counts": tier_counts,
        "tier_pct": tier_pct,
        "p50_by_tier": p50_by_tier,
        "top_tickers": top_tickers,
        "language_dist": lang_counts,
        "persona_dist": persona_counts,
        "llm_total_in": llm_in_total,
        "llm_total_out": llm_out_total,
    }


async def run_aggregation(storage_account_name: str, credential=None) -> None:
    """Read logs, write dashboard/24h.json + dashboard/7d.json."""
    creds = credential or DefaultAzureCredential()
    async with BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=creds,
    ) as svc:
        # 24h aggregation
        events_24h = await _read_logs_in_window(svc, 24)
        agg_24h = _aggregate(events_24h, "24h")
        # 7d aggregation
        events_7d = await _read_logs_in_window(svc, 24 * 7)
        agg_7d = _aggregate(events_7d, "7d")

        from azure.storage.blob import ContentSettings
        # 30분 browser cache + public CDN cache. Aggregator runs every 15min,
        # so 30min is safe (clients see at most 30min stale data).
        content_settings = ContentSettings(
            content_type="application/json",
            cache_control="public, max-age=1800",
        )
        for name, agg in (("24h.json", agg_24h), ("7d.json", agg_7d)):
            blob = svc.get_blob_client(DASHBOARD_CONTAINER, name)
            payload = json.dumps(agg, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                await blob.upload_blob(
                    payload, overwrite=True, content_settings=content_settings,
                )
            except Exception:
                logger.exception("dashboard upload failed for %s", name)

        logger.info("dashboard aggregation done — 24h=%d events, 7d=%d events",
                    len(events_24h), len(events_7d))


async def fetch_dashboard_json(
    storage_account_name: str, window: str, credential=None,
) -> dict | None:
    """Read the pre-aggregated dashboard/<window>.json from Blob."""
    creds = credential or DefaultAzureCredential()
    async with BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=creds,
    ) as svc:
        blob = svc.get_blob_client(DASHBOARD_CONTAINER, f"{window}.json")
        try:
            stream = await blob.download_blob()
            body = await stream.readall()
            return json.loads(body)
        except ResourceNotFoundError:
            return None
        except Exception:
            logger.exception("dashboard fetch failed window=%s", window)
            return None
