"""§T2E-A — Atomic Point earn / spend ledger.

Two layers:

  1. **Profile fields** — points_cumulative / points_balance / points_this_season
     are the source of truth for "what the user has". Atomic via the repo's
     update() (SQLite row lock or Blob ETag).

  2. **NDJSON audit log** — every Point movement is appended to logs/<KST_date>/...
     for forensic recovery, abuse detection, and dashboards. Failures here
     are non-fatal (logged at WARNING) — never block the user-facing path.

Season rollover is handled inline: when a user's stored season_id != current,
their points_this_season is reset to 0 BEFORE applying the new credit/debit.

The `tier` field is recomputed on every credit (only goes up). The
caller's profile object reflects the post-credit tier so the UI can
react immediately ("you just hit GOLD!").
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .gamification_config import current_season_id
from .tier_calculator import compute_tier_stage
from .user_profile import UserProfile

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _audit_log(
    usage_logger,
    *,
    anon: str,
    event: str,
    amount: int,
    reason: str,
    ref: str | None,
    balance_after: int,
) -> None:
    """Best-effort audit logging. Reuses the existing usage_logger sink."""
    if usage_logger is None:
        return
    try:
        # Reuse the usage_logger.record() schema with custom tier=points_event
        await usage_logger.record(
            anon=anon,
            lang="",
            persona="",
            ticker=ref or "",
            tier=f"points_{event}_{reason}",
            duration_ms=0,
            llm_in=amount,            # repurpose: amount delta
            llm_out=balance_after,    # repurpose: balance after
        )
    except Exception:
        logger.exception("point audit log failed (non-fatal)")


async def add_points(
    repo,
    user_key: str,
    amount: int,
    reason: str,
    *,
    ref: str | None = None,
    usage_logger=None,
) -> UserProfile:
    """Atomic credit. Negative amount → use deduct_points() instead.

    Returns the updated profile (with new tier already computed).
    """
    if amount == 0:
        return await _read(repo, user_key)
    if amount < 0:
        raise ValueError("use deduct_points() for negative amounts")

    profile = await _read(repo, user_key)
    season = current_season_id()

    # Season rollover — clear points_this_season if quarter changed
    if profile.season_id != season:
        profile.points_this_season = 0
        profile.season_id = season

    new_cumulative = profile.points_cumulative + amount
    new_balance = profile.points_balance + amount
    new_seasonal = profile.points_this_season + amount

    new_tier, new_stage, _label = compute_tier_stage(new_cumulative, new_seasonal)
    tier_changed = (new_tier != profile.tier) or (new_stage != profile.tier_stage)

    update_fields = {
        "points_cumulative": new_cumulative,
        "points_balance": new_balance,
        "points_this_season": new_seasonal,
        "season_id": season,
        "tier": new_tier,
        "tier_stage": new_stage,
    }
    if tier_changed:
        update_fields["tier_updated_at"] = _now_iso()

    profile = await _update(repo, user_key, **update_fields)

    await _audit_log(
        usage_logger,
        anon=profile.anon_user_id,
        event="add",
        amount=amount,
        reason=reason,
        ref=ref,
        balance_after=new_balance,
    )
    logger.info(
        "+%d P → %s (reason=%s, balance=%d, tier=%s)",
        amount, user_key, reason, new_balance, new_tier,
    )
    return profile


async def deduct_points(
    repo,
    user_key: str,
    amount: int,
    reason: str,
    *,
    ref: str | None = None,
    usage_logger=None,
    allow_negative: bool = False,
) -> UserProfile | None:
    """Atomic debit. Returns the updated profile, or None if insufficient
    balance and allow_negative=False.

    Cumulative + seasonal points are NOT deducted (those are append-only
    accounting). Only points_balance moves.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    profile = await _read(repo, user_key)
    if profile.points_balance < amount and not allow_negative:
        return None

    new_balance = profile.points_balance - amount
    profile = await _update(repo, user_key, points_balance=new_balance)

    await _audit_log(
        usage_logger,
        anon=profile.anon_user_id,
        event="deduct",
        amount=-amount,
        reason=reason,
        ref=ref,
        balance_after=new_balance,
    )
    logger.info(
        "-%d P → %s (reason=%s, balance=%d)",
        amount, user_key, reason, new_balance,
    )
    return profile


async def adjust_for_penalty(
    repo,
    user_key: str,
    amount: int,
    reason: str,
    *,
    ref: str | None = None,
    usage_logger=None,
) -> UserProfile:
    """Penalty / clawback (zombie invitee, abuse). Reduces both balance
    AND cumulative (= effectively reverses prior credit). Allows negative
    balance — converts overdraft to a debt counter for next earnings."""
    if amount <= 0:
        raise ValueError("amount must be positive")

    profile = await _read(repo, user_key)
    season = current_season_id()
    if profile.season_id != season:
        profile.points_this_season = 0
        profile.season_id = season

    profile = await _update(
        repo, user_key,
        points_balance=profile.points_balance - amount,
        points_cumulative=max(0, profile.points_cumulative - amount),
        points_this_season=max(0, profile.points_this_season - amount),
        season_id=season,
    )

    await _audit_log(
        usage_logger,
        anon=profile.anon_user_id,
        event="penalty",
        amount=-amount,
        reason=reason,
        ref=ref,
        balance_after=profile.points_balance,
    )
    return profile


# ──────────────────────────────────────────────────────────
# Repo abstraction — works with sync (SQLite) or async (Blob)
# ──────────────────────────────────────────────────────────

async def _read(repo, user_key: str) -> UserProfile:
    """Read a profile from any repo. Works with sync (SQLite) and async (Blob).

    Detect-by-result pattern: call the method, then check if it returned a
    coroutine. The earlier `inspect.iscoroutinefunction(repo.get)` check
    fails because bound methods don't expose __await__ — only the COROUTINE
    that's the *result* of calling them does.
    """
    res = repo.get(user_key) if hasattr(repo, "get") else repo.get_or_create(
        user_key, "en", "buffett"
    )
    if hasattr(res, "__await__"):
        return await res
    return res


async def _update(repo, user_key: str, **fields) -> UserProfile:
    res = repo.update(user_key, **fields)
    if hasattr(res, "__await__"):
        return await res
    return res
