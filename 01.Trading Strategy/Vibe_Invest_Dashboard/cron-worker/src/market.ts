/**
 * 10분 크론: 시세/섹터/급등락 스냅샷 → R2 market-latest.json + D1 movers + stats_cache.
 * 데이터: Yahoo (키 불필요) — chart meta(현재가·전일종가) + 사전정의 스크리너(급등/급락).
 * 무료 한도 절약: 미 장외 시간엔 조기 return.
 */
import { fetchQuote, fetchScreener, type Quote, type ScreenerRow } from "./providers/yahoo";
import { pyRound } from "../../shared/strategy/series";
import { SYM_BY_TICKER } from "../../shared/symbols";
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

// 한국인 선호 US ETF (표시용, #3). 10분 subrequest 한도 고려해 핵심만.
const ETF_DISPLAY = ["QQQ", "TQQQ", "SOXL", "SCHD", "JEPI", "JEPQ", "SMH", "SOXX", "NVDL", "TSLL"];

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
  etfs: Tile[];
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

/** 순수 조립: quote 맵 → 지수/섹터/ETF/VIX/리스크 스냅샷 (intraday, movers 제외). */
export function buildMarketSnapshot(quotes: Record<string, Quote>, ts: string): MarketSnapshot {
  const tile = (sym: string, name: string): Tile | null => {
    const q = quotes[sym];
    if (!q) return null;
    return { ticker: sym, name, price: pyRound(q.price, 2), chg_pct: pyRound(q.chgPct, 2) };
  };

  const indices = INDEX_SYMBOLS.map((s) => tile(s, INDEX_NAMES[s])).filter((t): t is Tile => t !== null);
  const sectors = SECTOR_SYMBOLS.map((s) => tile(s, SECTOR_NAMES[s])).filter((t): t is Tile => t !== null);
  const etfs = ETF_DISPLAY.map((s) => tile(s, SYM_BY_TICKER[s]?.ko ?? s)).filter((t): t is Tile => t !== null);
  const vix = quotes[VIX_SYMBOL] ? pyRound(quotes[VIX_SYMBOL].price, 1) : null;

  const sectorsUp = sectors.filter((s) => s.chg_pct > 0).length;
  const sectorsDown = sectors.filter((s) => s.chg_pct < 0).length;

  // 리스크 게이지(heuristic 0~100): 지수등락 + VIX + 섹터폭
  const avgIdxChg = indices.length ? indices.reduce((a, t) => a + t.chg_pct, 0) / indices.length : 0;
  const upRatio = sectors.length ? sectorsUp / sectors.length : 0.5;
  let score = 50 + clamp(avgIdxChg * 6, -25, 25) - clamp(((vix ?? 18) - 18) * 1.0, -15, 25) + (upRatio - 0.5) * 20;
  score = pyRound(clamp(score, 0, 100), 0);
  const risk_label = score < 40 ? "RISK_OFF" : score > 60 ? "RISK_ON" : "NEUTRAL";

  return { ts, indices, vix, sectors, etfs, breadth: { sectors_up: sectorsUp, sectors_down: sectorsDown }, risk_score: score, risk_label };
}

/** 10분 크론: 지수/섹터/ETF/VIX 시세 → R2 스냅샷 + stats_cache.last_update. (movers 제외 — 장종료 후 별도) */
export async function runMarketSnapshot(
  env: MarketEnv,
  now: Date = new Date(),
): Promise<{ skipped: boolean; reason?: string; risk?: number }> {
  if (!isUsMarketWindowUtc(now)) return { skipped: true, reason: "off-hours" };

  const ts = now.toISOString();
  const quotes: Record<string, Quote> = {};
  for (const sym of [...INDEX_SYMBOLS, VIX_SYMBOL, ...SECTOR_SYMBOLS, ...ETF_DISPLAY]) {
    try {
      quotes[sym] = await fetchQuote(sym);
    } catch {
      // 부분 성공 허용
    }
  }

  const snapshot = buildMarketSnapshot(quotes, ts);
  await env.SNAPSHOTS.put(SNAPSHOT_KEY, JSON.stringify(snapshot), {
    httpMetadata: { contentType: "application/json", cacheControl: "public, s-maxage=300" },
  });
  await env.DB.prepare(
    `INSERT INTO stats_cache (key, value, ts) VALUES ('last_update', ?, ?)
     ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts`,
  )
    .bind(ts, ts)
    .run();

  return { skipped: false, risk: snapshot.risk_score };
}

// ===========================================================================
// 급등/급락 (movers) — 장 종료 후 1회만 갱신·캐시. 휴장이면 직전값 유지(빈 응답 스킵).
// ===========================================================================
const MOVERS_KEY = "movers-latest.json";
type MoverRow = [string, string, number, string, string, number, number, number];

/** 순수 조립: 스크리너 → mover 리스트 + D1 행. */
export function buildMovers(
  gainers: ScreenerRow[],
  losers: ScreenerRow[],
  ts: string,
): { gainers: Mover[]; losers: Mover[]; rows: MoverRow[] } {
  const g = toMovers(gainers);
  const l = toMovers(losers);
  const rows: MoverRow[] = [
    ...g.map((m) => [ts, "gainer", m.rank, m.ticker, m.name, m.price, m.chg_pct, m.volume] as MoverRow),
    ...l.map((m) => [ts, "loser", m.rank, m.ticker, m.name, m.price, m.chg_pct, m.volume] as MoverRow),
  ];
  return { gainers: g, losers: l, rows };
}

async function persistMovers(db: D1Like, rows: MoverRow[]): Promise<void> {
  const stmt = db.prepare(
    `INSERT INTO movers (ts, direction, rank, ticker, name, price, chg_pct, volume)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(ts, direction, rank) DO UPDATE SET
       ticker=excluded.ticker, name=excluded.name, price=excluded.price, chg_pct=excluded.chg_pct, volume=excluded.volume`,
  );
  await db.batch(rows.map((r) => stmt.bind(...r)));
}

/**
 * 장 종료 후 1회: 나스닥 급등/급락 Top10 → D1 movers + R2 movers-latest.json.
 * 스크리너가 비면(휴장 등) 스킵 → 직전값 유지.
 */
export async function runMoversSnapshot(
  env: MarketEnv,
  now: Date = new Date(),
): Promise<{ skipped: boolean; reason?: string; gainers?: number; losers?: number }> {
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
  if (gainers.length === 0 && losers.length === 0) {
    return { skipped: true, reason: "no_data (휴장/실패 — 직전값 유지)" };
  }

  const ts = now.toISOString();
  const built = buildMovers(gainers, losers, ts);
  await env.SNAPSHOTS.put(
    MOVERS_KEY,
    JSON.stringify({ ts, gainers: built.gainers, losers: built.losers }),
    { httpMetadata: { contentType: "application/json", cacheControl: "public, s-maxage=1800" } },
  );
  await persistMovers(env.DB, built.rows);
  return { skipped: false, gainers: built.gainers.length, losers: built.losers.length };
}
