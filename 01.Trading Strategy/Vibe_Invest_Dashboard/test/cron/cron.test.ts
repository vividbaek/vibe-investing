import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { parseYahooChart, parseQuoteFromChart, parseScreener } from "../../cron-worker/src/providers/yahoo";
import { buildMarketSnapshot, buildMovers } from "../../cron-worker/src/market";
import { parseFredCsv } from "../../cron-worker/src/providers/fred";
import { computeSignals } from "../../cron-worker/src/signals";
import { persistSignals } from "../../cron-worker/src/daily";
import { isUsMarketWindowUtc } from "../../cron-worker/src/market";
import { reconcileWithCache, putSeries, getSeries, type R2Like } from "../../cron-worker/src/cache";
import { freshState } from "../../shared/strategy/ards/hysteresis";
import { AI_INFRA_TICKERS } from "../../shared/strategy/amqs";
import type { DSeries } from "../../shared/strategy/ards/dseries";

describe("providers/yahoo parseYahooChart", () => {
  it("adjclose 우선 + null 일봉 제거 + UTC 날짜", () => {
    const json = {
      chart: {
        result: [
          {
            timestamp: [1704067200, 1704153600, 1704240000], // 2024-01-01,02,03
            indicators: {
              quote: [{ close: [100, null, 102] }],
              adjclose: [{ adjclose: [99.5, null, 101.5] }],
            },
          },
        ],
      },
    };
    const ds = parseYahooChart(json);
    expect(ds.values).toEqual([99.5, 101.5]); // adjclose, null 제거
    expect(ds.dates).toEqual(["2024-01-01", "2024-01-03"]);
  });
  it("adjclose 없으면 close 사용", () => {
    const ds = parseYahooChart({
      chart: { result: [{ timestamp: [1704067200], indicators: { quote: [{ close: [50] }] } }] },
    });
    expect(ds.values).toEqual([50]);
  });
  it("빈 결과는 throw", () => {
    expect(() => parseYahooChart({ chart: {} })).toThrow();
  });
});

describe("providers/fred parseFredCsv", () => {
  it("헤더 스킵 + '.' 결측 제거", () => {
    const ds = parseFredCsv("DATE,VALUE\n2024-01-01,4.5\n2024-01-02,.\n2024-01-03,4.6\n");
    expect(ds.dates).toEqual(["2024-01-01", "2024-01-03"]);
    expect(ds.values).toEqual([4.5, 4.6]);
  });
});

describe("yahoo quote/screener 파싱", () => {
  it("parseQuoteFromChart: meta 현재가·전일종가→등락%", () => {
    const q = parseQuoteFromChart({ chart: { result: [{ meta: { regularMarketPrice: 705.06, chartPreviousClose: 740.61 } }] } });
    expect(q.price).toBe(705.06);
    expect(q.chgPct).toBeCloseTo(-4.8, 1);
  });
  it("parseScreener: quotes→행 추출", () => {
    const rows = parseScreener({
      finance: {
        result: [
          {
            quotes: [
              { symbol: "COO", shortName: "Cooper", regularMarketPrice: 67.34, regularMarketChangePercent: 8.57, regularMarketVolume: 9084331 },
              { symbol: "BAD" }, // 불완전 → 제외
            ],
          },
        ],
      },
    });
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({ ticker: "COO", name: "Cooper", price: 67.34 });
  });
});

describe("buildMarketSnapshot 조립 (intraday, movers 제외)", () => {
  it("지수·섹터·VIX·리스크게이지", () => {
    const quotes = {
      SPY: { price: 560, prevClose: 550, chgPct: 1.818 },
      QQQ: { price: 700, prevClose: 690, chgPct: 1.449 },
      "^VIX": { price: 15, prevClose: 16, chgPct: -6.25 },
      XLK: { price: 200, prevClose: 195, chgPct: 2.56 },
      XLF: { price: 40, prevClose: 40.5, chgPct: -1.23 },
    };
    const snapshot = buildMarketSnapshot(quotes, "2026-06-06T20:00:00Z");
    expect(snapshot.indices.find((i) => i.ticker === "SPY")?.chg_pct).toBe(1.82);
    expect(snapshot.vix).toBe(15);
    expect(snapshot.sectors).toHaveLength(2);
    expect(snapshot.breadth).toEqual({ sectors_up: 1, sectors_down: 1 });
    expect(snapshot.risk_score).toBeGreaterThanOrEqual(0);
    expect(snapshot.risk_score).toBeLessThanOrEqual(100);
    expect(["RISK_OFF", "NEUTRAL", "RISK_ON"]).toContain(snapshot.risk_label);
    expect(snapshot).not.toHaveProperty("movers");
  });
});

describe("buildMovers (장종료 후 1회)", () => {
  it("급등/급락 리스트 + D1 행", () => {
    const gainers = [
      { ticker: "AAA", name: "Alpha", price: 10, chgPct: 20.1, volume: 1_000_000 },
      { ticker: "BBB", name: "Beta", price: 5, chgPct: 15.4, volume: 800_000 },
    ];
    const losers = [{ ticker: "ZZZ", name: "Zeta", price: 3, chgPct: -18.2, volume: 900_000 }];
    const { gainers: g, losers: l, rows } = buildMovers(gainers, losers, "2026-06-06T20:00:00Z");
    expect(g[0]).toMatchObject({ rank: 1, ticker: "AAA", chg_pct: 20.1 });
    expect(l[0]).toMatchObject({ rank: 1, ticker: "ZZZ", chg_pct: -18.2 });
    expect(rows).toHaveLength(3);
    expect(rows[0]).toEqual(["2026-06-06T20:00:00Z", "gainer", 1, "AAA", "Alpha", 10, 20.1, 1_000_000]);
  });
});

describe("market off-hours guard", () => {
  it("UTC 13:00–21:30 안=true, 밖=false", () => {
    expect(isUsMarketWindowUtc(new Date("2026-06-05T14:00:00Z"))).toBe(true);
    expect(isUsMarketWindowUtc(new Date("2026-06-05T21:30:00Z"))).toBe(true);
    expect(isUsMarketWindowUtc(new Date("2026-06-05T02:00:00Z"))).toBe(false);
    expect(isUsMarketWindowUtc(new Date("2026-06-05T22:00:00Z"))).toBe(false);
  });
});

describe("computeSignals — 엔진 배선 (골든 데이터 기반)", () => {
  const ardsG = JSON.parse(readFileSync(new URL("../fixtures/ards_golden.json", import.meta.url), "utf8"));
  const amqsG = JSON.parse(readFileSync(new URL("../fixtures/amqs_golden.json", import.meta.url), "utf8"));

  // AMQS 입력(가격은 values 만 사용 → 날짜 무관)을 ARDS px 와 병합. 겹치는 티커는 ARDS 우선(골든 보존).
  const amqsPx: Record<string, DSeries> = {};
  for (const t of AI_INFRA_TICKERS) if (amqsG.prices[t]) amqsPx[t] = { dates: [], values: amqsG.prices[t] };
  amqsPx["QQQ"] = { dates: [], values: amqsG.qqq };
  amqsPx["^VIX"] = { dates: [], values: amqsG.vix };
  const px: Record<string, DSeries> = { ...amqsPx, ...(ardsG.px as Record<string, DSeries>) };
  const fred = ardsG.fred as Record<string, DSeries>;

  const res = computeSignals(px, fred, freshState(), "2026-06-06");

  it("ARDS 행: QQQ + 골든 verdict 매핑(REDUCE→SELL) + confidence + 상태", () => {
    const ards = res.rows.find((r) => r.strategy === "ARDS");
    expect(ards).toBeTruthy();
    expect(ards!.ticker).toBe("QQQ");
    expect(ards!.signal).toBe("SELL"); // action REDUCE → SELL
    expect(ards!.score).toBe(ardsG.verdict.confidence);
    expect(JSON.parse(ards!.detail_json).state).toBe(ardsG.verdict.state);
    expect(res.payload.ards.verdict.state).toBe(ardsG.verdict.state);
  });

  it("히스테리시스 상태: 최초 실행 → committed=raw", () => {
    expect(res.newState.committed).toBe(ardsG.raw);
  });

  it("AMQS 행: 다수 생성 + 유효 enum + 레짐 포함", () => {
    const amqs = res.rows.filter((r) => r.strategy === "AMQS");
    expect(amqs.length).toBeGreaterThan(0);
    for (const r of amqs) {
      expect(["BUY", "SELL", "HOLD"]).toContain(r.signal);
      expect(JSON.parse(r.detail_json).regime).toBe(res.payload.amqs.regime.label);
    }
  });

  it("워치리스트(#4): 빅테크+AI 종목 매수/매도 + 그룹 + 한글명", () => {
    const wl = res.payload.watchlist;
    expect(wl.length).toBeGreaterThan(0);
    for (const w of wl) {
      expect(["BUY", "SELL", "HOLD"]).toContain(w.signal);
      expect(["bigtech", "ai_semi", "ai_infra", "nasdaq"]).toContain(w.group);
      expect(typeof w.ko).toBe("string");
    }
    // D1 WATCHLIST 행도 생성
    expect(res.rows.some((r) => r.strategy === "WATCHLIST")).toBe(true);
    // 빅테크(예: AAPL) 포함
    expect(wl.some((w) => w.group === "bigtech")).toBe(true);
  });
});

function fakeR2(): R2Like & { _map: Map<string, string> } {
  const m = new Map<string, string>();
  return {
    _map: m,
    async get(k: string) {
      return m.has(k) ? { text: async () => m.get(k) as string } : null;
    },
    async put(k: string, v: string) {
      m.set(k, v);
    },
  };
}

describe("cache (R2) — 저장/조회 + 폴백", () => {
  it("putSeries → getSeries 라운드트립", async () => {
    const r2 = fakeR2();
    await putSeries(r2, "prices", "^GSPC", { dates: ["2026-01-01"], values: [5000] });
    expect(await getSeries(r2, "prices", "^GSPC")).toEqual({ dates: ["2026-01-01"], values: [5000] });
    expect(await getSeries(r2, "prices", "MISSING")).toBeNull();
  });

  it("reconcile: 성공분은 캐시 저장+사용, 실패분은 캐시 폴백, 둘다없으면 missing", async () => {
    const r2 = fakeR2();
    // 사전: AAPL 직전 저장본 존재 (이번엔 fetch 실패한다고 가정)
    await putSeries(r2, "prices", "AAPL", { dates: ["2026-01-01"], values: [190] });

    const fetched = { NVDA: { dates: ["2026-06-06"], values: [1000] } }; // AAPL/TSLA 는 실패
    const res = await reconcileWithCache(r2, "prices", ["NVDA", "AAPL", "TSLA"], fetched);

    expect(res.data.NVDA.values).toEqual([1000]); // fetch 성공
    expect(res.data.AAPL.values).toEqual([190]); // 캐시 폴백
    expect(res.fromCache).toEqual(["AAPL"]);
    expect(res.missing).toEqual(["TSLA"]); // fetch·캐시 모두 없음
    // NVDA 는 캐시에 새로 저장됨
    expect(await getSeries(r2, "prices", "NVDA")).toEqual({ dates: ["2026-06-06"], values: [1000] });
  });
});

describe("persistSignals — D1 upsert", () => {
  it("행마다 signals upsert 를 batch 로 실행", async () => {
    const calls: { sql: string; args: unknown[] }[] = [];
    const db = {
      prepare(sql: string) {
        return { bind: (...args: unknown[]) => ({ run: async () => {}, sql, args }) };
      },
      async batch(stmts: unknown[]) {
        for (const s of stmts as Array<{ sql: string; args: unknown[] }>) calls.push({ sql: s.sql, args: s.args });
      },
    };
    await persistSignals(db, [
      { date: "2026-06-06", strategy: "ARDS", ticker: "QQQ", signal: "SELL", score: 55, detail_json: "{}" },
      { date: "2026-06-06", strategy: "AMQS", ticker: "NVDA", signal: "BUY", score: 82.1, detail_json: "{}" },
    ]);
    expect(calls.length).toBe(2);
    expect(calls[0].sql).toContain("INSERT INTO signals");
    expect(calls[0].sql).toContain("ON CONFLICT(date, strategy, ticker)");
    expect(calls[1].args).toEqual(["2026-06-06", "AMQS", "NVDA", "BUY", 82.1, "{}"]);
  });
});
