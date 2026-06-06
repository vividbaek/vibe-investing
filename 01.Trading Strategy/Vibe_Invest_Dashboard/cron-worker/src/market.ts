/**
 * 10분 크론: 시세/섹터/급등락 스냅샷 → R2 market-latest.json + D1 movers + stats_cache.
 * 데이터: Yahoo (키 불필요) — chart meta(현재가·전일종가) + 사전정의 스크리너(급등/급락).
 * 무료 한도 절약: 미 장외 시간엔 조기 return.
 */
import { fetchQuote, fetchScreener, type Quote, type ScreenerRow } from "./providers/yahoo";
import { pyRound } from "../../shared/strategy/series";
import type { D1Like } from "../../shared/ingest";

export interface MarketEnv {
  DB: D1Database;
  SNAPSHOTS: R2Bucket;
}

// 지수 프록시 ETF + VIX
const INDEX_NAMES: Record<string, string> = { SPY: "S&P 500", QQQ: "나스닥100", DIA: "다우", IWM: "러셀2000" };
const INDEX_SYMBOLS = Object.keys(INDEX_NAMES);
const VIX_SYMBOL = "^VIX";

// 11 SPDR 섹터 ETF
const SECTOR_NAMES: Record<string, string> = {
  XLK: "기술",
  XLF: "금융",
  XLV: "헬스케어",
  XLE: "에너지",
  XLI: "산업재",
  XLY: "경기소비재",
  XLP: "필수소비재",
  XLU: "유틸리티",
  XLB: "소재",
  XLRE: "리츠",
  XLC: "커뮤니케이션",
};
const SECTOR_SYMBOLS = Object.keys(SECTOR_NAMES);

const SNAPSHOT_KEY = "market-latest.json";

export interface Tile {
  ticker: string;
  name: string;
  price: number;
  chg_pct: number;
}
export interface Mover {
  rank: number;
  ticker: string;
  name: string;
  price: number;
  chg_pct: number;
  volume: number;
}
export interface MarketSnapshot {
  ts: string;
  indices: Tile[];
  vix: number | null;
  sectors: Tile[];
  movers: { gainers: Mover[]; losers: Mover[] };
  breadth: { sectors_up: number; sectors_down: number };
  risk_score: number; // 0~100 (heuristic)
  risk_label: "RISK_OFF" | "NEUTRAL" | "RISK_ON";
}

function clamp(x: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, x));
}

/** 미 장 프리장~마감 대략 창: UTC 13:00–21:30. 밖이면 수집 스킵. */
export function isUsMarketWindowUtc(d: Date): boolean {
  const mins = d.getUTCHours() * 60 + d.getUTCMinutes();
  return mins >= 13 * 60 && mins <= 21 * 60 + 30;
}

function toMovers(rows: ScreenerRow[], limit = 10): Mover[] {
  return rows.slice(0, limit).map((r, i) => ({
    rank: i + 1,
    ticker: r.ticker,
    name: r.name,
    price: pyRound(r.price, 2),
    chg_pct: pyRound(r.chgPct, 2),
    volume: Math.round(r.volume),
  }));
}

/** 순수 조립: quote 맵 + 스크리너 → 스냅샷 + D1 mover 행. */
export function buildMarketSnapshot(
  quotes: Record<string, Quote>,
  gainers: ScreenerRow[],
  losers: ScreenerRow[],
  ts: string,
): { snapshot: MarketSnapshot; moverRows: Array<[string, string, number, string, string, number, number, number]> } {
  const tile = (sym: string, name: string): Tile | null => {
    const q = quotes[sym];
    if (!q) return null;
    return { ticker: sym, name, price: pyRound(q.price, 2), chg_pct: pyRound(q.chgPct, 2) };
  };

  const indices = INDEX_SYMBOLS.map((s) => tile(s, INDEX_NAMES[s])).filter((t): t is Tile => t !== null);
  const sectors = SECTOR_SYMBOLS.map((s) => tile(s, SECTOR_NAMES[s])).filter((t): t is Tile => t !== null);
  const vix = quotes[VIX_SYMBOL] ? pyRound(quotes[VIX_SYMBOL].price, 1) : null;

  const sectorsUp = sectors.filter((s) => s.chg_pct > 0).length;
  const sectorsDown = sectors.filter((s) => s.chg_pct < 0).length;

  // 리스크 게이지(heuristic 0~100): 지수등락 + VIX + 섹터폭
  const avgIdxChg = indices.length ? indices.reduce((a, t) => a + t.chg_pct, 0) / indices.length : 0;
  const upRatio = sectors.length ? sectorsUp / sectors.length : 0.5;
  let score = 50 + clamp(avgIdxChg * 6, -25, 25) - clamp(((vix ?? 18) - 18) * 1.0, -15, 25) + (upRatio - 0.5) * 20;
  score = pyRound(clamp(score, 0, 100), 0);
  const risk_label = score < 40 ? "RISK_OFF" : score > 60 ? "RISK_ON" : "NEUTRAL";

  const gMovers = toMovers(gainers);
  const lMovers = toMovers(losers);

  const snapshot: MarketSnapshot = {
    ts,
    indices,
    vix,
    sectors,
    movers: { gainers: gMovers, losers: lMovers },
    breadth: { sectors_up: sectorsUp, sectors_down: sectorsDown },
    risk_score: score,
    risk_label,
  };

  // D1 movers 행: [ts, direction, rank, ticker, name, price, chg_pct, volume]
  const moverRows: Array<[string, string, number, string, string, number, number, number]> = [
    ...gMovers.map((m) => [ts, "gainer", m.rank, m.ticker, m.name, m.price, m.chg_pct, m.volume] as [string, string, number, string, string, number, number, number]),
    ...lMovers.map((m) => [ts, "loser", m.rank, m.ticker, m.name, m.price, m.chg_pct, m.volume] as [string, string, number, string, string, number, number, number]),
  ];

  return { snapshot, moverRows };
}

async function persistMarket(db: D1Like, snapshot: MarketSnapshot, moverRows: ReturnType<typeof buildMarketSnapshot>["moverRows"]): Promise<void> {
  const moverStmt = db.prepare(
    `INSERT INTO movers (ts, direction, rank, ticker, name, price, chg_pct, volume)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(ts, direction, rank) DO UPDATE SET
       ticker=excluded.ticker, name=excluded.name, price=excluded.price, chg_pct=excluded.chg_pct, volume=excluded.volume`,
  );
  const statements = moverRows.map((r) => moverStmt.bind(...r));
  statements.push(
    db
      .prepare(
        `INSERT INTO stats_cache (key, value, ts) VALUES ('last_update', ?, ?)
         ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts`,
      )
      .bind(snapshot.ts, snapshot.ts),
  );
  if (statements.length) await db.batch(statements);
}

export async function runMarketSnapshot(
  env: MarketEnv,
  now: Date = new Date(),
): Promise<{ skipped: boolean; reason?: string; risk?: number; gainers?: number; losers?: number }> {
  if (!isUsMarketWindowUtc(now)) return { skipped: true, reason: "off-hours" };

  const ts = now.toISOString();
  const quotes: Record<string, Quote> = {};
  for (const sym of [...INDEX_SYMBOLS, VIX_SYMBOL, ...SECTOR_SYMBOLS]) {
    try {
      quotes[sym] = await fetchQuote(sym);
    } catch {
      // 부분 성공 허용
    }
  }
  let gainers: ScreenerRow[] = [];
  let losers: ScreenerRow[] = [];
  try {
    gainers = await fetchScreener("day_gainers", 10);
  } catch {
    /* 비움 */
  }
  try {
    losers = await fetchScreener("day_losers", 10);
  } catch {
    /* 비움 */
  }

  const { snapshot, moverRows } = buildMarketSnapshot(quotes, gainers, losers, ts);
  await env.SNAPSHOTS.put(SNAPSHOT_KEY, JSON.stringify(snapshot), {
    httpMetadata: { contentType: "application/json", cacheControl: "public, s-maxage=300" },
  });
  await persistMarket(env.DB, snapshot, moverRows);

  return { skipped: false, risk: snapshot.risk_score, gainers: snapshot.movers.gainers.length, losers: snapshot.movers.losers.length };
}
