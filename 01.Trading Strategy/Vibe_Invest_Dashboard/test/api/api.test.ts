import { describe, it, expect } from "vitest";
import { createHash } from "node:crypto";
import { sha256Hex } from "../../shared/hash";
import { onRequestGet as dashboardGet } from "../../functions/api/dashboard";

// D1 백엔드 엔드포인트(news/movers/rankings/search/track)는 wrangler pages dev + 로컬 D1 로
// 엔드투엔드 검증함(README 참고). 여기선 순수 로직(해시)·R2 서빙(dashboard)을 회귀 고정.

describe("shared/hash sha256Hex", () => {
  it("Node crypto 와 동일", async () => {
    const mine = await sha256Hex("1.2.3.4|ua|2026-06-06|salt");
    const node = createHash("sha256").update("1.2.3.4|ua|2026-06-06|salt").digest("hex");
    expect(mine).toBe(node);
    expect(mine).toMatch(/^[0-9a-f]{64}$/);
  });
});

function ctxWith(snapshot: string | null, url = "https://x/api/dashboard") {
  const env = {
    SNAPSHOTS: {
      async get(key: string) {
        return key === "signals/latest.json" && snapshot !== null ? { text: async () => snapshot } : null;
      },
    },
  };
  return { env, request: new Request(url) } as unknown as Parameters<typeof dashboardGet>[0];
}

describe("GET /api/dashboard — R2 스냅샷 서빙", () => {
  it("스냅샷 있으면 data+updated_at+s-maxage=60", async () => {
    const snap = JSON.stringify({ updated_at: "2026-06-06T21:00:00Z", ards: { verdict: { state: "CORRECTION" } } });
    const res = await dashboardGet(ctxWith(snap));
    expect(res.status).toBe(200);
    const body = (await res.json()) as { data: { ards: { verdict: { state: string } } }; updated_at: string };
    expect(body.data.ards.verdict.state).toBe("CORRECTION");
    expect(body.updated_at).toBe("2026-06-06T21:00:00Z");
    expect(res.headers.get("cache-control")).toContain("s-maxage=60");
  });
  it("스냅샷 없으면 data:null", async () => {
    const res = await dashboardGet(ctxWith(null));
    const body = (await res.json()) as { data: unknown };
    expect(body.data).toBeNull();
  });
  it("깨진 JSON 이면 data:null (throw 안 함)", async () => {
    const res = await dashboardGet(ctxWith("not json"));
    expect(res.status).toBe(200);
    expect(((await res.json()) as { data: unknown }).data).toBeNull();
  });
});
