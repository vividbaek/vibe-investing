import { jsonResponse } from "../../shared/http";

/**
 * GET /api/news?limit=10 — D1 news_summary 최신 N + market_summary. CDN 캐시 300s.
 */
interface Env {
  DB: D1Database;
}

function safeParse(s: unknown): unknown[] {
  if (typeof s !== "string") return [];
  try {
    const v = JSON.parse(s);
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const url = new URL(ctx.request.url);
  const limit = Math.min(50, Math.max(1, Number(url.searchParams.get("limit") ?? "10") || 10));

  const itemsRes = await ctx.env.DB.prepare(
    `SELECT id, ts, title_ko, summary_ko, category, tickers_json, source, url
     FROM news_summary ORDER BY ts DESC LIMIT ?`,
  )
    .bind(limit)
    .all();
  const market = await ctx.env.DB.prepare(`SELECT ts, summary_ko FROM market_summary WHERE id = 1`).first<{
    ts: string;
    summary_ko: string;
  }>();

  const items = (itemsRes.results ?? []).map((r) => {
    const row = r as Record<string, unknown>;
    return {
      id: row.id,
      ts: row.ts,
      title_ko: row.title_ko,
      summary_ko: row.summary_ko,
      category: row.category,
      tickers: safeParse(row.tickers_json),
      source: row.source,
      url: row.url,
    };
  });

  return jsonResponse({ market_summary: market ?? null, items }, { updatedAt: market?.ts ?? null, cacheSeconds: 300 });
};
