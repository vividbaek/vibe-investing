/**
 * FRED 무료 CSV provider (키 불필요): https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>
 * ARDS 거시축(침체 Composite)·금리축(DGS2/T5YIE)용.
 *
 * best-effort: FRED 가 막히거나 빈 응답이면 해당 시리즈를 누락시키고, ARDS 엔진이
 * 시장 프록시(yfinance px)로 자동 폴백한다(macro.ts/rates.ts 의 proxy 경로).
 */
import type { DSeries } from "../../../shared/strategy/ards/dseries";

/**
 * FRED CSV 파싱. 헤더 'DATE,VALUE'(또는 'observation_date,...'),
 * 결측은 '.' 로 표기됨 → 제거. → DSeries(dropna 상태).
 */
export function parseFredCsv(text: string): DSeries {
  const dates: string[] = [];
  const values: number[] = [];
  const lines = text.trim().split(/\r?\n/);
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const comma = line.indexOf(",");
    if (comma < 0) continue;
    const date = line.slice(0, comma).trim();
    const raw = line.slice(comma + 1).trim();
    if (raw === "." || raw === "") continue; // FRED 결측
    const v = Number(raw);
    if (Number.isNaN(v)) continue;
    dates.push(date);
    values.push(v);
  }
  return { dates, values };
}

const FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=";

export async function fetchFred(seriesId: string): Promise<DSeries> {
  const res = await fetch(`${FRED_BASE}${encodeURIComponent(seriesId)}`, {
    headers: { "User-Agent": "Mozilla/5.0", Accept: "text/csv" },
  });
  if (!res.ok) throw new Error(`fred ${seriesId}: HTTP ${res.status}`);
  return parseFredCsv(await res.text());
}

/** 여러 FRED 시리즈 best-effort 수집. 실패/빈 응답은 누락(엔진이 프록시 폴백). */
export async function fetchFredMany(
  ids: string[],
): Promise<{ data: Record<string, DSeries>; failures: Record<string, string> }> {
  const data: Record<string, DSeries> = {};
  const failures: Record<string, string> = {};
  for (const id of ids) {
    try {
      const ds = await fetchFred(id);
      if (ds.values.length > 0) data[id] = ds;
      else failures[id] = "empty";
    } catch (e) {
      failures[id] = String(e);
    }
  }
  return { data, failures };
}
