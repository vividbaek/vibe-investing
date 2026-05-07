"""Tests for saju_service (orchestration layer)."""

from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.point_ledger import add_points
from services.saju_service import (
    FREE_RECOMMEND_COUNT,
    FREE_TRIAL_DAYS,
    RECOMMEND_COUNT,
    UNLOCK_POINT_COST,
    build_today_payload,
    free_trial_days_remaining,
    has_birth_data,
    is_in_free_trial,
    mark_first_use,
    save_birth_data,
    unlock_ticker,
)
from services.user_profile import UserProfileRepo


@pytest.fixture
def repo(tmp_path: Path) -> UserProfileRepo:
    db = tmp_path / "test.db"
    return UserProfileRepo(db, salt="test-salt")


def _kst_today_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()


def _kst_iso(days_ago: int) -> str:
    d = (datetime.now(timezone.utc) + timedelta(hours=9)).date() - timedelta(days=days_ago)
    return d.isoformat()


class TestSaveBirthData:
    def test_persists_date_and_hour(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        assert p.saju_birth_date == "1990-05-15"
        assert p.saju_birth_hour == 14

    def test_unknown_hour_persists_as_neg1(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=None))
        p = repo.get("u1")
        assert p.saju_birth_hour == -1

    def test_invalid_date_raises(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        with pytest.raises(ValueError):
            asyncio.run(save_birth_data(repo, "u1", birth_date="not-a-date", birth_hour=10))


class TestFreeTrial:
    def test_first_use_returns_full_trial(self, repo: UserProfileRepo) -> None:
        p = repo.get_or_create("u1", "ko", "buffett")
        assert is_in_free_trial(p) is True
        assert free_trial_days_remaining(p) == FREE_TRIAL_DAYS

    def test_within_trial(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_first_used_at=_kst_iso(2))
        p = repo.get("u1")
        assert is_in_free_trial(p) is True
        assert free_trial_days_remaining(p) == FREE_TRIAL_DAYS - 2

    def test_expired_trial(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        repo.update("u1", saju_first_used_at=_kst_iso(FREE_TRIAL_DAYS + 1))
        p = repo.get("u1")
        assert is_in_free_trial(p) is False
        assert free_trial_days_remaining(p) == 0

    def test_mark_first_use_idempotent(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        p = repo.get("u1")
        p2 = asyncio.run(mark_first_use(repo, "u1", p))
        first_stamp = p2.saju_first_used_at
        assert first_stamp != ""
        # Calling again should NOT overwrite
        p3 = asyncio.run(mark_first_use(repo, "u1", p2))
        assert p3.saju_first_used_at == first_stamp


class TestBuildTodayPayload:
    def test_payload_has_5_recommendations(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        assert len(payload["recommendations"]) == RECOMMEND_COUNT

    def test_during_free_trial_all_unlocked(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        assert all(r["unlocked"] for r in payload["recommendations"])

    def test_after_trial_only_first_unlocked(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        repo.update("u1", saju_first_used_at=_kst_iso(FREE_TRIAL_DAYS + 1))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        recs = payload["recommendations"]
        unlocked = [r for r in recs if r["unlocked"]]
        assert len(unlocked) == FREE_RECOMMEND_COUNT
        # Locked picks must hide rationale + summary
        locked = [r for r in recs if not r["unlocked"]]
        assert all(r["rationale"] is None for r in locked)
        assert all(r["unlock_cost_points"] == UNLOCK_POINT_COST for r in locked)

    def test_disclaimer_present(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        assert "전문가" in payload["disclaimer"]
        assert "투자의 결과를 책임" in payload["disclaimer"]

    def test_summary_six_axes(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        for axis in ("재물", "사업", "학업", "연애", "건강", "주의할 점", "오늘의 투자 포인트"):
            assert axis in payload["summary"]


class TestUnlockTicker:
    def test_free_trial_skips_payment(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        # User has 0 points but should still succeed
        ok, reason, _ = asyncio.run(unlock_ticker(repo, "u1", p, "AAPL"))
        assert ok is True
        assert reason == "free_trial_active"

    def test_unlock_after_trial_with_points(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        # Expire trial
        repo.update("u1", saju_first_used_at=_kst_iso(FREE_TRIAL_DAYS + 1))
        # Give enough points
        asyncio.run(add_points(repo, "u1", UNLOCK_POINT_COST + 10, "test_seed"))
        p = repo.get("u1")
        # Pick a ticker that's in today's recommendations
        payload = build_today_payload(p, "u1")
        target = payload["recommendations"][2]["ticker"]  # locked one
        ok, reason, updated = asyncio.run(unlock_ticker(repo, "u1", p, target))
        assert ok is True
        assert reason == "ok"
        assert updated.points_balance == 10  # debited UNLOCK_POINT_COST
        assert target in updated.saju_unlocked_today

    def test_unlock_insufficient_points(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        repo.update("u1", saju_first_used_at=_kst_iso(FREE_TRIAL_DAYS + 1))
        p = repo.get("u1")
        payload = build_today_payload(p, "u1")
        target = payload["recommendations"][2]["ticker"]
        ok, reason, updated = asyncio.run(unlock_ticker(repo, "u1", p, target))
        assert ok is False
        assert reason == "insufficient_points"
        assert updated is None

    def test_unlock_ticker_not_in_today(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        repo.update("u1", saju_first_used_at=_kst_iso(FREE_TRIAL_DAYS + 1))
        p = repo.get("u1")
        ok, reason, _ = asyncio.run(unlock_ticker(repo, "u1", p, "ZZZZ"))
        assert ok is False
        assert reason == "ticker_not_in_today"


class TestHasBirthData:
    def test_false_initially(self, repo: UserProfileRepo) -> None:
        p = repo.get_or_create("u1", "ko", "buffett")
        assert has_birth_data(p) is False

    def test_true_after_save(self, repo: UserProfileRepo) -> None:
        repo.get_or_create("u1", "ko", "buffett")
        asyncio.run(save_birth_data(repo, "u1", birth_date="1990-05-15", birth_hour=14))
        p = repo.get("u1")
        assert has_birth_data(p) is True
