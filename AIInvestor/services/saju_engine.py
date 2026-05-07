"""Saju (Four Pillars) lite engine.

Scope (per product spec): 일주 기준 오행 우세 + 오늘 일진과의 상생/상극.
We compute the day pillar (일주) for both the user's birth and "today" using the
60-갑자 cycle anchored at a known reference date, then derive:
  - dominant_element: the user's day-master 천간 → 오행
  - today_element:    today's 일간 → 오행
  - relation:         생/극/비/설/모 between today_element ↔ dominant_element
  - fortune scores:   재물/사업/학업/연애/건강 (0–100), seeded by relation

This is intentionally NOT a full 4-pillars + 십신/대운 engine — see disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

# ─────────────────────────────────────────────────────────────────────────────
# 60갑자 anchor
# ─────────────────────────────────────────────────────────────────────────────
# 1900-01-01 (Gregorian, KST) → 甲戌 day (天干 0=甲, 地支 10=戌).
# Cross-check: 1900-01-31 (30 days later) → 甲辰 (stem 0, branch 4) ✓
# We index 천간 0=甲..9=癸, 지지 0=子..11=亥.
_ANCHOR_DATE = date(1900, 1, 1)
_ANCHOR_STEM_IDX = 0   # 甲
_ANCHOR_BRANCH_IDX = 10  # 戌

STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
STEMS_HJ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
BRANCHES_HJ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 천간 → 오행
STEM_TO_ELEMENT = {
    0: "wood", 1: "wood",   # 甲乙 → 木
    2: "fire", 3: "fire",   # 丙丁 → 火
    4: "earth", 5: "earth",  # 戊己 → 土
    6: "metal", 7: "metal",  # 庚辛 → 金
    8: "water", 9: "water",  # 壬癸 → 水
}

# 천간 음양 (yang/yin). 갑/병/무/경/임 = 양, 을/정/기/신/계 = 음
STEM_POLARITY = {0: "yang", 1: "yin", 2: "yang", 3: "yin", 4: "yang",
                 5: "yin", 6: "yang", 7: "yin", 8: "yang", 9: "yin"}

# 지지 → 오행 (주기, 본기 기준)
BRANCH_TO_ELEMENT = {
    0: "water",   # 子
    1: "earth",   # 丑
    2: "wood",    # 寅
    3: "wood",    # 卯
    4: "earth",   # 辰
    5: "fire",    # 巳
    6: "fire",    # 午
    7: "earth",   # 未
    8: "metal",   # 申
    9: "metal",   # 酉
    10: "earth",  # 戌
    11: "water",  # 亥
}

ELEMENT_KR = {"wood": "목(木)", "fire": "화(火)", "earth": "토(土)",
              "metal": "금(金)", "water": "수(水)"}
ELEMENT_EMOJI = {"wood": "🌳", "fire": "🔥", "earth": "⛰️",
                 "metal": "⚒️", "water": "💧"}

# ─────────────────────────────────────────────────────────────────────────────
# Time → day pillar
# ─────────────────────────────────────────────────────────────────────────────
# 일주는 "자시(子時) 23:00" 부터 다음 날로 넘긴다 (전통). 출생시각이 23:00 이후면 +1일.
# birth_hour: 0–23 (KST). None이면 야자시 보정 안 함.
def _day_pillar_index(d: date) -> tuple[int, int]:
    """Return (stem_idx, branch_idx) for the given Gregorian date (KST)."""
    delta = (d - _ANCHOR_DATE).days
    stem = (_ANCHOR_STEM_IDX + delta) % 10
    branch = (_ANCHOR_BRANCH_IDX + delta) % 12
    return stem, branch


def day_pillar(d: date, hour: int | None = None) -> tuple[int, int]:
    """Day pillar (천간, 지지) indices for date+hour (KST).

    If hour ≥ 23, the pillar advances to the next day (야자시 convention).
    """
    if hour is not None and hour >= 23:
        d = d + timedelta(days=1)
    return _day_pillar_index(d)


# ─────────────────────────────────────────────────────────────────────────────
# 시지 (hour branch) — for time pillar branch only
# ─────────────────────────────────────────────────────────────────────────────
# 子시: 23:00–00:59, 축시: 01:00–02:59, …
_HOUR_TO_BRANCH = [
    0,  # 00 자
    1, 1,   # 01–02 축
    2, 2,   # 03–04 인
    3, 3,   # 05–06 묘
    4, 4,   # 07–08 진
    5, 5,   # 09–10 사
    6, 6,   # 11–12 오
    7, 7,   # 13–14 미
    8, 8,   # 15–16 신
    9, 9,   # 17–18 유
    10, 10,  # 19–20 술
    11, 11,  # 21–22 해
    0,      # 23 자 (야자시)
]


def hour_branch(hour: int) -> int:
    return _HOUR_TO_BRANCH[hour % 24]


# ─────────────────────────────────────────────────────────────────────────────
# 오행 상생/상극 관계
# ─────────────────────────────────────────────────────────────────────────────
# 상생(生): 木→火→土→金→水→木
GENERATES = {"wood": "fire", "fire": "earth", "earth": "metal",
             "metal": "water", "water": "wood"}
# 상극(克): 木→土, 土→水, 水→火, 火→金, 金→木
OVERCOMES = {"wood": "earth", "earth": "water", "water": "fire",
             "fire": "metal", "metal": "wood"}

Relation = Literal["bi", "saeng_in", "saeng_out", "geuk_in", "geuk_out"]


def relation_between(today: str, me: str) -> Relation:
    """Today's element vs me (day-master 일간 element)."""
    if today == me:
        return "bi"             # 비화(比和) — 같은 오행, 동료/경쟁
    if GENERATES.get(today) == me:
        return "saeng_in"       # 인성(印星) — 오늘이 나를 생함, 도움받음
    if GENERATES.get(me) == today:
        return "saeng_out"      # 식상(食傷) — 내가 오늘을 생함, 기운 소모
    if OVERCOMES.get(today) == me:
        return "geuk_in"        # 관성(官星) — 오늘이 나를 극함, 압박/시험
    if OVERCOMES.get(me) == today:
        return "geuk_out"       # 재성(財星) — 내가 오늘을 극함, 재물/성취
    raise AssertionError(f"unreachable: today={today} me={me}")


RELATION_LABEL_KR = {
    "bi": "비화(比和)", "saeng_in": "인성(印星)", "saeng_out": "식상(食傷)",
    "geuk_in": "관성(官星)", "geuk_out": "재성(財星)",
}


# ─────────────────────────────────────────────────────────────────────────────
# Fortune scoring
# ─────────────────────────────────────────────────────────────────────────────
# 재물/사업/학업/연애/건강 운 — relation × element-stability heuristics.
# 0–100 점수. relation이 핵심 시그널이고, 거기서 ±15 정도 흔들린다.

# Base scores for each (relation, fortune-axis) pair.
# - 재물(wealth): 재성(geuk_out)이 가장 좋음
# - 사업(business): 식상(saeng_out)이 활동력, 재성도 좋음
# - 학업(study): 인성(saeng_in)이 가장 좋음
# - 연애(love): 재성/식상이 외향적, 인성도 안정
# - 건강(health): 비화/인성이 안정, 관성/식상은 소모
_BASE_SCORES = {
    "wealth":   {"bi": 55, "saeng_in": 60, "saeng_out": 65, "geuk_in": 45, "geuk_out": 80},
    "business": {"bi": 60, "saeng_in": 55, "saeng_out": 80, "geuk_in": 50, "geuk_out": 75},
    "study":    {"bi": 60, "saeng_in": 85, "saeng_out": 50, "geuk_in": 70, "geuk_out": 50},
    "love":     {"bi": 55, "saeng_in": 60, "saeng_out": 70, "geuk_in": 50, "geuk_out": 75},
    "health":   {"bi": 70, "saeng_in": 75, "saeng_out": 55, "geuk_in": 45, "geuk_out": 60},
}

FORTUNE_KEYS = ("wealth", "business", "study", "love", "health")
FORTUNE_KR = {
    "wealth": "재물운", "business": "사업운", "study": "학업운",
    "love": "연애운", "health": "건강운",
}


def fortune_scores(relation: Relation, day_branch_element: str,
                   today_branch_element: str) -> dict[str, int]:
    """Compute 5 fortune scores 0–100 from relation + branch-element nuance."""
    out = {}
    # 지지 보정: today's branch element이 user's day-branch element과 같으면 +5,
    # 상극이면 -5 (지지는 보조 시그널).
    branch_bonus = 0
    if today_branch_element == day_branch_element:
        branch_bonus = 5
    elif OVERCOMES.get(today_branch_element) == day_branch_element:
        branch_bonus = -5
    elif OVERCOMES.get(day_branch_element) == today_branch_element:
        branch_bonus = 3

    for axis in FORTUNE_KEYS:
        base = _BASE_SCORES[axis][relation]
        score = max(10, min(95, base + branch_bonus))
        out[axis] = score
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Stock recommendation favored elements
# ─────────────────────────────────────────────────────────────────────────────
# Given a relation, what element(s) should we favor for stock picks?
# Logic: favor elements that BENEFIT the day-master 일간.
#   - bi:        same element → 비견 동료, 또 다른 같은 element가 무난
#   - saeng_in:  오늘이 me를 생 → element that generates me (인성) is good
#   - saeng_out: me가 오늘을 생 → me element is preferred (자기 표현)
#   - geuk_in:   오늘이 me를 극 → 인성(나를 생하는 것)이 보호막
#   - geuk_out:  me가 오늘을 극 → 재성(내가 극하는 것) — 재물의 날
def favored_elements(my_element: str, relation: Relation) -> list[str]:
    """Ordered list of favored elements for stock picks today."""
    # element that generates me (인성)
    me_generator = next(
        (k for k, v in GENERATES.items() if v == my_element), None,
    )
    # element I generate (식상)
    me_generates = GENERATES.get(my_element)
    # element I overcome (재성)
    me_overcomes = OVERCOMES.get(my_element)
    # element that overcomes me (관성) — generally avoid
    me_overcome_by = next(
        (k for k, v in OVERCOMES.items() if v == my_element), None,
    )

    if relation == "geuk_out":
        # 재물의 날 — favor 재성(내가 극하는 것), then me (energetic)
        return [me_overcomes, my_element, me_generates]
    if relation == "saeng_out":
        # 활동/표현 — favor me, then 식상
        return [my_element, me_generates, me_overcomes]
    if relation == "saeng_in":
        # 도움받는 날 — favor 인성(나를 생), then me
        return [me_generator, my_element, me_generates]
    if relation == "geuk_in":
        # 압박의 날 — favor 인성(나를 생, 보호) over 재성
        return [me_generator, my_element]
    # bi
    return [my_element, me_generates, me_generator]


# ─────────────────────────────────────────────────────────────────────────────
# Main API
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SajuProfile:
    birth_date: str       # ISO yyyy-mm-dd (KST)
    birth_hour: int | None  # 0–23 KST, None = unknown
    day_stem_idx: int     # 0–9 (일간)
    day_branch_idx: int   # 0–11 (일지)
    hour_branch_idx: int | None  # 0–11 (시지)
    my_element: str       # wood/fire/earth/metal/water (일간 기준)
    day_branch_element: str
    polarity: str         # yang / yin

    @property
    def stem_kr(self) -> str:
        return STEMS_KR[self.day_stem_idx]

    @property
    def branch_kr(self) -> str:
        return BRANCHES_KR[self.day_branch_idx]

    @property
    def stem_hj(self) -> str:
        return STEMS_HJ[self.day_stem_idx]

    @property
    def branch_hj(self) -> str:
        return BRANCHES_HJ[self.day_branch_idx]

    @property
    def ilju_label(self) -> str:
        """e.g. '경자(庚子)'"""
        return f"{self.stem_kr}{self.branch_kr}({self.stem_hj}{self.branch_hj})"


@dataclass(frozen=True)
class TodaySaju:
    date: str             # ISO yyyy-mm-dd (KST)
    day_stem_idx: int
    day_branch_idx: int
    today_element: str    # 일간 element
    today_branch_element: str
    relation: Relation    # vs user's my_element
    fortune: dict[str, int]
    favored_elements_today: list[str]

    @property
    def relation_label(self) -> str:
        return RELATION_LABEL_KR[self.relation]

    @property
    def ilju_label(self) -> str:
        return (
            f"{STEMS_KR[self.day_stem_idx]}{BRANCHES_KR[self.day_branch_idx]}"
            f"({STEMS_HJ[self.day_stem_idx]}{BRANCHES_HJ[self.day_branch_idx]})"
        )


def build_profile(birth_date: str, birth_hour: int | None) -> SajuProfile:
    """Parse ISO date + optional hour → SajuProfile."""
    d = datetime.strptime(birth_date, "%Y-%m-%d").date()
    stem_idx, branch_idx = day_pillar(d, birth_hour)
    h_branch = hour_branch(birth_hour) if birth_hour is not None else None
    elem = STEM_TO_ELEMENT[stem_idx]
    return SajuProfile(
        birth_date=birth_date,
        birth_hour=birth_hour,
        day_stem_idx=stem_idx,
        day_branch_idx=branch_idx,
        hour_branch_idx=h_branch,
        my_element=elem,
        day_branch_element=BRANCH_TO_ELEMENT[branch_idx],
        polarity=STEM_POLARITY[stem_idx],
    )


def today_for(profile: SajuProfile, today_kst: date | None = None) -> TodaySaju:
    """Compute today's 일진 + relation + fortune scores."""
    if today_kst is None:
        # KST = UTC+9
        today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date()
    stem_idx, branch_idx = _day_pillar_index(today_kst)
    today_elem = STEM_TO_ELEMENT[stem_idx]
    today_branch_elem = BRANCH_TO_ELEMENT[branch_idx]
    rel = relation_between(today_elem, profile.my_element)
    scores = fortune_scores(rel, profile.day_branch_element, today_branch_elem)
    favored = favored_elements(profile.my_element, rel)
    return TodaySaju(
        date=today_kst.isoformat(),
        day_stem_idx=stem_idx,
        day_branch_idx=branch_idx,
        today_element=today_elem,
        today_branch_element=today_branch_elem,
        relation=rel,
        fortune=scores,
        favored_elements_today=favored,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Narrative summary (used by /saju/today)
# ─────────────────────────────────────────────────────────────────────────────
DISCLAIMER_KO = (
    "※ 본 사주 풀이는 일주 기준 오행 우세와 오늘 일진의 상생·상극만으로 산출한 "
    "간이 결과이며, 명리학의 통변이 완벽하지 않아 실제 투자 시 전문가의 도움이 필요합니다. "
    "본 결과는 투자의 결과를 책임지지 않습니다."
)
DISCLAIMER_EN = (
    "※ This is a simplified Saju reading based only on day-master element + today's "
    "generation/overcoming relation. It is not a complete 명리학 interpretation. "
    "Please consult a professional for real investment decisions — we do not take "
    "responsibility for any investment outcomes."
)


def summary_lines_ko(profile: SajuProfile, today: TodaySaju) -> dict[str, str]:
    """Return 6-axis bullet summary for today (재물/사업/학업/연애/건강/주의)."""
    rel = today.relation
    me = profile.my_element
    me_kr = ELEMENT_KR[me]
    today_kr = ELEMENT_KR[today.today_element]
    relation_kr = RELATION_LABEL_KR[rel]

    rel_phrase = {
        "bi": "동료·경쟁자가 가까운 날",
        "saeng_in": "외부의 도움·기회가 흐르는 날",
        "saeng_out": "내 에너지를 표현·소비하는 날",
        "geuk_in": "압박·시험·검증이 들어오는 날",
        "geuk_out": "내가 주도해 결과를 만드는 날",
    }[rel]

    # Investment focus per relation
    inv_focus = {
        "bi": "동종업·시너지 종목으로 분산. 무리한 추격매수는 자제.",
        "saeng_in": "안정·블루칩 위주. 정보·연구·교육 섹터에 기회.",
        "saeng_out": "표현·미디어·소비재. 단기 모멘텀에 활동 활발.",
        "geuk_in": "방어주·필수소비재·헬스케어. 손절선 명확히 둘 것.",
        "geuk_out": "성장·재무 강한 기업. 차익 실현 타이밍 좋음.",
    }[rel]

    return {
        "헤더": (
            f"{me_kr} 일간 × 오늘 {today_kr} 일진 → {relation_kr} · {rel_phrase}"
        ),
        "재물": _wealth_blurb(rel, today.fortune["wealth"]),
        "사업": _business_blurb(rel, today.fortune["business"]),
        "학업": _study_blurb(rel, today.fortune["study"]),
        "연애": _love_blurb(rel, today.fortune["love"]),
        "건강": _health_blurb(rel, today.fortune["health"]),
        "주의할 점": _caution_blurb(rel),
        "오늘의 투자 포인트": inv_focus,
    }


def _grade(score: int) -> str:
    if score >= 80:
        return "매우 좋음"
    if score >= 65:
        return "좋음"
    if score >= 50:
        return "보통"
    if score >= 35:
        return "주의"
    return "약함"


def _wealth_blurb(rel: Relation, score: int) -> str:
    base = {
        "geuk_out": "재성이 활성화 — 결과·수익이 따라오는 흐름.",
        "saeng_out": "활동력은 좋지만 지출도 늘 수 있음.",
        "saeng_in": "받는 운 — 외부 자금·기회가 들어옴.",
        "bi": "동등한 흐름 — 협업으로 키울 만함.",
        "geuk_in": "압박·지출 가능 — 무리한 베팅 금물.",
    }[rel]
    return f"({score}점, {_grade(score)}) {base}"


def _business_blurb(rel: Relation, score: int) -> str:
    base = {
        "saeng_out": "추진력·아이디어가 발휘됨. 신규 기획에 유리.",
        "geuk_out": "성과 결산·수금에 좋은 날.",
        "saeng_in": "멘토·자원의 도움 받기 좋음.",
        "bi": "파트너·동료와의 합이 중요.",
        "geuk_in": "내부 점검·리스크 관리에 집중.",
    }[rel]
    return f"({score}점, {_grade(score)}) {base}"


def _study_blurb(rel: Relation, score: int) -> str:
    base = {
        "saeng_in": "학습 흡수·집중력이 최상.",
        "geuk_in": "도전적 과제·시험에 적기, 압박 견뎌낼 만함.",
        "bi": "스터디·토론에 효과적.",
        "geuk_out": "응용·실습 중심.",
        "saeng_out": "표현·발표·정리에 좋음.",
    }[rel]
    return f"({score}점, {_grade(score)}) {base}"


def _love_blurb(rel: Relation, score: int) -> str:
    base = {
        "geuk_out": "능동적 어필 — 내가 다가가는 흐름이 통함.",
        "saeng_out": "감정 표현이 솔직해짐.",
        "saeng_in": "안정·신뢰 기반 관계에 좋음.",
        "bi": "동료·친구에서 발전 가능.",
        "geuk_in": "갈등·시험 가능 — 인내 필요.",
    }[rel]
    return f"({score}점, {_grade(score)}) {base}"


def _health_blurb(rel: Relation, score: int) -> str:
    base = {
        "saeng_in": "회복·휴식에 적합.",
        "bi": "안정적 흐름 — 평소 페이스 유지.",
        "geuk_out": "체력 소모 큼 — 무리하지 않기.",
        "saeng_out": "에너지 발산 후 피로 가능.",
        "geuk_in": "스트레스·면역 주의. 충분한 수면.",
    }[rel]
    return f"({score}점, {_grade(score)}) {base}"


def _caution_blurb(rel: Relation) -> str:
    return {
        "bi": "비슷한 의견·동종업과의 충돌, 추격매수 자제.",
        "saeng_in": "수동적이 되기 쉬움 — 결정 미루지 말 것.",
        "saeng_out": "과소비·과활동 주의, 휴식 챙기기.",
        "geuk_in": "스트레스성 결정·손절 회피 주의. 손절선 사수.",
        "geuk_out": "욕심 과잉 주의 — 차익 실현 타이밍 놓치지 말 것.",
    }[rel]
