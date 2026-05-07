"""Tests for stock_classifier and stock_recommender."""

from __future__ import annotations

from datetime import date

from services.saju_engine import build_profile, today_for
from services.stock_classifier import classify, color_to_element
from services.stock_recommender import (
    all_entries,
    by_element,
    explain_pick,
    recommend_for_today,
)


class TestClassifier:
    def test_semiconductor_is_metal(self) -> None:
        c = classify(sector="Information Technology", industry="Semiconductors")
        assert c.primary == "metal"

    def test_biotech_is_wood(self) -> None:
        c = classify(sector="Health Care", industry="Biotechnology")
        assert c.primary == "wood"

    def test_reit_is_earth(self) -> None:
        c = classify(sector="Real Estate", industry="Industrial REIT")
        assert c.primary == "earth"

    def test_bank_is_metal(self) -> None:
        c = classify(sector="Financial Services", industry="Bank")
        assert c.primary == "metal"

    def test_telecom_is_water(self) -> None:
        c = classify(sector="Communication Services", industry="Telecom")
        assert c.primary == "water"

    def test_oil_midstream_overrides_energy_sector(self) -> None:
        # Pipelines should be water, not fire (despite being Energy sector)
        c = classify(sector="Energy", industry="Oil Gas Midstream")
        assert c.primary == "water"

    def test_software_is_fire(self) -> None:
        c = classify(sector="Information Technology", industry="Application Software")
        assert c.primary == "fire"

    def test_color_red_is_fire(self) -> None:
        assert color_to_element("#FF0000") == "fire"

    def test_color_green_is_wood(self) -> None:
        assert color_to_element("#00C805") == "wood"

    def test_color_blue_is_water(self) -> None:
        assert color_to_element("#1A1F71") == "water"

    def test_color_silver_is_metal(self) -> None:
        # Light grey
        assert color_to_element("#C0C0C0") == "metal"

    def test_unknown_falls_back_to_default(self) -> None:
        c = classify()
        assert c.primary == "earth"  # safe default
        assert c.source == "default"


class TestRecommender:
    def test_loader_loads_csv(self) -> None:
        entries = all_entries()
        assert len(entries) > 100

    def test_each_element_has_entries(self) -> None:
        for elem in ("wood", "fire", "earth", "metal", "water"):
            assert len(by_element(elem)) >= 5, f"too few {elem} stocks in CSV"

    def test_recommends_5(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        picks = recommend_for_today(p, t, n=5, seed=42)
        assert len(picks) == 5
        # All picks should be unique
        assert len({x.ticker for x in picks}) == 5

    def test_picks_match_favored_elements(self) -> None:
        # Wood me, geuk_out → favors earth + wood
        p = build_profile("1990-05-15", 14)
        # Force a known relation by picking a date — we don't control it directly,
        # so just check the picks' elements are consistent with favored_elements
        from services.saju_engine import favored_elements
        t = today_for(p, date(2026, 5, 7))
        favored = set(favored_elements(p.my_element, t.relation))
        picks = recommend_for_today(p, t, n=5, seed=1)
        # At least most of the picks should be in favored elements
        in_favored = sum(1 for x in picks if x.primary_element in favored)
        assert in_favored >= 3

    def test_deterministic_with_seed(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        a = recommend_for_today(p, t, n=5, seed=42)
        b = recommend_for_today(p, t, n=5, seed=42)
        assert [x.ticker for x in a] == [x.ticker for x in b]

    def test_explain_pick_returns_string(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        picks = recommend_for_today(p, t, n=1, seed=0)
        line = explain_pick(picks[0], p, t)
        assert picks[0].ticker in line
        assert len(line) > 20
