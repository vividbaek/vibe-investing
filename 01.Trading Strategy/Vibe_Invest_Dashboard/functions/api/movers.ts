import { jsonResponse } from "../../shared/http";

/**
 * GET /api/movers — D1 movers 최신 ts 의 급등/급락. CDN 캐시 300s.
 */
interface Env {
  DB: D1Database;
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const latest = await ctx.env.DB.prepare(`SELECT ts FROM movers ORDER BY ts DESC LIMIT 1`).first<{ ts: string }>();
  if (!latest) return jsonResponse({ ts: null, gainers: [], losers: [] }, { cacheSeconds: 300 });

  const rows = await ctx.env.DB.prepare(
    `SELECT direction, rank, ticker, name, price, chg_pct, volume
     FROM movers WHERE ts = ? ORDER BY direction, rank`,
  )
    .bind(latest.ts)
    .all();
  const all = (rows.results ?? []) as Array<Record<string, unknown>>;
  return jsonResponse(
    {
      ts: latest.ts,
      gainers: all.filter((r) => r.direction === "gainer"),
      losers: all.filter((r) => r.direction === "loser"),
    },
    { updatedAt: latest.ts, cacheSeconds: 300 },
  );
};
