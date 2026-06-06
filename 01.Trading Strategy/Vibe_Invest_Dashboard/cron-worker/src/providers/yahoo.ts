/**
 * Yahoo Finance chart API provider (무료, 키 불필요).
 * 엔진이 쓰는 심볼(^GSPC, ^NDX, ^TNX, ^VIX, ^MOVE, 종목/ETF)을 그대로 사용.
 * Stooq 는 봇 차단(PoW)으로 Worker fetch 부적합 → Yahoo chart 채택.
 *
 * 날짜는 timestamp(UTC) 기반 YYYY-MM-DD. 같은 거래일이면 모든 심볼이 동일 문자열 →
 * ARDS macro 의 비율 교집합(ratioIntersect) 정렬이 일관되게 동작(엔진은 위치 인덱싱이라 캘린더값 무관).
 */
import type { DSeries } from "../../../shared/strategy/ards/dseries";

interface YahooChartJson {
  chart: {
    result?: Array<{
      timestamp?: number[];
      indicators: {
        quote: Array<{ close?: Array<number | null> }>;
        adjclose?: Array<{ adjclose?: Array<number | null> }>;
      };
    }>;
    error?: unknown;
  };
}

/** chart JSON → DSeries. adjclose 우선(yfinance Adj Close 대응), null 일봉 제거. */
export function parseYahooChart(json: YahooChartJson): DSeries {
  const r = json.chart?.result?.[0];
  if (!r || !r.timestamp) throw new Error("yahoo: empty result");
  const ts = r.timestamp;
  const adj = r.indicators.adjclose?.[0]?.adjclose;
  const close = r.indicators.quote?.[0]?.close;
  const series = adj ?? close;
  if (!series) throw new Error("yahoo: no close series");

  const dates: string[] = [];
  const values: number[] = [];
  for (let i = 0; i < ts.length; i++) {
    const v = series[i];
    if (v === null || v === undefined || Number.isNaN(v)) continue;
    dates.push(new Date(ts[i] * 1000).toISOString().slice(0, 10));
    values.push(v);
  }
  return { dates, values };
}

const YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/";

/** 단일 심볼 일봉 수집. range 예: '2y'(약 504거래일 → 420 룩백 충분). */
export async function fetchDaily(symbol: string, range = "2y"): Promise<DSeries> {
  const url = `${YAHOO_BASE}${encodeURIComponent(symbol)}?range=${range}&interval=1d`;
  const res = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" } });
  if (!res.ok) throw new Error(`yahoo ${symbol}: HTTP ${res.status}`);
  return parseYahooChart((await res.json()) as YahooChartJson);
}

/**
 * 여러 심볼 순차 수집(부분 성공 허용 — 한 심볼 실패가 전체를 죽이지 않음).
 * Workers 무료 subrequest 한도(50/req) 내에서 사용. 실패 심볼은 결과에서 누락 + failures 에 기록.
 */
export async function fetchDailyMany(
  symbols: string[],
  range = "2y",
): Promise<{ data: Record<string, DSeries>; failures: Record<string, string> }> {
  const data: Record<string, DSeries> = {};
  const failures: Record<string, string> = {};
  for (const s of symbols) {
    try {
      const ds = await fetchDaily(s, range);
      if (ds.values.length > 0) data[s] = ds;
      else failures[s] = "empty";
    } catch (e) {
      failures[s] = String(e);
    }
  }
  return { data, failures };
}
