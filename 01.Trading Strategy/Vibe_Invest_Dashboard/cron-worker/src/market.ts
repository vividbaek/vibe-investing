/**
 * 10분 크론: 시세/섹터/급등락 스냅샷 → R2 + D1 (프론트 폴링용).
 *
 * 현재: 장외시간 스킵 + 키 가드만 구현. Finnhub/FMP 호출은 키 확보 후 채운다(#9b).
 * (무료 한도 절약: 미 장외 시간엔 조기 return 으로 API 호출 안 함.)
 */
export interface MarketEnv {
  DB: D1Database;
  SNAPSHOTS: R2Bucket;
  FINNHUB_KEY?: string;
  FMP_KEY?: string;
}

/** 미 장 프리장~마감 대략 창: UTC 13:00–21:30 (서머타임 기준). 밖이면 수집 스킵. */
export function isUsMarketWindowUtc(d: Date): boolean {
  const mins = d.getUTCHours() * 60 + d.getUTCMinutes();
  return mins >= 13 * 60 && mins <= 21 * 60 + 30;
}

export async function runMarketSnapshot(
  env: MarketEnv,
  now: Date = new Date(),
): Promise<{ skipped: boolean; reason?: string }> {
  if (!isUsMarketWindowUtc(now)) return { skipped: true, reason: "off-hours" };
  if (!env.FINNHUB_KEY) return { skipped: true, reason: "no FINNHUB_KEY" };
  // TODO(#9b): Finnhub 지수(SPY/QQQ/DIA/IWM 프록시)+VIX+섹터 ETF11 + 급등/급락 Top10
  //   → R2 snapshots/market-latest.json (+ 히스토리) + D1 market_snapshot/movers upsert
  //   → stats_cache.last_update 갱신.
  return { skipped: true, reason: "not_implemented" };
}
