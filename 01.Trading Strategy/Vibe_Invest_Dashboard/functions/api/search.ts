import { jsonResponse } from "../../shared/http";
import { sha256Hex } from "../../shared/hash";

/**
 * GET /api/search?q=NVDA — 해당 종목의 최신 전략 시그널 + 검색 로그 기록(D1 write).
 * 쓰기가 있으므로 no-store. user_hash 는 익명 해시(원본 IP 미저장).
 */
interface Env {
  DB: D1Database;
  USER_HASH_SALT?: string;
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const url = new URL(ctx.request.url);
  const q = (url.searchParams.get("q") ?? "").trim().toUpperCase();
  if (!q || q.length > 12 || !/^[A-Z0-9.^-]+$/.test(q)) {
    return jsonResponse({ error: "invalid_query" }, { status: 400 });
  }

  const signals = await ctx.env.DB.prepare(
    `SELECT strategy, ticker, signal, score, detail_json, date
     FROM signals WHERE ticker = ? ORDER BY date DESC LIMIT 6`,
  )
    .bind(q)
    .all();

  // 검색 로그 (익명)
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const ip = ctx.request.headers.get("cf-connecting-ip") ?? "0.0.0.0";
  const ua = ctx.request.headers.get("user-agent") ?? "";
  const userHash = await sha256Hex(`${ip}|${ua}|${today}|${ctx.env.USER_HASH_SALT ?? ""}`);
  try {
    await ctx.env.DB.prepare(`INSERT INTO searches (ts, date, ticker, user_hash) VALUES (?, ?, ?, ?)`)
      .bind(now.toISOString(), today, q, userHash)
      .run();
  } catch {
    // 로그 실패는 검색 응답을 막지 않음
  }

  return jsonResponse({ ticker: q, signals: signals.results ?? [] });
};
