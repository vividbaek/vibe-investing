"""Tests for Saju (Four Pillars) lite engine."""

from __future__ import annotations

from datetime import date

import pytest

from services.saju_engine import (
    BRANCH_TO_ELEMENT,
    FORTUNE_KEYS,
    GENERATES,
    OVERCOMES,
    STEM_TO_ELEMENT,
    build_profile,
    day_pillar,
    favored_elements,
    fortune_scores,
    relation_between,
    summary_lines_ko,
    today_for,
)


class TestDayPillar:
    """Verify 60-갑자 calendar math against known anchors."""

    def test_anchor_1900_01_01(self) -> None:
        # 1900-01-01 = 甲戌 day (stem 0, branch 10)
        assert day_pillar(date(1900, 1, 1)) == (0, 10)

    def test_1900_01_31_is_galjin(self) -> None:
        # 30 days after anchor → 甲辰 day (stem 0, branch 4)
        assert day_pillar(date(1900, 1, 31)) == (0, 4)

    def test_60_day_cycle(self) -> None:
        """60 days later → same pillar."""
        assert day_pillar(date(1900, 1, 1)) == day_pillar(date(1900, 3, 2))

    def test_yajashi_advance(self) -> None:
        """hour ≥ 23 should advance day pillar by 1."""
        d = date(1990, 5, 15)
        without = day_pillar(d, hour=12)
        with_yaja = day_pillar(d, hour=23)
        # stem: +1, branch: +1
        assert with_yaja == ((without[0] + 1) % 10, (without[1] + 1) % 12)


class TestRelations:
    """Verify 오행 상생/상극 logic."""

    def test_generates_cycle(self) -> None:
        # 木→火→土→金→水→木
        chain = ["wood", "fire", "earth", "metal", "water", "wood"]
        for a, b in zip(chain, chain[1:]):
            assert GENERATES[a] == b

    def test_overcomes_cycle(self) -> None:
        # 木→土, 土→水, 水→火, 火→金, 金→木
        assert OVERCOMES["wood"] == "earth"
        assert OVERCOMES["earth"] == "water"
        assert OVERCOMES["water"] == "fire"
        assert OVERCOMES["fire"] == "metal"
        assert OVERCOMES["metal"] == "wood"

    def test_relation_bi(self) -> None:
        assert relation_between("wood", "wood") == "bi"

    def test_relation_saeng_in(self) -> None:
        # water generates wood → relation is saeng_in for wood
        assert relation_between("water", "wood") == "saeng_in"

    def test_relation_saeng_out(self) -> None:
        # wood generates fire → relation is saeng_out for wood
        assert relation_between("fire", "wood") == "saeng_out"

    def test_relation_geuk_in(self) -> None:
        # metal overcomes wood → relation is geuk_in for wood
        assert relation_between("metal", "wood") == "geuk_in"

    def test_relation_geuk_out(self) -> None:
        # wood overcomes earth → relation is geuk_out for wood
        assert relation_between("earth", "wood") == "geuk_out"


class TestFortuneScores:
    """Score sanity checks."""

    def test_geuk_out_high_wealth(self) -> None:
        s = fortune_scores("geuk_out", "wood", "wood")
        assert s["wealth"] >= 70

    def test_saeng_in_high_study(self) -> None:
        s = fortune_scores("saeng_in", "wood", "wood")
        assert s["study"] >= 80

    def test_geuk_in_low_health(self) -> None:
        s = fortune_scores("geuk_in", "wood", "fire")
        assert s["health"] <= 55

    def test_all_keys_present(self) -> None:
        s = fortune_scores("bi", "wood", "wood")
        assert set(s.keys()) == set(FORTUNE_KEYS)

    def test_scores_in_range(self) -> None:
        for rel in ("bi", "saeng_in", "saeng_out", "geuk_in", "geuk_out"):
            for branch_a in ("wood", "fire", "earth", "metal", "water"):
                for branch_b in ("wood", "fire", "earth", "metal", "water"):
                    s = fortune_scores(rel, branch_a, branch_b)
                    for v in s.values():
                        assert 10 <= v <= 95


class TestFavoredElements:
    def test_geuk_out_favors_overcome(self) -> None:
        # wood me, geuk_out → favors earth (what wood overcomes)
        favored = favored_elements("wood", "geuk_out")
        assert favored[0] == "earth"

    def test_geuk_in_favors_protector(self) -> None:
        # wood me, geuk_in → favors water (what generates wood, the protector)
        favored = favored_elements("wood", "geuk_in")
        assert favored[0] == "water"

    def test_saeng_in_favors_generator(self) -> None:
        # wood me, saeng_in → favors water (the generator)
        favored = favored_elements("wood", "saeng_in")
        assert favored[0] == "water"


class TestBuildProfile:
    def test_basic(self) -> None:
        p = build_profile("1990-05-15", 14)
        assert p.birth_date == "1990-05-15"
        assert p.birth_hour == 14
        # 1990-05-15 = day_pillar computed
        s, b = day_pillar(date(1990, 5, 15))
        assert p.day_stem_idx == s
        assert p.day_branch_idx == b
        assert p.my_element == STEM_TO_ELEMENT[s]
        assert p.day_branch_element == BRANCH_TO_ELEMENT[b]

    def test_unknown_hour(self) -> None:
        p = build_profile("1990-05-15", None)
        assert p.birth_hour is None
        assert p.hour_branch_idx is None

    def test_yajashi(self) -> None:
        p_late = build_profile("1990-05-15", 23)
        p_early = build_profile("1990-05-16", 0)
        # 야자시 23:00 of May 15 → uses May 16 day pillar
        assert p_late.day_stem_idx == p_early.day_stem_idx
        assert p_late.day_branch_idx == p_early.day_branch_idx


class TestTodayFor:
    def test_returns_all_fields(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        assert t.date == "2026-05-07"
        assert t.relation in {"bi", "saeng_in", "saeng_out", "geuk_in", "geuk_out"}
        assert set(t.fortune.keys()) == set(FORTUNE_KEYS)
        assert len(t.favored_elements_today) >= 2

    def test_relation_consistency(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        assert t.relation == relation_between(t.today_element, p.my_element)


class TestSummaryLines:
    def test_six_axes_present(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        s = summary_lines_ko(p, t)
        for k in ("재물", "사업", "학업", "연애", "건강", "주의할 점", "오늘의 투자 포인트"):
            assert k in s
            assert len(s[k]) > 0

    def test_score_in_blurb(self) -> None:
        p = build_profile("1990-05-15", 14)
        t = today_for(p, date(2026, 5, 7))
        s = summary_lines_ko(p, t)
        # Wealth blurb should contain its numeric score
        assert str(t.fortune["wealth"]) in s["재물"]
