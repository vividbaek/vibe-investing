/**
 * 4개 메뉴 기능 패널 (모달). 내용은 AIInvestor 포팅.
 *  - 사주: 결정론 엔진(saju.ts) 완전 동작
 *  - 예측: 출첵 + 예측 — localStorage 로컬판(포인트·스트릭 로컬 저장)
 *  - 페르소나: 3인 설명·선택 (AI 코멘트는 백엔드 필요 → 안내)
 *  - 친구추천: 보상구조 + 로컬 초대코드 + 공유링크 (추적은 백엔드 필요)
 */
import { buildProfile, todayFor, narrative, ELEMENT_KR, ELEMENT_EMOJI, SAJU_DISCLAIMER } from "./saju";
import { SYM_BY_TICKER } from "../../shared/symbols";

const esc = (s: unknown): string =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);

// --- 로컬 상태 (localStorage) ----------------------------------------------
const LS = {
  get<T>(k: string, d: T): T {
    try {
      const v = localStorage.getItem(k);
      return v ? (JSON.parse(v) as T) : d;
    } catch {
      return d;
    }
  },
  set(k: string, v: unknown) {
    try {
      localStorage.setItem(k, JSON.stringify(v));
    } catch {
      /* ignore */
    }
  },
};
function getPoints(): number {
  return LS.get<number>("vi_points", 0);
}
function addPoints(n: number): number {
  const p = getPoints() + n;
  LS.set("vi_points", p);
  return p;
}
function kstToday(): string {
  return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}

// ===========================================================================
// 사주
// ===========================================================================
const ELEM_LABEL = (e: keyof typeof ELEMENT_KR) => `${ELEMENT_EMOJI[e]} ${ELEMENT_KR[e]}`;

function renderSajuResult(box: HTMLElement, birthDate: string, hour: number | null) {
  const profile = buildProfile(birthDate, hour);
  const today = todayFor(profile);
  const narr = narrative(profile, today);
  LS.set("vi_saju", { birthDate, hour });
  box.innerHTML = `
    <div class="saju-top">
      <div><span class="lab">내 일주</span><b>${esc(profile.iljuLabel)}</b> · ${ELEM_LABEL(profile.myElement)} 일간</div>
      <div><span class="lab">오늘 일진</span><b>${esc(today.iljuLabel)}</b> · ${ELEM_LABEL(today.todayElement)}</div>
      <div class="rel">${esc(narr.header)}</div>
    </div>
    <div class="saju-bars">
      ${narr.axes
        .map(
          (a) => `<div class="bar-row">
            <span class="bk">${esc(a.label)}</span>
            <span class="bt"><span class="bf" style="width:${a.score}%"></span></span>
            <span class="bs">${a.score} · ${esc(a.grade)}</span>
            <span class="bx">${esc(a.text)}</span>
          </div>`,
        )
        .join("")}
    </div>
    <div class="saju-focus"><b>오늘의 투자 포인트</b> ${esc(narr.invFocus)}</div>
    <div class="saju-focus"><b>주의</b> ${esc(narr.caution)}</div>
    <div class="saju-fav"><b>오늘 유리한 오행</b> ${today.favored.map((e) => ELEM_LABEL(e)).join("  ")}</div>
    <p class="disc">${esc(SAJU_DISCLAIMER)}</p>`;
}

export function renderSaju(body: HTMLElement) {
  const saved = LS.get<{ birthDate: string; hour: number | null } | null>("vi_saju", null);
  const hourOpts = ['<option value="">모름</option>']
    .concat(Array.from({ length: 24 }, (_, h) => `<option value="${h}">${String(h).padStart(2, "0")}시</option>`))
    .join("");
  body.innerHTML = `
    <h3 class="ft-h">🔮 사주 — 오늘의 투자운</h3>
    <p class="ft-sub">생년월일(양력)과 태어난 시각으로 오늘 일진과의 상생·상극을 풀이합니다. 결정론 계산(저장은 이 브라우저에만).</p>
    <div class="saju-form">
      <input id="saju-date" type="date" value="${saved?.birthDate ?? ""}" max="${kstToday()}" />
      <select id="saju-hour">${hourOpts}</select>
      <button id="saju-go" class="btn-primary">풀이 보기</button>
    </div>
    <div id="saju-result" class="saju-result"></div>`;
  const dateEl = body.querySelector("#saju-date") as unknown as HTMLInputElement;
  const hourEl = body.querySelector("#saju-hour") as unknown as HTMLSelectElement;
  if (saved?.hour !== null && saved?.hour !== undefined) hourEl.value = String(saved.hour);
  const resultBox = body.querySelector<HTMLElement>("#saju-result")!;
  const go = () => {
    if (!dateEl.value) {
      resultBox.innerHTML = '<div class="sub">생년월일을 입력하세요.</div>';
      return;
    }
    renderSajuResult(resultBox, dateEl.value, hourEl.value === "" ? null : Number(hourEl.value));
  };
  body.querySelector<HTMLButtonElement>("#saju-go")!.onclick = go;
  if (saved?.birthDate) go();
}

// ===========================================================================
// 예측 — 출첵 + 예측
// ===========================================================================
interface Attend {
  last: string;
  streak: number;
}
interface Pred {
  ticker: string;
  dir: "up" | "down";
  date: string;
  ko: string;
}

function attendancePoints(streak: number): { base: number; bonus: number } {
  // AIInvestor: base 10, +5/연속, 최대 +50
  return { base: 10, bonus: Math.min(50, Math.max(0, streak - 1) * 5) };
}

export function renderPredict(body: HTMLElement) {
  const draw = () => {
    const pts = getPoints();
    const at = LS.get<Attend>("vi_attend", { last: "", streak: 0 });
    const today = kstToday();
    const did = at.last === today;
    const preds = LS.get<Pred[]>("vi_preds", []);
    body.innerHTML = `
      <h3 class="ft-h">🎯 예측 — 출석 & 시장 예측</h3>
      <div class="points-bar">보유 포인트 <b>${pts.toLocaleString()} P</b> <span class="sub">· 로컬 집계(이 브라우저)</span></div>

      <section class="ft-card">
        <div class="ft-card-h">📅 출석 체크</div>
        <p class="ft-sub">매일 출석 시 10P, 연속 출석마다 +5P (최대 +50P).</p>
        <div class="attend-row">
          <div class="streak">연속 <b>${at.streak}</b>일</div>
          <button id="attend-btn" class="btn-primary" ${did ? "disabled" : ""}>${did ? "오늘 출석 완료 ✓" : "출석 체크 +10P~"}</button>
        </div>
      </section>

      <section class="ft-card">
        <div class="ft-card-h">📈 오늘의 예측</div>
        <p class="ft-sub">종목의 다음 거래일 방향을 예측 (참여 시 +1P). 결과는 다음 거래일에 직접 확인.</p>
        <div class="pred-form">
          <input id="pred-tk" placeholder="티커 (예: NVDA)" />
          <button class="btn-up" data-dir="up">▲ 상승</button>
          <button class="btn-down" data-dir="down">▼ 하락</button>
        </div>
        <div class="pred-list">
          ${
            preds.length
              ? preds
                  .slice(-12)
                  .reverse()
                  .map(
                    (p) => `<div class="pred-item">
                      <span class="tk">${esc(p.ticker)}</span><span class="ko">${esc(p.ko)}</span>
                      <span class="${p.dir === "up" ? "up" : "down"}">${p.dir === "up" ? "▲ 상승" : "▼ 하락"}</span>
                      <span class="sub">${esc(p.date)} · 대기</span></div>`,
                  )
                  .join("")
              : '<div class="sub" style="color:var(--text-dim)">아직 예측이 없습니다.</div>'
          }
        </div>
      </section>`;

    body.querySelector<HTMLButtonElement>("#attend-btn")!.onclick = () => {
      const cur = LS.get<Attend>("vi_attend", { last: "", streak: 0 });
      if (cur.last === today) return;
      const yest = new Date(Date.now() + 9 * 3600 * 1000 - 86400000).toISOString().slice(0, 10);
      const streak = cur.last === yest ? cur.streak + 1 : 1;
      const { base, bonus } = attendancePoints(streak);
      LS.set("vi_attend", { last: today, streak });
      addPoints(base + bonus);
      draw();
    };
    const tkEl = body.querySelector<HTMLInputElement>("#pred-tk")!;
    body.querySelectorAll<HTMLButtonElement>("[data-dir]").forEach((b) => {
      b.onclick = () => {
        const t = tkEl.value.trim().toUpperCase();
        if (!t) return;
        const list = LS.get<Pred[]>("vi_preds", []);
        list.push({ ticker: t, dir: b.dataset.dir as "up" | "down", date: kstToday(), ko: SYM_BY_TICKER[t]?.ko ?? "" });
        LS.set("vi_preds", list);
        addPoints(1);
        draw();
      };
    });
  };
  draw();
}

// ===========================================================================
// 페르소나
// ===========================================================================
const PERSONAS = [
  { key: "buffett", name: "Warren Buffett", kr: "워런 버핏", tag: "장기 가치", desc: "경제적 해자·잉여현금흐름·ROE 중심. 적정가 대비 가격, 장기 보유." },
  { key: "dalio", name: "Ray Dalio", kr: "레이 달리오", tag: "매크로 / 올웨더", desc: "거시·신용사이클·리스크 패리티. 분산과 균형의 올웨더 관점." },
  { key: "wood", name: "Cathie Wood", kr: "캐시 우드", tag: "혁신 성장", desc: "AI·로봇·유전체·에너지 등 파괴적 혁신. 5년 지수성장 관점." },
];

export function renderPersona(body: HTMLElement) {
  let selected = LS.get<string>("vi_persona", "buffett");
  const draw = () => {
    body.innerHTML = `
      <h3 class="ft-h">🧠 페르소나 — 투자 멘토 의견</h3>
      <p class="ft-sub">멘토 페르소나를 고르고 종목을 입력하면 해당 관점의 코멘트를 받습니다.</p>
      <div class="persona-grid">
        ${PERSONAS.map(
          (p) => `<div class="persona-card ${p.key === selected ? "on" : ""}" data-p="${p.key}">
            <div class="pn">${esc(p.kr)} <span class="sub">${esc(p.name)}</span></div>
            <div class="pt">${esc(p.tag)}</div>
            <div class="pd">${esc(p.desc)}</div>
          </div>`,
        ).join("")}
      </div>
      <div class="persona-ask">
        <input id="persona-tk" placeholder="종목 티커 (예: NVDA)" />
        <button id="persona-go" class="btn-primary">${esc(PERSONAS.find((p) => p.key === selected)!.kr)} 의견 보기</button>
      </div>
      <div id="persona-out" class="persona-out"></div>
      <p class="disc">ℹ AI는 오류·환각이 있을 수 있어 본 응답은 참고용입니다. 투자 책임은 본인에게 있습니다.</p>`;
    body.querySelectorAll<HTMLElement>("[data-p]").forEach((c) => {
      c.onclick = () => {
        selected = c.dataset.p!;
        LS.set("vi_persona", selected);
        draw();
      };
    });
    body.querySelector<HTMLButtonElement>("#persona-go")!.onclick = () => {
      const t = body.querySelector<HTMLInputElement>("#persona-tk")!.value.trim().toUpperCase();
      const out = body.querySelector<HTMLElement>("#persona-out")!;
      const p = PERSONAS.find((x) => x.key === selected)!;
      out.innerHTML = t
        ? `<div class="sub"><b>${esc(p.kr)}</b> 관점의 <b>${esc(t)}</b> AI 코멘트는 <b>AIInvestor 백엔드(DeepSeek)</b> 연결이 필요합니다.
           현재 대시보드는 정적 빌드라 코멘트 생성은 연동 후 제공됩니다. 우선 ${esc(p.tag)} 관점: <i>${esc(p.desc)}</i></div>`
        : '<div class="sub">티커를 입력하세요.</div>';
    };
  };
  draw();
}

// ===========================================================================
// 친구추천
// ===========================================================================
function inviteCode(): string {
  let c = LS.get<string>("vi_invite", "");
  if (!c) {
    const alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    c = Array.from({ length: 8 }, () => alpha[Math.floor((crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32) * alpha.length)]).join("");
    LS.set("vi_invite", c);
  }
  return c;
}

export function renderReferral(body: HTMLElement) {
  const code = inviteCode();
  const link = `${location.origin}/?ref=${code}`;
  body.innerHTML = `
    <h3 class="ft-h">👥 친구 추천</h3>
    <p class="ft-sub">친구를 초대하고 포인트를 받으세요. (보상 구조는 AIInvestor 기준 · 실제 추적·정산은 백엔드 연동 필요)</p>
    <div class="ref-code">
      <div><span class="lab">내 초대코드</span><b class="mono">${esc(code)}</b></div>
      <div class="ref-link"><input id="ref-link" readonly value="${esc(link)}" /><button id="ref-copy" class="btn-primary">복사</button></div>
    </div>
    <table class="ref-table">
      <tr><th>이벤트</th><th>초대한 사람</th><th>친구</th></tr>
      <tr><td>링크 클릭(랜딩)</td><td class="up">+30P</td><td>—</td></tr>
      <tr><td>친구 가입</td><td>—</td><td class="up">+200P</td></tr>
      <tr><td>첫 미션 완료</td><td class="up">+470P</td><td>—</td></tr>
      <tr><td>전환당 합계</td><td class="up"><b>+500P</b></td><td class="up"><b>+200P</b></td></tr>
      <tr><td>7일 미활동(좀비)</td><td class="down">-30P</td><td>—</td></tr>
    </table>
    <p class="disc">※ 현재는 초대코드·공유링크만 로컬 생성됩니다. 클릭·가입·미션 추적과 포인트 정산은 백엔드(AIInvestor) 연동 후 동작합니다.</p>`;
  body.querySelector<HTMLButtonElement>("#ref-copy")!.onclick = () => {
    const inp = body.querySelector<HTMLInputElement>("#ref-link")!;
    inp.select();
    navigator.clipboard?.writeText(inp.value);
    body.querySelector<HTMLButtonElement>("#ref-copy")!.textContent = "복사됨 ✓";
  };
}

// ===========================================================================
export const FEATURES: Record<string, { title: string; render: (b: HTMLElement) => void }> = {
  persona: { title: "페르소나", render: renderPersona },
  predict: { title: "예측", render: renderPredict },
  saju: { title: "사주", render: renderSaju },
  referral: { title: "친구추천", render: renderReferral },
};
