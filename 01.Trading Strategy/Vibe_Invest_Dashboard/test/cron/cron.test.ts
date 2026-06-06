import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { parseYahooChart } from "../../cron-worker/src/providers/yahoo";
import { parseFredCsv } from "../../cron-worker/src/providers/fred";
import { computeSignals } from "../../cron-worker/src/signals";
import { persistSignals } from "../../cron-worker/src/daily";
import { isUsMarketWindowUtc } from "../../cron-worker/src/market";
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
