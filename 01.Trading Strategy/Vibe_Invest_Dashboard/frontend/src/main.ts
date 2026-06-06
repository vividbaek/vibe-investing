/**
 * Vibe Investing — 대시보드 프론트엔드 (vanilla TS).
 * /api/* (크론이 선계산한 R2/D1) 를 읽어 렌더. 차트는 경량 SVG 직접 렌더.
 * 등락색 한국식(적=상승, 청=하락). 빈 화면 금지(스켈레톤/stale).
 */
import "./styles.css";
import { searchSymbols, SYM_BY_TICKER } from "../../shared/symbols";
import { FEATURES } from "./features";

// ---------------------------------------------------------------------------
// 유틸
// ---------------------------------------------------------------------------
const $ = (id: string) => document.getElementById(id)!;
const esc = (s: unknown): string =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
const pctCls = (p: number): string => (p > 0 ? "up" : p < 0 ? "down" : "");
const fmtPct = (p: number | null | undefined): string =>
  p === null || p === undefined || Number.isNaN(p) ? "—" : `${p > 0 ? "+" : ""}${p.toFixed(2)}%`;
const fmtNum = (n: number | null | undefined, d = 2): string =>
  n === null || n === undefined || Number.isNaN(n) ? "—" : n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

interface Envelope<T> {
  data: T;
  updated_at: string | null;
}
async function getJSON<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
  const r = await fetch(path, init);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return (await r.json()) as Envelope<T>;
}

// ---------------------------------------------------------------------------
// i18n (섹션 제목 위주, 뉴스는 KO 고정)
// ---------------------------------------------------------------------------
const I18N: Record<string, Record<string, string>> = {
  ko: { market: "시장 상황", etf: "인기 ETF", watch: "주요 종목 — 빅테크 · AI · AI 인프라", gainers: "나스닥 급등 TOP 10", losers: "나스닥 급락 TOP 10", news: "주요 경제 뉴스 요약", rankings: "인기 검색 TOP 5", stats: "사이트 통계" },
  en: { market: "Market", etf: "Popular ETFs", watch: "Watchlist — Big Tech · AI · AI Infra", gainers: "Top Gainers", losers: "Top Losers", news: "Market News", rankings: "Top Searches", stats: "Site Stats" },
};
let lang: "ko" | "en" = "ko";
function applyLang() {
  document.documentElement.lang = lang;
  document.querySelectorAll<HTMLElement>("[data-i18n]").forEach((node) => {
    const k = node.dataset.i18n!;
    if (I18N[lang][k]) node.textContent = I18N[lang][k];
  });
  $("lang").textContent = lang.toUpperCase();
}

// ---------------------------------------------------------------------------
// 시그널 배지
// ---------------------------------------------------------------------------
const SIG_LABEL: Record<string, string> = { BUY: "매수", SELL: "매도", HOLD: "보유", SHORT_TERM_RISK: "단기하락 주의", SURGE: "급등" };
const SIG_ICON: Record<string, string> = { SHORT_TERM_RISK: "⚠ ", SURGE: "▲ " };
function badge(sig: string, dateStr?: string): string {
  const d = dateStr ? `<span class="d">· ${esc(dateStr)}</span>` : "";
  return `<span class="badge b-${sig}">${SIG_ICON[sig] ?? ""}${SIG_LABEL[sig] ?? sig}${d}</span>`;
}
// AMQS 티어 → 대시보드 배지 (STRATEGY-ANALYSIS §2.5)
const AMQS_MAP: Record<string, string | null> = { DIP_BUY: "BUY", CENTER: "BUY", SATELLITE: "HOLD", TACTICAL: "HOLD", REDUCE: "SELL", EXIT: "SELL", EXCLUDED: null, HOLD: null };
// ARDS action → 배지
const ARDS_MAP: Record<string, string> = { RISK_ON: "BUY", BUY_DIP_TACTICAL: "BUY", HOLD_ACCUMULATE: "HOLD", REDUCE: "SELL", DEFENSIVE_ARDS: "SELL" };

// ---------------------------------------------------------------------------
// SVG: 리스크 게이지 (반원)
// ---------------------------------------------------------------------------
function gaugeSvg(score: number, label: string): string {
  const cx = 90, cy = 88, r = 70;
  const ang = (180 - (score / 100) * 180) * (Math.PI / 180);
  const nx = cx + r * Math.cos(ang), ny = cy - r * Math.sin(ang);
  const col = score > 60 ? "var(--up)" : score < 40 ? "var(--down)" : "var(--hold)";
  return `<svg viewBox="0 0 180 100" width="100%" role="img" aria-label="리스크 ${score}">
    <path d="M20 88 A70 70 0 0 1 160 88" fill="none" stroke="var(--line)" stroke-width="12" stroke-linecap="round"/>
    <path d="M20 88 A70 70 0 0 1 160 88" fill="none" stroke="${col}" stroke-width="12" stroke-linecap="round"
      stroke-dasharray="${(score / 100) * 220} 999"/>
    <line x1="${cx}" y1="${cy}" x2="${nx.toFixed(1)}" y2="${ny.toFixed(1)}" stroke="var(--text)" stroke-width="2.5"/>
    <circle cx="${cx}" cy="${cy}" r="4" fill="var(--text)"/>
    <text x="90" y="62" text-anchor="middle" font-family="var(--mono)" font-size="26" font-weight="700" fill="var(--text)">${score}</text>
  </svg><div class="lab" style="color:${col}">${esc(label)}</div>`;
}

// ---------------------------------------------------------------------------
// 렌더: 시장 다이어그램 (/api/market)
// ---------------------------------------------------------------------------
interface Tile { ticker: string; name: string; price: number; chg_pct: number; }
interface MarketData {
  ts: string; indices: Tile[]; vix: number | null; sectors: Tile[]; etfs?: Tile[];
  risk_score: number; risk_label: string;
}
interface Mover { rank: number; ticker: string; name: string; price: number; chg_pct: number; volume: number; }

function renderMarket(m: MarketData | null) {
  if (!m) {
    $("gauge").innerHTML = '<div class="skel" style="height:120px"></div>';
    return;
  }
  const RISK_KR: Record<string, string> = { RISK_OFF: "Risk-Off", NEUTRAL: "중립", RISK_ON: "Risk-On" };
  $("gauge").innerHTML = gaugeSvg(m.risk_score, RISK_KR[m.risk_label] ?? m.risk_label);

  $("heatmap").innerHTML = m.sectors
    .map((s) => {
      const op = Math.min(0.85, Math.abs(s.chg_pct) / 3 + 0.12);
      const bg = s.chg_pct >= 0 ? `rgba(240,82,77,${op})` : `rgba(76,141,245,${op})`;
      return `<div class="tile" style="background:${bg}" data-tk="${esc(s.ticker)}">
        <div class="tk">${esc(s.name)}</div><div class="pc">${fmtPct(s.chg_pct)}</div></div>`;
    })
    .join("");

  const idxRows = m.indices.map(
    (i) => `<div class="idx"><span><b>${esc(i.ticker)}</b> <span class="nm">${esc(i.name)}</span></span>
      <span data-num class="${pctCls(i.chg_pct)}">${fmtPct(i.chg_pct)}</span></div>`,
  );
  if (m.vix !== null)
    idxRows.push(`<div class="idx"><span><b>VIX</b> <span class="nm">변동성</span></span>
      <span data-num>${fmtNum(m.vix, 1)}</span></div>`);
  $("indices").innerHTML = idxRows.join("");

  const etfs = m.etfs ?? [];
  $("etfs").innerHTML = etfs.length
    ? etfs
        .map(
          (e) => `<div class="etf-tile" data-tk="${esc(e.ticker)}">
            <span class="tk">${esc(e.ticker)}</span>
            <span class="ko">${esc(e.name)}</span>
            <span class="pc ${pctCls(e.chg_pct)}" data-num>${fmtPct(e.chg_pct)}</span>
          </div>`,
        )
        .join("")
    : '<div class="sub" style="color:var(--text-dim);padding:4px 0">—</div>';
}

function renderMovers(id: string, list: Mover[]) {
  if (!list || list.length === 0) {
    $(id).innerHTML = '<div class="nm" style="color:var(--text-dim);padding:12px 0">데이터 없음</div>';
    return;
  }
  $(id).innerHTML = list
    .map(
      (m) => `<div class="mv" data-tk="${esc(m.ticker)}">
        <span class="rk">${m.rank}</span>
        <span><span class="tk">${esc(m.ticker)}</span> <span class="nm">${esc(m.name)}</span></span>
        <span class="px" data-num>${fmtNum(m.price)}</span>
        <span class="pc ${pctCls(m.chg_pct)}" data-num>${fmtPct(m.chg_pct)}</span>
      </div>`,
    )
    .join("");
}

// ---------------------------------------------------------------------------
// 렌더: 전략 카드 (/api/dashboard)
// ---------------------------------------------------------------------------
interface Verdict {
  state: string; state_kr: string; action: string; confidence: number;
  headline: string; handoff?: string; decline_type: { kr: string; code: string };
  axes: { macro: number; macro_phase?: string; price_stress: number; rate_stress: number | null };
  evidence: { trend_broken: boolean; breadth_above_200dma: number; tape_drawdown: number };
}
interface AmqsMetric { ticker: string; signal: string; totalScore100: number; subtheme?: string; selected?: boolean; }
interface WatchItem { ticker: string; ko: string; group: string; signal: string; score: number; }
interface DashData {
  ards?: { verdict: Verdict };
  amqs?: { regime: { label: string }; metrics: AmqsMetric[] };
  watchlist?: WatchItem[];
}

const WL_GROUP_KR: Record<string, string> = { bigtech: "빅테크", ai_semi: "AI 반도체", ai_infra: "AI 인프라" };
function renderWatchlist(items: WatchItem[] | undefined) {
  const root = $("watchlist");
  if (!items || items.length === 0) {
    root.innerHTML = '<div class="sub" style="color:var(--text-dim);padding:8px 0">데이터 준비 중 — 일1회 갱신.</div>';
    return;
  }
  const order = ["bigtech", "ai_semi", "ai_infra"];
  const byG: Record<string, WatchItem[]> = {};
  for (const w of items) (byG[w.group] = byG[w.group] ?? []).push(w);
  root.innerHTML = order
    .filter((g) => byG[g]?.length)
    .map(
      (g) => `<div class="wl-group">
        <div class="wl-gh">${WL_GROUP_KR[g] ?? g}</div>
        <div class="wl-items">${byG[g]
          .sort((a, b) => b.score - a.score)
          .map(
            (w) => `<div class="wl-item" data-tk="${esc(w.ticker)}">
              <span class="tk">${esc(w.ticker)}</span>
              <span class="ko">${esc(w.ko)}</span>
              ${badge(w.signal)}
            </div>`,
          )
          .join("")}</div>
      </div>`,
    )
    .join("");
}

function renderStrategies(d: DashData | null) {
  const root = $("strategies");
  if (!d || (!d.ards && !d.amqs)) {
    root.innerHTML = '<div class="card"><div class="skel" style="height:140px"></div></div><div class="card"><div class="skel" style="height:140px"></div></div>';
    return;
  }
  const cards: string[] = [];

  // ARDS
  if (d.ards?.verdict) {
    const v = d.ards.verdict;
    const sig = ARDS_MAP[v.action] ?? "HOLD";
    const defense = v.action === "DEFENSIVE_ARDS";
    const strip = v.evidence.trend_broken && sig !== "SELL" ? " risk-strip" : "";
    cards.push(`<div class="card${strip}">
      <div class="card-h"><span class="nm">ARDS</span><span class="sub">시장 국면 · ${esc(v.state_kr)}</span></div>
      <div class="row-sig"><span><b>QQQ</b> <span class="sub">나스닥100</span></span>${badge(sig)}</div>
      <div class="kv"><span class="k">방어모드</span><span>${defense ? "ON ⚠" : "OFF"}</span></div>
      <div class="kv"><span class="k">거시 Composite</span><span data-num>${fmtNum(v.axes.macro, 1)} · ${esc(v.axes.macro_phase ?? "")}</span></div>
      <div class="kv"><span class="k">가격 스트레스</span><span data-num>${fmtNum(v.axes.price_stress, 1)}</span></div>
      <div class="kv"><span class="k">하락유형</span><span>${esc(v.decline_type.kr)}</span></div>
      <div class="kv"><span class="k">신뢰도</span><span data-num>${v.confidence}%</span></div>
      <p class="headline">${esc(v.headline)}</p>
      ${v.handoff ? `<p class="handoff">${esc(v.handoff)}</p>` : ""}
    </div>`);
  }

  // AMQS
  if (d.amqs) {
    const REG: Record<string, string> = { RISK_ON: "리스크온", RISK_OFF: "리스크오프", DEFENSIVE: "방어" };
    const rows = (d.amqs.metrics ?? [])
      .map((m) => ({ m, sig: AMQS_MAP[m.signal] }))
      .filter((x) => x.sig)
      .sort((a, b) => b.m.totalScore100 - a.m.totalScore100)
      .slice(0, 6)
      .map(
        ({ m, sig }) => `<div class="row-sig">
          <span><b>${esc(m.ticker)}</b> <span class="sub">${esc(m.subtheme ?? "")} · ${fmtNum(m.totalScore100, 0)}점</span></span>${badge(sig!)}</div>`,
      )
      .join("");
    const off = d.amqs.regime.label !== "RISK_ON";
    cards.push(`<div class="card${off ? " risk-strip" : ""}">
      <div class="card-h"><span class="nm">AMQS</span><span class="sub">AI 인프라 모멘텀 · ${esc(REG[d.amqs.regime.label] ?? d.amqs.regime.label)}</span></div>
      ${rows || '<div class="sub">선정 종목 없음</div>'}
    </div>`);
  }

  root.innerHTML = cards.join("");
}

// ---------------------------------------------------------------------------
// 렌더: 뉴스 (/api/news)
// ---------------------------------------------------------------------------
interface NewsItem { id: string; ts: string; title_ko: string; summary_ko: string; category: string; tickers: string[]; source: string; url: string; }
let allNews: NewsItem[] = [];
let newsFilter = "전체";
function timeAgo(iso: string): string {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const m = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (m < 60) return `${m}분 전`;
  const h = Math.round(m / 60);
  return h < 24 ? `${h}시간 전` : `${Math.round(h / 24)}일 전`;
}
function renderNews(market_summary: { summary_ko: string } | null, items: NewsItem[]) {
  allNews = items;
  if (market_summary?.summary_ko) $("market-summary").textContent = market_summary.summary_ko;
  const cats = ["전체", ...Array.from(new Set(items.map((i) => i.category)))];
  $("news-filter").innerHTML = cats.map((c) => `<span class="chip ${c === newsFilter ? "on" : ""}" data-cat="${esc(c)}">${esc(c)}</span>`).join("");
  drawNews();
}
function drawNews() {
  const list = newsFilter === "전체" ? allNews : allNews.filter((i) => i.category === newsFilter);
  if (list.length === 0) {
    $("news").innerHTML = '<div class="sub" style="color:var(--text-dim);padding:12px 0">뉴스가 아직 없습니다.</div>';
    return;
  }
  $("news").innerHTML = list
    .map(
      (i) => `<div class="news-item">
        <span class="cat">${esc(i.category)}</span>
        <span><a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.title_ko)}</a>
          <span class="sub" style="color:var(--text-dim)"> — ${esc(i.summary_ko)}</span></span>
        <span class="tm">${esc(i.source)} · ${timeAgo(i.ts)}</span>
      </div>`,
    )
    .join("");
}

// ---------------------------------------------------------------------------
// 렌더: 랭킹 / 통계
// ---------------------------------------------------------------------------
function renderRankings(top: Array<{ rank: number; ticker: string; search_count: number }>) {
  if (!top || top.length === 0) {
    $("rankings").innerHTML = '<div class="sub" style="color:var(--text-dim)">아직 충분한 검색 데이터가 없습니다.</div>';
    return;
  }
  $("rankings").innerHTML = top
    .map((r) => `<div class="rk-row"><span><span class="ct">${r.rank}.</span> <span class="tk">${esc(r.ticker)}</span></span><span class="ct">${r.search_count}회</span></div>`)
    .join("");
}
function renderStats(dau: number, total: number) {
  $("stats").innerHTML = `
    <div class="stat"><div class="big" data-num>${dau.toLocaleString()}</div><div class="lab">DAU (오늘)</div></div>
    <div class="stat"><div class="big" data-num>${total.toLocaleString()}</div><div class="lab">누적 방문자</div></div>
    <div class="cap">익명 집계 · 개인정보 미저장</div>`;
}

// ---------------------------------------------------------------------------
// 갱신 표시
// ---------------------------------------------------------------------------
/** 모든 시각은 KST(Asia/Seoul) 고정 노출 — 브라우저 타임존 무관. */
function fmtKST(iso: string): string {
  return new Date(iso).toLocaleString("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
function setUpdated(iso: string | null) {
  const node = $("updated");
  if (!iso) {
    node.textContent = "데이터 준비 중 — 곧 갱신됩니다.";
    return;
  }
  const age = (Date.now() - new Date(iso).getTime()) / 60000;
  const t = `${fmtKST(iso)} KST`;
  if (age > 20) {
    node.textContent = `⚠ 데이터 지연 중 — 마지막 갱신 ${t}`;
    node.classList.add("stale");
  } else {
    node.textContent = `마지막 갱신 ${t}`;
    node.classList.remove("stale");
  }
}

// ---------------------------------------------------------------------------
// 검색
// ---------------------------------------------------------------------------
/** 입력 중 자동완성 제안 (티커/한글명/영문명/약칭). 클라이언트 번들 사전, 서버 호출 없음. */
function renderSuggestions(q: string) {
  const box = $("search-result");
  const hits = searchSymbols(q, 8);
  if (hits.length === 0) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  box.innerHTML =
    `<div class="ac-head">제안</div>` +
    hits
      .map(
        (s) => `<div class="ac-item" data-pick="${esc(s.t)}">
          <span class="tk">${esc(s.t)}</span>
          <span class="ko">${esc(s.ko)}</span>
          <span class="en">${esc(s.en)}</span>
        </div>`,
      )
      .join("");
}

/** 입력값 → 검색할 티커로 해석(정확 티커 우선, 아니면 첫 제안). */
function resolveTicker(value: string): string | null {
  const v = value.trim();
  if (!v) return null;
  if (SYM_BY_TICKER[v.toUpperCase()]) return v.toUpperCase();
  const hits = searchSymbols(v, 1);
  return hits.length ? hits[0].t : v.toUpperCase();
}

async function doSearch(q: string) {
  const box = $("search-result");
  box.hidden = false;
  box.innerHTML = '<div class="skel" style="height:40px"></div>';
  try {
    const { data } = await getJSON<{ ticker: string; signals: Array<{ strategy: string; signal: string; score: number; date: string }> }>(
      `/api/search?q=${encodeURIComponent(q)}`,
    );
    const sigs = data.signals?.length
      ? data.signals.map((s) => `<div class="row-sig"><span>${esc(s.strategy)} <span class="sub">${esc(s.date)}</span></span>${badge(s.signal, "")}</div>`).join("")
      : '<div class="sub" style="color:var(--text-dim)">해당 종목 시그널 없음 (유니버스 외)</div>';
    const sym = SYM_BY_TICKER[data.ticker];
    const nm = sym ? `<span class="sub">${esc(sym.ko)} · ${esc(sym.en)}</span>` : "";
    box.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:baseline"><span><b>${esc(data.ticker)}</b> ${nm}</span><span class="chip" id="sc-close">닫기 ✕</span></div>${sigs}
      <div class="sub" style="color:var(--text-dim);margin-top:6px">⚠ 투자 조언이 아닙니다.</div>`;
    $("sc-close").onclick = () => (box.hidden = true);
  } catch {
    box.innerHTML = '<div class="sub">검색 실패</div>';
  }
}

// ---------------------------------------------------------------------------
// 로딩
// ---------------------------------------------------------------------------
async function loadAll() {
  let updated: string | null = null;
  const tasks: Array<Promise<void>> = [
    getJSON<DashData>("/api/dashboard")
      .then((r) => { renderStrategies(r.data); renderWatchlist(r.data?.watchlist); updated = r.updated_at ?? updated; })
      .catch(() => { renderStrategies(null); renderWatchlist(undefined); }),
    getJSON<MarketData>("/api/market").then((r) => { renderMarket(r.data); updated = r.updated_at ?? updated; }).catch(() => renderMarket(null)),
    getJSON<{ gainers: Mover[]; losers: Mover[] }>("/api/movers")
      .then((r) => { renderMovers("gainers", r.data?.gainers ?? []); renderMovers("losers", r.data?.losers ?? []); })
      .catch(() => { renderMovers("gainers", []); renderMovers("losers", []); }),
    getJSON<{ market_summary: { summary_ko: string } | null; items: NewsItem[] }>("/api/news?limit=12")
      .then((r) => renderNews(r.data.market_summary, r.data.items ?? [])).catch(() => renderNews(null, [])),
    getJSON<{ top: Array<{ rank: number; ticker: string; search_count: number }> }>("/api/rankings")
      .then((r) => renderRankings(r.data.top ?? [])).catch(() => renderRankings([])),
    getJSON<{ dau: number; total_au: number }>("/api/track", { method: "POST" })
      .then((r) => renderStats(r.data.dau, r.data.total_au)).catch(() => renderStats(0, 0)),
  ];
  await Promise.allSettled(tasks);
  setUpdated(updated);
}

// ---------------------------------------------------------------------------
// 이벤트 & 부트
// ---------------------------------------------------------------------------
function boot() {
  applyLang();
  // 토글
  $("theme").onclick = () => {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    $("theme").textContent = next === "light" ? "☀" : "☾";
  };
  $("lang").onclick = () => { lang = lang === "ko" ? "en" : "ko"; applyLang(); };
  // 검색 — 입력 중 자동완성(티커/한글/영문/약칭), Enter/선택 시 조회
  const input = $("search") as HTMLInputElement;
  input.addEventListener("input", () => {
    if (input.value.trim()) renderSuggestions(input.value);
    else $("search-result").hidden = true;
  });
  input.addEventListener("keydown", (e) => {
    if ((e as KeyboardEvent).key === "Enter") {
      const tk = resolveTicker(input.value);
      if (tk) { input.value = tk; doSearch(tk); }
    } else if ((e as KeyboardEvent).key === "Escape") {
      $("search-result").hidden = true;
    }
  });
  // 위임: 자동완성 선택 / 티커 클릭 → 검색, 카테고리 칩, 외부 클릭 시 닫기
  document.addEventListener("click", (e) => {
    const pick = (e.target as HTMLElement).closest<HTMLElement>("[data-pick]");
    if (pick?.dataset.pick) { input.value = pick.dataset.pick; doSearch(pick.dataset.pick); return; }
    const t = (e.target as HTMLElement).closest<HTMLElement>("[data-tk]");
    if (t?.dataset.tk) { input.value = t.dataset.tk; doSearch(t.dataset.tk); return; }
    const chip = (e.target as HTMLElement).closest<HTMLElement>("[data-cat]");
    if (chip?.dataset.cat) { newsFilter = chip.dataset.cat; renderNews(null, allNews); return; }
    if (!(e.target as HTMLElement).closest(".hdr-search")) $("search-result").hidden = true;
  });
  // 기능 메뉴 → 모달
  const modal = $("modal");
  const openFeature = (name: string) => {
    const f = FEATURES[name];
    if (!f) return;
    f.render($("modal-body"));
    modal.hidden = false;
    document.body.style.overflow = "hidden";
  };
  const closeFeature = () => {
    modal.hidden = true;
    document.body.style.overflow = "";
  };
  document.querySelectorAll<HTMLElement>(".menu-btn").forEach((b) => {
    b.onclick = () => openFeature(b.dataset.feature!);
  });
  modal.querySelectorAll<HTMLElement>("[data-close]").forEach((c) => (c.onclick = closeFeature));
  document.addEventListener("keydown", (e) => {
    if ((e as KeyboardEvent).key === "Escape" && !modal.hidden) closeFeature();
  });
  // 딥링크: #saju 등으로 열기
  const hash = location.hash.slice(1);
  if (FEATURES[hash]) openFeature(hash);

  // 상승색 안내 1회
  if (!localStorage.getItem("up-tip")) {
    $("tooltip").hidden = false;
    setTimeout(() => ($("tooltip").hidden = true), 5000);
    localStorage.setItem("up-tip", "1");
  }
  loadAll();
}
boot();
