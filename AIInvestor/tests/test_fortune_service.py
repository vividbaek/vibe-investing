"""Tests for fortune_service — risk pool loader + age check + idempotent unlock."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from services.fortune_service import (
    UNLOCK_COST_POINTS,
    get_risk_pool,
    is_age_19_or_older,
    is_already_unlocked_today,
    select_for_user,
    unlock_via_points,
    _kst_today_iso,
)
from services.point_ledger import add_points
from services.user_profile import UserProfileRepo


@pytest.fixture
def repo(tmp_path: Path) -> UserProfileRepo:
    return UserProfileRepo(tmp_path / "test.db", salt="test-salt")


class TestRiskPool:
    def test_loads_three_tiers(self) -> None:
        p = get_risk_pool()
        assert "low" in p and "medium" in p and "high" in p

    def test_each_tier_has_5_or_more(self) -> None:
        p = get_risk_pool()
        for tier in ("low", "medium", "high"):
            assert len(p[tier]) >= 5

    def test_skips_underscore_keys(self) -> None:
        """data/risk_pools.json contains a _comment key; loader must drop it."""
        p = get_risk_pool()
        assert all(not k.startswith("_") for k in p.keys())


class TestAgeCheck:
    def test_exactly_19_passes(self) -> None:
        assert is_age_19_or_older("2007-01-01", today_iso="2026-01-01")

    def test_18_years_11_months_fails(self) -> None:
        assert not is_age_19_or_older("2007-06-15", today_iso="2026-05-08")

    def test_30_years_passes(self) -> None:
        assert is_age_19_or_older("1996-05-08", today_iso="2026-05-08")

    def test_invalid_date_fails(self) -> None:
        assert not is_age_19_or_older("not-a-date")
        assert not is_age_19_or_older("")


class TestSelectForUser:
    def test_no_birth_returns_none(self, repo: UserProfileRepo) -> None:
        p = repo.get_or_create("u1", "ko", "buffett")
        assert select_for_user(p) is None

    def test_with_birth_returns_result(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_birth_date="1985-03-15", saju_birth_hour=8)
        p = repo.get("u1")
        r = select_for_user(p)
        assert r is not None
        assert "lucky_number" in r
        assert "free" in r and "ticker" in r["free"]
        assert len(r["locked"]) == 2


class TestIsAlreadyUnlockedToday:
    def test_unlocked_today_true(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_unlocked_today=["AAPL"],
                    saju_unlocked_date_kst=_kst_today_iso())
        p = repo.get("u1")
        assert is_already_unlocked_today(p, "AAPL")

    def test_unlocked_yesterday_false(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_unlocked_today=["AAPL"],
                    saju_unlocked_date_kst="2020-01-01")
        p = repo.get("u1")
        assert not is_already_unlocked_today(p, "AAPL")

    def test_different_ticker_false(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_unlocked_today=["AAPL"],
                    saju_unlocked_date_kst=_kst_today_iso())
        p = repo.get("u1")
        assert not is_already_unlocked_today(p, "TSLA")


class TestUnlockViaPoints:
    def test_insufficient_points(self, repo: UserProfileRepo) -> None:
        p = repo.get_or_create("u1", "ko", "buffett")
        ok, reason, updated = asyncio.run(unlock_via_points(repo, p, "AAPL"))
        assert not ok
        assert reason == "insufficient_points"
        assert updated is None

    def test_successful_unlock_deducts(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(add_points(repo, "u1", UNLOCK_COST_POINTS + 50, "test_seed"))
        p = repo.get("u1")
        assert p.points_balance == UNLOCK_COST_POINTS + 50
        ok, reason, updated = asyncio.run(unlock_via_points(repo, p, "AAPL"))
        assert ok
        assert reason == "ok"
        assert updated.points_balance == 50  # deducted UNLOCK_COST_POINTS
        assert "AAPL" in updated.saju_unlocked_today

    def test_idempotent_same_day(self, repo: UserProfileRepo) -> None:
        """Re-unlocking same ticker same day → no extra charge."""
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(add_points(repo, "u1", UNLOCK_COST_POINTS + 50, "test_seed"))
        # First unlock
        p1 = repo.get("u1")
        asyncio.run(unlock_via_points(repo, p1, "AAPL"))
        bal1 = repo.get("u1").points_balance
        # Second unlock (same ticker, same day) — should not deduct
        p2 = repo.get("u1")
        ok, reason, updated = asyncio.run(unlock_via_points(repo, p2, "AAPL"))
        assert ok
        assert reason == "already_unlocked"
        bal2 = repo.get("u1").points_balance
        assert bal1 == bal2
