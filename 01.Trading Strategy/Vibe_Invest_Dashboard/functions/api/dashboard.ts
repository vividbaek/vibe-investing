import { jsonResponse } from "../../shared/http";

/**
 * GET /api/dashboard — 크론이 미리 만든 R2 signals/latest.json 을 그대로 서빙.
 * origin 연산 0 (읽기만) + CDN 엣지 캐시(s-maxage=60). 없으면 data:null(프론트 스켈레톤/stale).
 */
interface Env {
  SNAPSHOTS: R2Bucket;
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const obj = await ctx.env.SNAPSHOTS.get("signals/latest.json");
  if (!obj) return jsonResponse(null, { cacheSeconds: 30 });
  let payload: { updated_at?: string | null } | null;
  try {
    payload = JSON.parse(await obj.text());
  } catch {
    return jsonResponse(null, { cacheSeconds: 30 });
  }
  return jsonResponse(payload, { updatedAt: payload?.updated_at ?? null, cacheSeconds: 60 });
};
