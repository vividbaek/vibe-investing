/**
 * 일1회 시그널 파이프라인 — run.py build() 의 Worker 판.
 * Yahoo(가격) + FRED(거시, best-effort) 수집 → ARDS/AMQS 엔진 → D1 signals + R2 스냅샷 + 상태 영속화.
 *
 * computeSignals 는 순수(데이터 in → 결과 out, Date/네트워크 없음) → 골든으로 단위테스트.
 */
import { runArds, toDashboardSignal as ardsToSignal } from "../../shared/strategy/ards/index";
import type { HystState } from "../../shared/strategy/ards/hysteresis";
import { runAmqs, AI_INFRA_TICKERS, toDashboardSignal as amqsToSignal } from "../../shared/strategy/amqs";
import {
  INDICES,
  COMPLEX,
  MACRO_MARKET,
  RATE_MARKET,
  FRED_SERIES,
  RATE_FRED,
} from "../../shared/strategy/ards/config";
import { pyRound } from "../../shared/strategy/series";
import type { DSeries } from "../../shared/strategy/ards/dseries";
import type { DashboardSignal } from "../../shared/strategy/types";

/** 수집 대상 심볼 (중복 제거). */
export const ARDS_YAHOO_SYMBOLS = [
  ...Object.keys(INDICES),
  ...Object.keys(COMPLEX),
  ...MACRO_MARKET,
  ...RATE_MARKET,
];
export const AMQS_YAHOO_SYMBOLS = [...AI_INFRA_TICKERS, "QQQ", "^VIX"];
export const ALL_YAHOO_SYMBOLS = [...new Set([...ARDS_YAHOO_SYMBOLS, ...AMQS_YAHOO_SYMBOLS])];
export const FRED_IDS = [...FRED_SERIES, ...RATE_FRED];

export interface SignalRow {
  date: string;
  strategy: "ARDS" | "AMQS";
  ticker: string;
  signal: DashboardSignal;
  score: number;
  detail_json: string;
}

export interface DailyPayload {
  date: string;
  updated_at: string | null;
  ards: ReturnType<typeof runArds>;
  amqs: { regime: ReturnType<typeof runAmqs>["regime"]; metrics: ReturnType<typeof runAmqs>["metrics"] };
  data_quality?: { yahoo_ok: number; yahoo_fail: number; fred_ok: number; fred_fail: number };
}

export interface ComputeResult {
  payload: DailyPayload;
  rows: SignalRow[];
  newState: HystState;
}

/** 순수 계산: px/fred + 직전 히스테리시스 상태 → 페이로드 + D1 행 + 새 상태. */
export function computeSignals(
  px: Record<string, DSeries>,
  fred: Record<string, DSeries>,
  prevState: HystState,
  today: string,
): ComputeResult {
  const ards = runArds(px, fred, prevState, today);

  const amqsInputs = AI_INFRA_TICKERS.filter((t) => px[t]).map((t) => ({ ticker: t, closes: px[t].values }));
  const amqs = runAmqs(amqsInputs, {
    qqqCloses: px["QQQ"]?.values,
    vixCloses: px["^VIX"]?.values,
  });

  const rows: SignalRow[] = [];

  // ARDS: 시장 국면 1행 (대표 티커 QQQ). 추세 붕괴면 매도가 아닌 한 단기하락 주의로.
  let ardsSig: DashboardSignal = ardsToSignal(ards.verdict.action);
  if (ardsSig !== "SELL" && ards.verdict.evidence.trend_broken) ardsSig = "SHORT_TERM_RISK";
  rows.push({
    date: today,
    strategy: "ARDS",
    ticker: "QQQ",
    signal: ardsSig,
    score: ards.verdict.confidence,
    detail_json: JSON.stringify(ards.verdict),
  });

  // AMQS: 종목별 (매핑 가능한 것만)
  for (const m of amqs.metrics) {
    const s = amqsToSignal(m.signal);
    if (s === null) continue;
    rows.push({
      date: today,
      strategy: "AMQS",
      ticker: m.ticker,
      signal: s,
      score: pyRound(m.totalScore100, 1),
      detail_json: JSON.stringify({
        amqs_signal: m.signal,
        subtheme: m.subtheme,
        total: pyRound(m.totalScore100, 1),
        weight: pyRound(m.weight, 4),
        selected: m.selected,
        regime: amqs.regime.label,
        reason: m.reason,
      }),
    });
  }

  return {
    payload: { date: today, updated_at: null, ards, amqs: { regime: amqs.regime, metrics: amqs.metrics } },
    rows,
    newState: ards.state,
  };
}
