/**
 * 사주(四柱) 라이트 엔진 — AIInvestor services/saju_engine.py 충실 포팅(결정론, LLM 불필요).
 * 일주(日柱) 오행 × 오늘 일진의 상생·상극 → 5운(재물/사업/학업/연애/건강) + 해설.
 */

const STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"];
const STEMS_HJ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"];
const BRANCHES_HJ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

type Element = "wood" | "fire" | "earth" | "metal" | "water";
const STEM_TO_ELEMENT: Element[] = ["wood", "wood", "fire", "fire", "earth", "earth", "metal", "metal", "water", "water"];
const STEM_POLARITY = ["yang", "yin", "yang", "yin", "yang", "yin", "yang", "yin", "yang", "yin"];
const BRANCH_TO_ELEMENT: Element[] = [
  "water", "earth", "wood", "wood", "earth", "fire", "fire", "earth", "metal", "metal", "earth", "water",
];
export const ELEMENT_KR: Record<Element, string> = { wood: "목(木)", fire: "화(火)", earth: "토(土)", metal: "금(金)", water: "수(水)" };
export const ELEMENT_EMOJI: Record<Element, string> = { wood: "🌳", fire: "🔥", earth: "⛰️", metal: "⚒️", water: "💧" };

// 1900-01-01(KST) = 甲戌 (stem 0, branch 10)
const ANCHOR_UTC = Date.UTC(1900, 0, 1);
function daysSinceAnchor(y: number, m: number, d: number): number {
  return Math.floor((Date.UTC(y, m - 1, d) - ANCHOR_UTC) / 86400000);
}
function dayPillarIndex(y: number, m: number, d: number): [number, number] {
  const delta = daysSinceAnchor(y, m, d);
  return [((0 + delta) % 10 + 10) % 10, ((10 + delta) % 12 + 12) % 12];
}

const GENERATES: Record<Element, Element> = { wood: "fire", fire: "earth", earth: "metal", metal: "water", water: "wood" };
const OVERCOMES: Record<Element, Element> = { wood: "earth", earth: "water", water: "fire", fire: "metal", metal: "wood" };

export type Relation = "bi" | "saeng_in" | "saeng_out" | "geuk_in" | "geuk_out";
function relationBetween(today: Element, me: Element): Relation {
  if (today === me) return "bi";
  if (GENERATES[today] === me) return "saeng_in";
  if (GENERATES[me] === today) return "saeng_out";
  if (OVERCOMES[today] === me) return "geuk_in";
  return "geuk_out"; // OVERCOMES[me] === today
}
export const RELATION_LABEL_KR: Record<Relation, string> = {
  bi: "비화(比和)", saeng_in: "인성(印星)", saeng_out: "식상(食傷)", geuk_in: "관성(官星)", geuk_out: "재성(財星)",
};

const BASE_SCORES: Record<string, Record<Relation, number>> = {
  wealth: { bi: 55, saeng_in: 60, saeng_out: 65, geuk_in: 45, geuk_out: 80 },
  business: { bi: 60, saeng_in: 55, saeng_out: 80, geuk_in: 50, geuk_out: 75 },
  study: { bi: 60, saeng_in: 85, saeng_out: 50, geuk_in: 70, geuk_out: 50 },
  love: { bi: 55, saeng_in: 60, saeng_out: 70, geuk_in: 50, geuk_out: 75 },
  health: { bi: 70, saeng_in: 75, saeng_out: 55, geuk_in: 45, geuk_out: 60 },
};
export const FORTUNE_KEYS = ["wealth", "business", "study", "love", "health"] as const;
export const FORTUNE_KR: Record<string, string> = { wealth: "재물운", business: "사업운", study: "학업운", love: "연애운", health: "건강운" };

function fortuneScores(rel: Relation, dayBranchElem: Element, todayBranchElem: Element): Record<string, number> {
  let bonus = 0;
  if (todayBranchElem === dayBranchElem) bonus = 5;
  else if (OVERCOMES[todayBranchElem] === dayBranchElem) bonus = -5;
  else if (OVERCOMES[dayBranchElem] === todayBranchElem) bonus = 3;
  const out: Record<string, number> = {};
  for (const axis of FORTUNE_KEYS) out[axis] = Math.max(10, Math.min(95, BASE_SCORES[axis][rel] + bonus));
  return out;
}

function favoredElements(me: Element, rel: Relation): Element[] {
  const meGenerator = (Object.keys(GENERATES) as Element[]).find((k) => GENERATES[k] === me)!;
  const meGenerates = GENERATES[me];
  const meOvercomes = OVERCOMES[me];
  if (rel === "geuk_out") return [meOvercomes, me, meGenerates];
  if (rel === "saeng_out") return [me, meGenerates, meOvercomes];
  if (rel === "saeng_in") return [meGenerator, me, meGenerates];
  if (rel === "geuk_in") return [meGenerator, me];
  return [me, meGenerates, meGenerator];
}

export interface SajuProfile {
  birthDate: string;
  birthHour: number | null;
  dayStemIdx: number;
  dayBranchIdx: number;
  myElement: Element;
  dayBranchElement: Element;
  polarity: string;
  iljuLabel: string;
}
export interface TodaySaju {
  date: string;
  todayElement: Element;
  todayBranchElement: Element;
  relation: Relation;
  relationLabel: string;
  fortune: Record<string, number>;
  favored: Element[];
  iljuLabel: string;
}

function iljuLabel(stem: number, branch: number): string {
  return `${STEMS_KR[stem]}${BRANCHES_KR[branch]}(${STEMS_HJ[stem]}${BRANCHES_HJ[branch]})`;
}

export function buildProfile(birthDate: string, birthHour: number | null): SajuProfile {
  const [y, m, d] = birthDate.split("-").map(Number);
  let yy = y, mm = m, dd = d;
  if (birthHour !== null && birthHour >= 23) {
    const nx = new Date(Date.UTC(y, m - 1, d + 1));
    yy = nx.getUTCFullYear(); mm = nx.getUTCMonth() + 1; dd = nx.getUTCDate();
  }
  const [stem, branch] = dayPillarIndex(yy, mm, dd);
  return {
    birthDate, birthHour,
    dayStemIdx: stem, dayBranchIdx: branch,
    myElement: STEM_TO_ELEMENT[stem],
    dayBranchElement: BRANCH_TO_ELEMENT[branch],
    polarity: STEM_POLARITY[stem],
    iljuLabel: iljuLabel(stem, branch),
  };
}

export function todayFor(profile: SajuProfile, todayKst?: Date): TodaySaju {
  const now = todayKst ?? new Date(Date.now() + 9 * 3600 * 1000); // KST
  const y = now.getUTCFullYear(), m = now.getUTCMonth() + 1, d = now.getUTCDate();
  const [stem, branch] = dayPillarIndex(y, m, d);
  const todayElem = STEM_TO_ELEMENT[stem];
  const todayBranchElem = BRANCH_TO_ELEMENT[branch];
  const rel = relationBetween(todayElem, profile.myElement);
  return {
    date: `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
    todayElement: todayElem,
    todayBranchElement: todayBranchElem,
    relation: rel,
    relationLabel: RELATION_LABEL_KR[rel],
    fortune: fortuneScores(rel, profile.dayBranchElement, todayBranchElem),
    favored: favoredElements(profile.myElement, rel),
    iljuLabel: iljuLabel(stem, branch),
  };
}

// --- 해설 (saju_engine.py summary_lines_ko) ---
const REL_PHRASE: Record<Relation, string> = {
  bi: "동료·경쟁자가 가까운 날", saeng_in: "외부의 도움·기회가 흐르는 날", saeng_out: "내 에너지를 표현·소비하는 날",
  geuk_in: "압박·시험·검증이 들어오는 날", geuk_out: "내가 주도해 결과를 만드는 날",
};
const INV_FOCUS: Record<Relation, string> = {
  bi: "동종업·시너지 종목으로 분산. 무리한 추격매수는 자제.",
  saeng_in: "안정·블루칩 위주. 정보·연구·교육 섹터에 기회.",
  saeng_out: "표현·미디어·소비재. 단기 모멘텀에 활동 활발.",
  geuk_in: "방어주·필수소비재·헬스케어. 손절선 명확히 둘 것.",
  geuk_out: "성장·재무 강한 기업. 차익 실현 타이밍 좋음.",
};
const BLURBS: Record<string, Record<Relation, string>> = {
  wealth: { geuk_out: "재성이 활성화 — 결과·수익이 따라오는 흐름.", saeng_out: "활동력은 좋지만 지출도 늘 수 있음.", saeng_in: "받는 운 — 외부 자금·기회가 들어옴.", bi: "동등한 흐름 — 협업으로 키울 만함.", geuk_in: "압박·지출 가능 — 무리한 베팅 금물." },
  business: { saeng_out: "추진력·아이디어가 발휘됨. 신규 기획에 유리.", geuk_out: "성과 결산·수금에 좋은 날.", saeng_in: "멘토·자원의 도움 받기 좋음.", bi: "파트너·동료와의 합이 중요.", geuk_in: "내부 점검·리스크 관리에 집중." },
  study: { saeng_in: "학습 흡수·집중력이 최상.", geuk_in: "도전적 과제·시험에 적기, 압박 견뎌낼 만함.", bi: "스터디·토론에 효과적.", geuk_out: "응용·실습 중심.", saeng_out: "표현·발표·정리에 좋음." },
  love: { geuk_out: "능동적 어필 — 내가 다가가는 흐름이 통함.", saeng_out: "감정 표현이 솔직해짐.", saeng_in: "안정·신뢰 기반 관계에 좋음.", bi: "동료·친구에서 발전 가능.", geuk_in: "갈등·시험 가능 — 인내 필요." },
  health: { saeng_in: "회복·휴식에 적합.", bi: "안정적 흐름 — 평소 페이스 유지.", geuk_out: "체력 소모 큼 — 무리하지 않기.", saeng_out: "에너지 발산 후 피로 가능.", geuk_in: "스트레스·면역 주의. 충분한 수면." },
};
const CAUTION: Record<Relation, string> = {
  bi: "비슷한 의견·동종업과의 충돌, 추격매수 자제.", saeng_in: "수동적이 되기 쉬움 — 결정 미루지 말 것.",
  saeng_out: "과소비·과활동 주의, 휴식 챙기기.", geuk_in: "스트레스성 결정·손절 회피 주의. 손절선 사수.",
  geuk_out: "욕심 과잉 주의 — 차익 실현 타이밍 놓치지 말 것.",
};
export function grade(score: number): string {
  return score >= 80 ? "매우 좋음" : score >= 65 ? "좋음" : score >= 50 ? "보통" : score >= 35 ? "주의" : "약함";
}
export interface SajuNarrative {
  header: string;
  axes: Array<{ key: string; label: string; score: number; grade: string; text: string }>;
  caution: string;
  invFocus: string;
}
export function narrative(profile: SajuProfile, today: TodaySaju): SajuNarrative {
  const rel = today.relation;
  const meKr = ELEMENT_KR[profile.myElement];
  const todayKr = ELEMENT_KR[today.todayElement];
  return {
    header: `${meKr} 일간 × 오늘 ${todayKr} 일진 → ${today.relationLabel} · ${REL_PHRASE[rel]}`,
    axes: (FORTUNE_KEYS as readonly string[]).map((k) => ({
      key: k, label: FORTUNE_KR[k], score: today.fortune[k], grade: grade(today.fortune[k]), text: BLURBS[k][rel],
    })),
    caution: CAUTION[rel],
    invFocus: INV_FOCUS[rel],
  };
}

export const SAJU_DISCLAIMER =
  "※ 본 사주 풀이는 일주 기준 오행 우세와 오늘 일진의 상생·상극만으로 산출한 간이 결과이며, 명리학의 통변이 완벽하지 않아 실제 투자 시 전문가의 도움이 필요합니다. 본 결과는 투자의 결과를 책임지지 않습니다.";
