import { jsonResponse } from "../../shared/http";
import { sha256Hex } from "../../shared/hash";

/**
 * POST /api/track — DAU/누적 AU 기록 후 {dau, total_au} 반환.
 * user_hash = SHA-256(IP + UA + [date] + salt). 원본 IP 미저장. no-store.
 */
interface Env {
  DB: D1Database;
  USER_HASH_SALT?: string;
}

export const onRequestPost: PagesFunction<Env> = async (ctx) => {
  const now = new Date();
  const today = now.toISOString().slice(0, 10);
  const ip = ctx.request.headers.get("cf-connecting-ip") ?? "0.0.0.0";
  const ua = ctx.request.headers.get("user-agent") ?? "";
  const salt = ctx.env.USER_HASH_SALT ?? "";

  const dayHash = await sha256Hex(`${ip}|${ua}|${today}|${salt}`);
  const allHash = await sha256Hex(`${ip}|${ua}|${salt}`);

  await ctx.env.DB.batch([
    ctx.env.DB.prepare(`INSERT OR IGNORE INTO daily_users (date, user_hash) VALUES (?, ?)`).bind(today, dayHash),
    ctx.env.DB.prepare(`INSERT OR IGNORE INTO all_users (user_hash, first_seen) VALUES (?, ?)`).bind(
      allHash,
      now.toISOString(),
    ),
  ]);

  const dau = await ctx.env.DB.prepare(`SELECT COUNT(*) AS c FROM daily_users WHERE date = ?`)
    .bind(today)
    .first<{ c: number }>();
  const total = await ctx.env.DB.prepare(`SELECT COUNT(*) AS c FROM all_users`).first<{ c: number }>();

  return jsonResponse({ dau: dau?.c ?? 0, total_au: total?.c ?? 0 });
};
