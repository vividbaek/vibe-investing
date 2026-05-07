"""Saju service — orchestrates Saju engine + stock recommender + user state.

Handles:
  - Persisting birth date/hour to UserProfile
  - 5-day free counter
  - Daily KST reset of `saju_unlocked_today` ticker list
  - Picking the daily 5 stocks (deterministic per user × KST date)
  - Atomic point spend on unlock
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from .point_ledger import deduct_points
from .saju_engine import (
    DISCLAIMER_KO,
    SajuProfile,
    TodaySaju,
    build_profile,
    summary_lines_ko,
    today_for,
)
from .stock_recommender import (
    StockEntry,
    explain_pick,
    recommend_for_today,
)
from .user_profile import UserProfile

logger = logging.getLogger(__name__)

# Cost in points to unlock one extra Saju recommendation
UNLOCK_POINT_COST = 200
# Free trial window in days (first /saju/ use anchors the start)
FREE_TRIAL_DAYS = 5
# Number of recommendations to surface
RECOMMEND_COUNT = 5
# How many are unlocked free (everyone, every day)
FREE_RECOMMEND_COUNT = 1


def _kst_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=9)


def _kst_today_iso() -> str:
    return _kst_now().date().isoformat()


def is_in_free_trial(profile: UserProfile) -> bool:
    """True if user is within their first FREE_TRIAL_DAYS of Saju use."""
    if not profile.saju_first_used_at:
        return True  # never used → first use will be free
    try:
        first = datetime.fromisoformat(profile.saju_first_used_at).date()
    except ValueError:
        return True
    days_since = (_kst_now().date() - first).days
    return days_since < FREE_TRIAL_DAYS


def free_trial_days_remaining(profile: UserProfile) -> int:
    """Days remaining in free trial; 0 if expired."""
    if not profile.saju_first_used_at:
        return FREE_TRIAL_DAYS
    try:
        first = datetime.fromisoformat(profile.saju_first_used_at).date()
    except ValueError:
        return FREE_TRIAL_DAYS
    days_since = (_kst_now().date() - first).days
    return max(0, FREE_TRIAL_DAYS - days_since)


def has_birth_data(profile: UserProfile) -> bool:
    return bool(profile.saju_birth_date)


def make_saju_profile(profile: UserProfile) -> SajuProfile | None:
    """Build a SajuProfile from the user's stored birth data, or None."""
    if not profile.saju_birth_date:
        return None
    hour = profile.saju_birth_hour if profile.saju_birth_hour >= 0 else None
    return build_profile(profile.saju_birth_date, hour)


# ─────────────────────────────────────────────────────────────────────────────
# Public service ops
# ─────────────────────────────────────────────────────────────────────────────
async def save_birth_data(repo, user_key: str, *, birth_date: str,
                          birth_hour: int | None) -> UserProfile:
    """Persist birth date+hour. Validates by trying to build a SajuProfile."""
    sp = build_profile(birth_date, birth_hour)  # raises on bad input
    fields = {
        "saju_birth_date": sp.birth_date,
        "saju_birth_hour": birth_hour if birth_hour is not None else -1,
    }
    return await _maybe_async_update(repo, user_key, fields)


async def mark_first_use(repo, user_key: str, profile: UserProfile) -> UserProfile:
    """Stamp first-use date if not already stamped (anchors free-trial window)."""
    if profile.saju_first_used_at:
        return profile
    return await _maybe_async_update(
        repo, user_key, {"saju_first_used_at": _kst_today_iso()},
    )


async def reset_unlocks_if_new_day(repo, user_key: str,
                                   profile: UserProfile) -> UserProfile:
    """Reset the daily-unlocked tickers list at KST midnight."""
    today = _kst_today_iso()
    if profile.saju_unlocked_date_kst == today:
        return profile
    return await _maybe_async_update(repo, user_key, {
        "saju_unlocked_today": [],
        "saju_unlocked_date_kst": today,
    })


def _seed_for(user_key: str, kst_date: str) -> int:
    """Stable per-user × per-day seed so picks are consistent within a day."""
    return abs(hash(f"{user_key}|{kst_date}")) % (2**31)


def get_today_recommendations(profile: UserProfile,
                              user_key: str) -> tuple[SajuProfile, TodaySaju, list[StockEntry]]:
    """Build SajuProfile, today's reading, and 5 picks (deterministic for the day)."""
    sp = make_saju_profile(profile)
    if sp is None:
        raise ValueError("birth_data_missing")
    ts = today_for(sp)
    seed = _seed_for(user_key, _kst_today_iso())
    picks = recommend_for_today(sp, ts, n=RECOMMEND_COUNT, seed=seed)
    return sp, ts, picks


def build_today_payload(profile: UserProfile, user_key: str) -> dict:
    """Full payload for /saju/today + /saju/recommend."""
    sp, ts, picks = get_today_recommendations(profile, user_key)
    summary = summary_lines_ko(sp, ts)

    free_trial = is_in_free_trial(profile)
    days_left = free_trial_days_remaining(profile)
    unlocked = set(profile.saju_unlocked_today)

    rec_payload = []
    for idx, p in enumerate(picks):
        # First card is always free; rest are locked unless: free trial, or unlocked today
        is_locked_default = idx >= FREE_RECOMMEND_COUNT
        unlocked_for_user = (
            (not is_locked_default)
            or free_trial
            or (p.ticker in unlocked)
        )
        rec_payload.append({
            "ticker": p.ticker,
            "name": p.name,
            "sector": p.sector,
            "industry": p.industry,
            "primary_element": p.primary_element,
            "secondary_element": p.secondary_element,
            "brand_color": p.brand_color,
            "rationale": explain_pick(p, sp, ts) if unlocked_for_user else None,
            "summary": p.business_summary if unlocked_for_user else None,
            "unlocked": unlocked_for_user,
            "unlock_cost_points": UNLOCK_POINT_COST if not unlocked_for_user else 0,
        })

    return {
        "saju": {
            "birth_date": sp.birth_date,
            "birth_hour": sp.birth_hour,
            "ilju": sp.ilju_label,
            "my_element": sp.my_element,
            "polarity": sp.polarity,
        },
        "today": {
            "date": ts.date,
            "ilju": ts.ilju_label,
            "today_element": ts.today_element,
            "relation": ts.relation,
            "relation_label": ts.relation_label,
            "fortune": ts.fortune,
            "favored_elements": ts.favored_elements_today,
        },
        "summary": summary,
        "recommendations": rec_payload,
        "free_trial": {
            "active": free_trial,
            "days_remaining": days_left,
            "trial_days": FREE_TRIAL_DAYS,
        },
        "unlock": {
            "cost_points": UNLOCK_POINT_COST,
            "unlocked_today_count": len(unlocked),
        },
        "disclaimer": DISCLAIMER_KO,
    }


async def unlock_ticker(repo, user_key: str, profile: UserProfile,
                        ticker: str, *, usage_logger=None) -> tuple[bool, str, UserProfile | None]:
    """Spend UNLOCK_POINT_COST to unlock one ticker for today.

    Returns (ok, reason, updated_profile).
    Reasons: "ok" | "already_unlocked" | "free_trial_active" |
             "ticker_not_in_today" | "insufficient_points"
    """
    profile = await reset_unlocks_if_new_day(repo, user_key, profile)

    if is_in_free_trial(profile):
        return True, "free_trial_active", profile

    # Validate ticker is one of today's recommendations
    _, _, picks = get_today_recommendations(profile, user_key)
    today_tickers = {p.ticker for p in picks}
    if ticker not in today_tickers:
        return False, "ticker_not_in_today", None

    if ticker in profile.saju_unlocked_today:
        return True, "already_unlocked", profile

    new_profile = await deduct_points(
        repo, user_key, UNLOCK_POINT_COST,
        reason="saju_unlock", ref=ticker,
        usage_logger=usage_logger,
    )
    if new_profile is None:
        return False, "insufficient_points", None

    new_unlocks = list(new_profile.saju_unlocked_today) + [ticker]
    new_profile = await _maybe_async_update(repo, user_key, {
        "saju_unlocked_today": new_unlocks,
        "saju_unlocked_date_kst": _kst_today_iso(),
    })
    return True, "ok", new_profile


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
async def _maybe_async_update(repo, user_key: str, fields: dict) -> UserProfile:
    """Repo.update may be async (Blob) or sync (SQLite). Handle both."""
    result = repo.update(user_key, **fields)
    if hasattr(result, "__await__"):
        return await result
    return result
