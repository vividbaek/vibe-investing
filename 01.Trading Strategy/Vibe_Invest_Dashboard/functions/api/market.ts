import { jsonResponse } from "../../shared/http";

/**
 * GET /api/market — 10분 크론이 만든 R2 market-latest.json 서빙(지수·섹터·VIX·급등락·리스크게이지).
 * 읽기만 + CDN 엣지 캐시(s-maxage=120). 없으면 data:null(프론트 스켈레톤/stale).
 */
interface Env {
  SNAPSHOTS: R2Bucket;
}

export const onRequestGet: PagesFunction<Env> = async (ctx) => {
  const obj = await ctx.env.SNAPSHOTS.get("market-latest.json");
  if (!obj) return jsonResponse(null, { cacheSeconds: 30 });
  let snap: { ts?: string } | null;
  try {
    snap = JSON.parse(await obj.text());
  } catch {
    return jsonResponse(null, { cacheSeconds: 30 });
  }
  return jsonResponse(snap, { updatedAt: snap?.ts ?? null, cacheSeconds: 120 });
};
