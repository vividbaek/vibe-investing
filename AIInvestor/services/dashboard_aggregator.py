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


# ────────────────────────────────────────────────────────────
# §7 Persona sub-dashboard — per-persona breakdown of Korean
# favorites + all tickers, language distribution, traffic share.
# ────────────────────────────────────────────────────────────

VALID_PERSONAS = ("buffett", "dalio", "wood")


def _deepseek_cost_usd(tokens_in: int, tokens_out: int) -> float:
    """Estimate DeepSeek API cost from token counts. Defaults match
    deepseek-chat 2026 published pricing; override via env vars
    DEEPSEEK_PRICE_IN_PER_M / DEEPSEEK_PRICE_OUT_PER_M (USD per 1M tokens).
    """
    import os
    try:
        in_per_m  = float(os.getenv("DEEPSEEK_PRICE_IN_PER_M",  "0.27"))
        out_per_m = float(os.getenv("DEEPSEEK_PRICE_OUT_PER_M", "1.10"))
    except ValueError:
        in_per_m, out_per_m = 0.27, 1.10
    return round((tokens_in / 1_000_000) * in_per_m + (tokens_out / 1_000_000) * out_per_m, 4)


def _build_persona_breakdown(
    events: list[dict],
    persona_filter: str | None,
) -> dict[str, Any]:
    """For each persona, aggregate ticker counts, language dist, total."""
    from .hot_ticker_resolver import load_korean_favorites
    favs = load_korean_favorites()

    per: dict[str, dict] = {p: {
        "total": 0,
        "language_dist": {},
        "ticker_counts": {},
        "llm_in": 0, "llm_out": 0,
    } for p in VALID_PERSONAS}

    for e in events:
        prs = (e.get("persona") or "").lower()
        if prs not in per:
            continue
        if persona_filter and prs != persona_filter:
            continue
        bucket = per[prs]
        bucket["total"] += 1
        lng = e.get("lang") or "?"
        bucket["language_dist"][lng] = bucket["language_dist"].get(lng, 0) + 1
        tk = (e.get("ticker") or "").upper()
        if tk:
            bucket["ticker_counts"][tk] = bucket["ticker_counts"].get(tk, 0) + 1
        bucket["llm_in"] += int(e.get("llm_in", 0) or 0)
        bucket["llm_out"] += int(e.get("llm_out", 0) or 0)

    # Build per-persona output: top KR favorites (with name) + top all tickers
    out_personas: dict[str, dict] = {}
    for prs, b in per.items():
        if persona_filter and prs != persona_filter:
            continue
        ranked = sorted(b["ticker_counts"].items(), key=lambda x: -x[1])
        kr_top = []
        for tk, count in ranked:
            if tk in favs:
                fav = favs[tk]
                kr_top.append({
                    "ticker": tk,
                    "name_kr": fav.name_kr,
                    "rank": fav.preference_rank,
                    "count": count,
                })
            if len(kr_top) >= 14:
                break
        out_personas[prs] = {
            "total": b["total"],
            "language_dist": b["language_dist"],
            "korean_favorites_top": kr_top,
            "all_top_tickers": ranked[:20],
            "llm_in": b["llm_in"],
            "llm_out": b["llm_out"],
        }

    # KR favorites coverage matrix — for each favorite, how many queries per persona
    coverage = []
    for tk, fav in sorted(favs.items(), key=lambda x: x[1].preference_rank):
        row = {
            "ticker": tk,
            "name_kr": fav.name_kr,
            "name_en": fav.name_en,
            "rank": fav.preference_rank,
            "reason_kr": fav.reason_kr,
        }
        total = 0
        for prs in VALID_PERSONAS:
            c = per[prs]["ticker_counts"].get(tk, 0)
            row[prs] = c
            total += c
        row["total"] = total
        coverage.append(row)

    return {
        "personas": out_personas,
        "korean_favorites_coverage": coverage,
    }


async def fetch_persona_breakdown(
    storage_account_name: str,
    window: str,
    persona: str | None = None,
    credential=None,
) -> dict[str, Any]:
    """Read logs in window, build per-persona breakdown. Heavier than
    fetch_dashboard_json — meant for the operator-only persona dashboard."""
    hours = 24 if window == "24h" else 168
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            events = await _read_logs_in_window(svc, hours)
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()

    breakdown = _build_persona_breakdown(events, persona)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": window,
        "persona_filter": persona,
        "total_events": len(events),
        **breakdown,
    }


# ════════════════════════════════════════════════════════════
# §V2 Observability dashboard — proves the caching hypothesis
#
# Hypothesis (대 명제):
#   Similar-interest cohorts ask similar questions at similar times,
#   so caching at peak query timing saves LLM calls + energy.
#
# We surface 4 cache categories:
#   llm_call   — full LLM call (tier ∈ live, deep)
#   llm_cache  — LLM-result cache hit, no LLM call (tier=commentary_hit)
#   obj_cache  — object-storage hit, LLM may run (tier=snapshot_hit)
#   cdn_edge   — CDN/SWA edge hit (estimated; not in NDJSON yet — placeholder)
#
# And 3 statistical proofs:
#   ticker concentration (Top10 share, HHI) — proves "similar questions"
#   hourly routine (Gini of hourly distribution) — proves "similar times"
#   cohort overlap (Jaccard of top-N tickers across cohorts) — proves "similar interest"
# ════════════════════════════════════════════════════════════


def _classify_cache_category(tier: str) -> str:
    """Map raw tier values to one of the 4 cache buckets.

    Cache hierarchy (fastest → slowest):
      function_cache  — Function App in-process 5-min memory cache hit
                        (no yfinance, but LLM still ran)
      llm_cache       — pre-warmed LLM commentary blob (no yfinance, no LLM)
      obj_cache       — pre-warmed snapshot blob (no yfinance, LLM ran)
      llm_call        — full live path (yfinance + LLM)

    Note: 'commentary_hit' saves the LLM call; 'snapshot_hit' and
    'function_cache' both save yfinance only — LLM still runs in those tiers.
    """
    if tier == "commentary_hit":
        return "llm_cache"
    if tier == "snapshot_hit":
        return "obj_cache"
    if tier == "function_cache":
        return "function_cache"
    if tier in ("live", "deep", "dual", "ai_search_live"):
        return "llm_call"
    return "other"


def _date_key_kst(ts_iso: str) -> str:
    """Convert UTC ISO timestamp → 'YYYY-MM-DD' in KST (UTC+9)."""
    try:
        dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    kst = dt + timedelta(hours=9)
    return f"{kst.year:04d}-{kst.month:02d}-{kst.day:02d}"


def _hour_kst(ts_iso: str) -> int:
    """Return KST hour (0-23) for an event timestamp."""
    try:
        dt = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return -1
    kst = dt + timedelta(hours=9)
    return kst.hour


def _hhi(counts: dict[str, int]) -> float:
    """Herfindahl-Hirschman Index in 0–1 range (sum of squared shares)."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return round(sum((c / total) ** 2 for c in counts.values()), 4)


def _gini(values: list[float]) -> float:
    """Gini coefficient of a distribution (0 = perfectly uniform, 1 = all in one)."""
    if not values:
        return 0.0
    sv = sorted(values)
    n = len(sv)
    cum = sum((i + 1) * v for i, v in enumerate(sv))
    s = sum(sv)
    if s == 0:
        return 0.0
    return round((2 * cum) / (n * s) - (n + 1) / n, 4)


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return round(len(a & b) / max(len(a | b), 1), 4)


def _classify_cohort(
    first_seen: dict[str, datetime],
    last_seen: dict[str, datetime],
    event_counts: dict[str, int],
    now: datetime,
) -> dict[str, str]:
    """For each anon_id, classify into 'new' / 'active' / 'dormant'.
      new     — first seen within last 7 days
      active  — ≥3 events in last 14 days AND not new
      dormant — last seen ≥14 days ago
      casual  — anything else (active but low-frequency)
    """
    cohort: dict[str, str] = {}
    for anon, fs in first_seen.items():
        ls = last_seen.get(anon, fs)
        n_events = event_counts.get(anon, 0)
        days_since_first = (now - fs).days
        days_since_last = (now - ls).days
        if days_since_first <= 7:
            cohort[anon] = "new"
        elif days_since_last >= 14:
            cohort[anon] = "dormant"
        elif n_events >= 3:
            cohort[anon] = "active"
        else:
            cohort[anon] = "casual"
    return cohort


def _aggregate_v2(events: list[dict], days: int = 30) -> dict[str, Any]:
    """The big aggregation. Returns the full payload the v2 dashboard renders."""
    now = datetime.now(timezone.utc)

    # 4-way category counters (function_cache replaces the old cdn_edge slot)
    _empty_cats = lambda: {"function_cache": 0, "llm_cache": 0, "obj_cache": 0, "llm_call": 0, "other": 0}
    cat_today: dict[str, int] = _empty_cats()
    cat_total: dict[str, int] = _empty_cats()

    # DeepSeek token counters — total / today / yesterday for the dashboard's
    # cost section. We also accumulate per-day to drive a daily token chart.
    tokens_today_in = 0
    tokens_today_out = 0
    tokens_yest_in = 0
    tokens_yest_out = 0
    tokens_total_in = 0
    tokens_total_out = 0

    # daily_series[date_key] → {function_cache, llm_call, llm_cache, obj_cache, other, users(set), p50_pool}
    daily: dict[str, dict[str, Any]] = {}

    # hourly_routine[hour] → {function_cache, llm_call, llm_cache, obj_cache, other}
    hourly: dict[int, dict[str, int]] = {h: _empty_cats() for h in range(24)}

    # cohort tracking
    first_seen: dict[str, datetime] = {}
    last_seen: dict[str, datetime] = {}
    user_event_count: dict[str, int] = {}
    user_tickers: dict[str, list[str]] = {}

    # ticker concentration — across all events
    ticker_total: dict[str, int] = {}

    # persona × ticker for grand summary
    persona_ticker: dict[str, dict[str, int]] = {p: {} for p in VALID_PERSONAS}

    today_key = (now + timedelta(hours=9)).strftime("%Y-%m-%d")
    yest_key  = ((now + timedelta(hours=9)).date() - timedelta(days=1)).isoformat()

    for e in events:
        ts = e.get("ts", "")
        date_key = _date_key_kst(ts)
        if not date_key:
            continue
        cat = _classify_cache_category(e.get("tier", ""))
        cat_total[cat] = cat_total.get(cat, 0) + 1
        if date_key == today_key:
            cat_today[cat] = cat_today.get(cat, 0) + 1

        # DeepSeek token counters
        ein = int(e.get("llm_in", 0) or 0)
        eout = int(e.get("llm_out", 0) or 0)
        tokens_total_in += ein
        tokens_total_out += eout
        if date_key == today_key:
            tokens_today_in += ein
            tokens_today_out += eout
        elif date_key == yest_key:
            tokens_yest_in += ein
            tokens_yest_out += eout

        # daily series
        d = daily.setdefault(date_key, {
            "function_cache": 0, "llm_cache": 0, "obj_cache": 0, "llm_call": 0, "other": 0,
            "users": set(), "durations": [], "llm_in": 0, "llm_out": 0,
        })
        d[cat] = d.get(cat, 0) + 1
        d["llm_in"] += ein
        d["llm_out"] += eout
        anon = e.get("anon")
        if anon:
            d["users"].add(anon)
        dur = e.get("duration_ms")
        if isinstance(dur, (int, float)):
            d["durations"].append(int(dur))

        # hourly routine
        hr = _hour_kst(ts)
        if 0 <= hr < 24:
            hourly[hr][cat] = hourly[hr].get(cat, 0) + 1

        # cohort + ticker per user
        if anon:
            try:
                event_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if anon not in first_seen or event_dt < first_seen[anon]:
                first_seen[anon] = event_dt
            if anon not in last_seen or event_dt > last_seen[anon]:
                last_seen[anon] = event_dt
            user_event_count[anon] = user_event_count.get(anon, 0) + 1
            tk = (e.get("ticker") or "").upper()
            if tk:
                user_tickers.setdefault(anon, []).append(tk)
                ticker_total[tk] = ticker_total.get(tk, 0) + 1

        # persona × ticker
        prs = (e.get("persona") or "").lower()
        tk = (e.get("ticker") or "").upper()
        if prs in persona_ticker and tk:
            persona_ticker[prs][tk] = persona_ticker[prs].get(tk, 0) + 1

    # daily series → list, last `days` days, KST descending
    daily_list = []
    for date_key, d in sorted(daily.items(), reverse=True)[:days]:
        durations = d.pop("durations", [])
        users = d.pop("users", set())
        d["users"] = len(users)
        d["p50_ms"] = _percentile(durations, 0.5) if durations else 0
        d["total"] = d["function_cache"] + d["llm_call"] + d["llm_cache"] + d["obj_cache"]
        cache_hits = d["function_cache"] + d["llm_cache"] + d["obj_cache"]
        d["cache_hit_pct"] = round(cache_hits / d["total"] * 100, 1) if d["total"] else 0.0
        d["date"] = date_key
        daily_list.append(d)

    # hourly_routine — array form (sorted by hour)
    hourly_list = []
    for h in range(24):
        b = hourly[h]
        b["hour"] = h
        b["total"] = b["function_cache"] + b["llm_call"] + b["llm_cache"] + b["obj_cache"]
        hourly_list.append(b)

    # concentration metrics
    total_events_with_ticker = sum(ticker_total.values())
    top_n = sorted(ticker_total.items(), key=lambda x: -x[1])[:10]
    top10_share = (
        round(sum(c for _, c in top_n) / total_events_with_ticker * 100, 1)
        if total_events_with_ticker else 0.0
    )
    hhi = _hhi(ticker_total)
    hourly_volumes = [b["total"] for b in hourly_list]
    gini_temporal = _gini(hourly_volumes)

    # cohorts
    cohort = _classify_cohort(first_seen, last_seen, user_event_count, now)
    cohort_groups = {"new": [], "active": [], "dormant": [], "casual": []}
    for anon, group in cohort.items():
        cohort_groups[group].append(anon)
    cohort_summary = {}
    for group, anons in cohort_groups.items():
        # build the group's ticker preference vector
        group_tickers: dict[str, int] = {}
        for a in anons:
            for tk in user_tickers.get(a, []):
                group_tickers[tk] = group_tickers.get(tk, 0) + 1
        cohort_summary[group] = {
            "users": len(anons),
            "events": sum(user_event_count.get(a, 0) for a in anons),
            "top_tickers": sorted(group_tickers.items(), key=lambda x: -x[1])[:10],
        }

    # cohort overlap (Jaccard of top-10 ticker sets across cohorts)
    cohort_top_sets = {
        g: {tk for tk, _ in c["top_tickers"]}
        for g, c in cohort_summary.items()
    }
    overlap = {
        "new_vs_active":     _jaccard(cohort_top_sets["new"],     cohort_top_sets["active"]),
        "active_vs_dormant": _jaccard(cohort_top_sets["active"],  cohort_top_sets["dormant"]),
        "new_vs_dormant":    _jaccard(cohort_top_sets["new"],     cohort_top_sets["dormant"]),
    }

    # statistical interpretation hint (auto-generated bullets)
    interpretation = []
    if total_events_with_ticker >= 20:
        interpretation.append({
            "kind": "concentration",
            "msg": (
                f"Top 10 ticker가 전체 쿼리의 {top10_share}%를 차지합니다. "
                f"이론상 LLM 호출의 최대 {top10_share}%를 캐시로 절감 가능."
            ),
            "good": top10_share >= 50,
        })
    if sum(hourly_volumes) >= 20:
        peak_hour = max(range(24), key=lambda h: hourly_list[h]["total"])
        interpretation.append({
            "kind": "temporal",
            "msg": (
                f"시간대별 분포 Gini={gini_temporal} — "
                f"피크 시간 KST {peak_hour:02d}시. "
                f"피크 직전에 사전 캐싱하면 첫 사용자 응답시간을 절감 가능."
            ),
            "good": gini_temporal >= 0.3,
        })
    if total_events_with_ticker:
        cache_hits = (
            cat_total["function_cache"] + cat_total["llm_cache"] + cat_total["obj_cache"]
        )
        all_paths = cache_hits + cat_total["llm_call"]
        cache_hit_pct = round(cache_hits / max(all_paths, 1) * 100, 1)
        # LLM 호출 절감 = LLM 캐시 히트 (commentary_hit). function_cache + obj_cache
        # 는 yfinance 만 절약하고 LLM 은 호출됨.
        llm_calls_saved = cat_total["llm_cache"]
        interpretation.append({
            "kind": "cache_efficiency",
            "msg": (
                f"실측 캐시 적중률 {cache_hit_pct}% (Function/LLM/Object 캐시 / 전체). "
                f"LLM 호출 절감 {llm_calls_saved:,}건 — DeepSeek API 미사용."
            ),
            "good": cache_hit_pct >= 50,
        })
    if cohort_summary["new"]["users"] and cohort_summary["active"]["users"]:
        interpretation.append({
            "kind": "cohort_overlap",
            "msg": (
                f"신규 vs 활성 cohort top-10 ticker Jaccard 유사도 = {overlap['new_vs_active']}. "
                f"높을수록 '비슷한 관심사' 가설 지지."
            ),
            "good": overlap["new_vs_active"] >= 0.4,
        })

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "window_days": days,
        "totals": {
            "today": cat_today,
            "cumulative": cat_total,
            "today_total": sum(cat_today.values()),
            "cumulative_total": sum(cat_total.values()),
            # LLM 호출 절감 = commentary_hit (LLM 결과 캐시 히트, DeepSeek 호출 안 됨)
            "llm_calls_saved_today": cat_today["llm_cache"],
            "llm_calls_saved_total": cat_total["llm_cache"],
        },
        "deepseek": {
            "tokens_today_in":  tokens_today_in,
            "tokens_today_out": tokens_today_out,
            "tokens_yest_in":   tokens_yest_in,
            "tokens_yest_out":  tokens_yest_out,
            "tokens_total_in":  tokens_total_in,
            "tokens_total_out": tokens_total_out,
            "cost_today_usd":  _deepseek_cost_usd(tokens_today_in, tokens_today_out),
            "cost_yest_usd":   _deepseek_cost_usd(tokens_yest_in,  tokens_yest_out),
            "cost_total_usd":  _deepseek_cost_usd(tokens_total_in, tokens_total_out),
            "price_in_per_m":  float(__import__("os").getenv("DEEPSEEK_PRICE_IN_PER_M",  "0.27")),
            "price_out_per_m": float(__import__("os").getenv("DEEPSEEK_PRICE_OUT_PER_M", "1.10")),
        },
        "daily_series": daily_list,
        "hourly_routine": hourly_list,
        "concentration": {
            "top10_share_pct": top10_share,
            "hhi": hhi,
            "gini_temporal": gini_temporal,
            "top_tickers": top_n,
        },
        "cohorts": cohort_summary,
        "cohort_overlap_jaccard": overlap,
        "persona_ticker": {
            p: sorted(tks.items(), key=lambda x: -x[1])[:10]
            for p, tks in persona_ticker.items()
        },
        "interpretation": interpretation,
    }


async def run_aggregation_v2(storage_account_name: str, days: int = 30, credential=None) -> None:
    """Heavier aggregation across last `days` days. Writes dashboard/v2.json."""
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            events = await _read_logs_in_window(svc, days * 24)
            agg = _aggregate_v2(events, days=days)

            from azure.storage.blob import ContentSettings
            content_settings = ContentSettings(
                content_type="application/json",
                cache_control="public, max-age=900",  # 15min
            )
            blob = svc.get_blob_client(DASHBOARD_CONTAINER, "v2.json")
            payload = json.dumps(agg, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                await blob.upload_blob(payload, overwrite=True, content_settings=content_settings)
            except Exception:
                logger.exception("v2 dashboard upload failed")
            logger.info("v2 aggregation done — %d events over %d days", len(events), days)
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()


async def fetch_dashboard_v2(storage_account_name: str, credential=None) -> dict | None:
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            blob = svc.get_blob_client(DASHBOARD_CONTAINER, "v2.json")
            try:
                stream = await blob.download_blob()
                body = await stream.readall()
                return json.loads(body)
            except ResourceNotFoundError:
                return None
            except Exception:
                logger.exception("v2 dashboard fetch failed")
                return None
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()


async def export_daily_csv(
    storage_account_name: str,
    date_kst: str,
    credential=None,
) -> bytes:
    """Read all events whose KST date matches `date_kst` (YYYY-MM-DD), return CSV bytes."""
    # Read ~36 hours window to safely cover one KST day in UTC log files
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            # Pull a 7-day window then filter — simpler than computing UTC ranges
            events = await _read_logs_in_window(svc, 24 * 7)
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()

    rows = ["timestamp_kst,anon_user_id_short,language,persona,ticker,tier,cache_category,duration_ms,llm_in,llm_out"]
    for e in events:
        ts = e.get("ts", "")
        if _date_key_kst(ts) != date_kst:
            continue
        try:
            kst_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=9)
            kst_str = kst_dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            kst_str = ts
        rows.append(",".join([
            kst_str,
            str(e.get("anon", ""))[:8],
            str(e.get("lang", "")),
            str(e.get("persona", "")),
            str(e.get("ticker", "")),
            str(e.get("tier", "")),
            _classify_cache_category(e.get("tier", "")),
            str(e.get("duration_ms", 0)),
            str(e.get("llm_in", 0)),
            str(e.get("llm_out", 0)),
        ]))
    return "\n".join(rows).encode("utf-8")
