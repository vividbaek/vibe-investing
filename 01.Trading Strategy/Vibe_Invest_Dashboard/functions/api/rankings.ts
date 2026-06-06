import { jsonResponse } from "../../shared/http";

/**
 * GET /api/rankings — 검색 Top 5 (rankings 캐시 테이블). 최신 집계일 기준. CDN 캐시 300s.
 */
interface Env {
  DB: D1Database;
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const latest = await ctx.env.DB.prepare(`SELECT date FROM rankings ORDER BY date DESC LIMIT 1`).first<{
    date: string;
  }>();
  if (!latest) return jsonResponse({ date: null, top: [] }, { cacheSeconds: 300 });

  const rows = await ctx.env.DB.prepare(
    `SELECT rank, ticker, search_count FROM rankings WHERE date = ? ORDER BY rank LIMIT 5`,
  )
    .bind(latest.date)
    .all();
  return jsonResponse({ date: latest.date, top: rows.results ?? [] }, { updatedAt: latest.date, cacheSeconds: 300 });
};
