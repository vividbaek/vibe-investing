"""Tests for services.fortune_match — deterministic + uniform distribution."""

from __future__ import annotations

import pytest

from services.fortune_match import (
    build_risk_pool,
    classify_risk,
    select_daily_free_stock,
)


# Fixed reusable pool
_POOL = {
    "low":    ["JNJ", "PG",  "KO",  "WMT", "MCD", "PEP",  "T",   "VZ"],
    "medium": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "JPM", "V",  "MA"],
    "high":   ["TSLA", "NVDA", "AMD", "PLTR", "COIN", "MARA", "SHOP", "ARKK"],
}


class TestClassifyRisk:
    def test_none_is_low(self) -> None:
        assert classify_risk(None) == "low"

    def test_below_1_is_low(self) -> None:
        assert classify_risk(0.5) == "low"
        assert classify_risk(0.99) == "low"

    def test_1_to_1_5_is_medium(self) -> None:
        assert classify_risk(1.0) == "medium"
        assert classify_risk(1.49) == "medium"

    def test_above_1_5_is_high(self) -> None:
        assert classify_risk(1.5) == "high"
        assert classify_risk(3.0) == "high"


class TestBuildRiskPool:
    def test_groups_by_risk(self) -> None:
        entries = [
            {"ticker": "JNJ", "beta": 0.6},
            {"ticker": "AAPL", "beta": 1.2},
            {"ticker": "TSLA", "beta": 2.0},
        ]
        # Need ≥5 per tier → expand
        for t, b in [("PG", 0.5), ("KO", 0.7), ("WMT", 0.8), ("MCD", 0.9)]:
            entries.append({"ticker": t, "beta": b})
        for t in ["MSFT", "GOOGL", "AMZN", "META"]:
            entries.append({"ticker": t, "beta": 1.2})
        for t in ["NVDA", "AMD", "PLTR", "COIN"]:
            entries.append({"ticker": t, "beta": 2.0})
        pool = build_risk_pool(entries)
        assert "JNJ" in pool["low"]
        assert "AAPL" in pool["medium"]
        assert "TSLA" in pool["high"]

    def test_empty_pool_raises(self) -> None:
        with pytest.raises(ValueError, match="insufficient pool"):
            build_risk_pool([])

    def test_skips_blank_tickers(self) -> None:
        entries = [{"ticker": "", "beta": 1.0}]
        # Should still raise (no valid entries → all tiers under 5)
        with pytest.raises(ValueError):
            build_risk_pool(entries)


class TestSelectDailyFreeStock:
    def test_deterministic(self) -> None:
        """Same inputs 100x → same output."""
        first = select_daily_free_stock("19850315", "0830", "20260508", _POOL)
        for _ in range(100):
            again = select_daily_free_stock("19850315", "0830", "20260508", _POOL)
            assert again == first

    def test_different_today_changes_lucky_number(self) -> None:
        """Across 30 different `today` values, expect lucky_number variance."""
        seen = set()
        for d in range(1, 31):
            r = select_daily_free_stock(
                "19850315", "0830", f"202605{d:02d}", _POOL,
            )
            seen.add(r["lucky_number"])
        # At least 5 distinct lucky numbers should appear over 30 days
        assert len(seen) >= 5

    def test_returns_3_distinct_picks(self) -> None:
        r = select_daily_free_stock("19850315", "0830", "20260508", _POOL)
        free_t = r["free"]["ticker"]
        locked_ts = [p["ticker"] for p in r["locked"]]
        # All 3 tickers should be distinct (they come from different risk tiers)
        assert free_t not in locked_ts

    def test_lucky_number_in_range(self) -> None:
        for d in range(1, 100):
            r = select_daily_free_stock(
                f"19{(d % 100):02d}0101", "0830", "20260508", _POOL,
            )
            assert 0 <= r["lucky_number"] <= 9

    def test_two_locked_picks(self) -> None:
        r = select_daily_free_stock("19850315", "0830", "20260508", _POOL)
        assert len(r["locked"]) == 2
        assert {p["risk"] for p in r["locked"]} == set(
            ["low", "medium", "high"]) - {r["free"]["risk"]}

    def test_fortune_seed_is_16_hex(self) -> None:
        r = select_daily_free_stock("19850315", "0830", "20260508", _POOL)
        seed = r["fortune_seed"]
        assert len(seed) == 16
        assert all(c in "0123456789abcdef" for c in seed)

    def test_lucky_number_distribution_uniform(self) -> None:
        """1000 random user × today combos — Lucky number should be ~uniform."""
        from collections import Counter
        counts: Counter = Counter()
        for i in range(1000):
            r = select_daily_free_stock(
                f"19{(i % 90) + 10:02d}{(i % 12) + 1:02d}{(i % 28) + 1:02d}",
                f"{(i % 24):02d}30",
                f"2026{((i % 12) + 1):02d}{((i % 28) + 1):02d}",
                _POOL,
            )
            counts[r["lucky_number"]] += 1
        # Each bucket should hold ~100 ± 50 — chi-squared p > 0.05 for uniform
        for n in range(10):
            assert 50 <= counts[n] <= 150, f"lucky #{n} count = {counts[n]}"

    def test_unknown_birth_time(self) -> None:
        """birth_time='9999' (unknown hour) is allowed and deterministic."""
        a = select_daily_free_stock("19850315", "9999", "20260508", _POOL)
        b = select_daily_free_stock("19850315", "9999", "20260508", _POOL)
        assert a == b
