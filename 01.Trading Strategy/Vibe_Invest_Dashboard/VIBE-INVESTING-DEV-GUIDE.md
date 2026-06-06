# Vibe Investing — 전체 개발 가이드 & 화면 가이드

> **버전**: v0.2 | **작성일**: 2026-06-06 | **작성**: Claude + Dennis Kim
> **v0.2 반영**: 등락색 한국식 확정, 뉴스 요약 1일 9회(KST) 스케줄 확정, DAU=유저 해시 방식 확정, 도메인은 우선 workers.dev
> **원칙**: "LLM은 엑셀이지 오라클이 아니다" — 모든 시그널은 룰 기반, LLM은 요약/정리 도구로만 사용

---

# PART A. 개발 가이드

## 1. 시스템 개요

3개 퀀트 전략(ARDS, AMQS, MU_Hynix)의 대시보드를 단일 웹 페이지로 통합한
**Vibe Investing** 사이트. Cloudflare 무료 티어 + Azure 무료 티어 + DeepSeek API로 운영.

```
┌─────────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS (Cloudflare CDN)
┌──────────────────────────▼──────────────────────────────────────┐
│  Cloudflare Workers (Static Assets + API)                        │
│  ├─ 정적 프론트엔드 (대시보드 SPA)                                │
│  ├─ GET  /api/dashboard     ← 통합 대시보드 데이터               │
│  ├─ GET  /api/search?q=     ← 종목 검색 + 검색 로그 기록         │
│  ├─ GET  /api/rankings      ← 검색 상위 5                        │
│  ├─ GET  /api/movers        ← 나스닥 급등10/급락10               │
│  ├─ GET  /api/news          ← 뉴스 요약 (D1 캐시)                │
│  ├─ POST /api/ingest/news   ← Azure→CF 수신 (HMAC 인증)          │
│  └─ POST /api/track         ← DAU/AU 카운트                      │
├─────────────────────────────────────────────────────────────────┤
│  Cron Trigger Worker                                             │
│  ├─ */10 * * * * : 지수/섹터/급등급락 수집 → R2 + D1            │
│  └─ 30 21 * * 1-5 (UTC) : 일봉 수집 → ARDS/AMQS/MU_Hynix 시그널 │
├──────────────┬──────────────────────┬───────────────────────────┤
│  D1 (SQLite) │  R2 (Object Storage) │  KV (선택, 미사용 권장)    │
└──────────────┴──────────────────────┴───────────────────────────┘
                           ▲
                           │ POST /api/ingest/news (HMAC-SHA256)
┌──────────────────────────┴──────────────────────────────────────┐
│  Azure Functions (Consumption/Flex, 무료 한도)                   │
│  └─ Timer Trigger (1일 9회 KST): 뉴스 수집 → DeepSeek 요약 → CF │
│       ├─ 뉴스 소스: Finnhub /news, Alpha Vantage NEWS_SENTIMENT  │
│       └─ DeepSeek API: deepseek-chat (한국어 요약 + 카테고리)    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 역할 분담 (왜 이렇게 나누나)

| 작업 | 위치 | 이유 |
|---|---|---|
| 시세/급등급락 수집 | CF Cron Worker | I/O 작업이라 10ms CPU 제한 무관, CF 내부 저장소 직접 접근 |
| 뉴스 수집 + LLM 요약 | Azure Functions | DeepSeek 응답 대기·재시도·프롬프트 관리에 유리, Azure MVP 크레딧/무료 한도 활용 |
| 시그널 계산 (일 1회) | CF Cron Worker | 일봉 기반 룰 연산은 가볍고, 결과를 D1에 바로 기록 |
| 프론트 렌더링 | 클라이언트 | 다이어그램/차트를 SVG로 클라이언트 렌더 → Worker CPU 절약 |

### 1.2 무료 티어 한도 체크 (2026-06 기준, 변동 가능)

| 서비스 | 무료 한도 | 본 프로젝트 예상 사용량 |
|---|---|---|
| CF Workers | 100K req/day, 10ms CPU | 크론 144회 + API 호출. DAU 수천까지 여유 |
| CF D1 | 5GB, 읽기 5M rows/day, 쓰기 100K rows/day | 쓰기: 크론 ~1K/day + 검색로그. 충분 |
| CF R2 | 10GB, Class A 1M/월 | 스냅샷 JSON 수십 MB 수준 |
| CF Cron | 무료 포함 | */10 = 4,320회/월 |
| Azure Functions | 월 100만 실행 + 400,000 GB-s 무료 | 타이머 4,320회/월 |
| DeepSeek API | **유료** (Claude 대비 약 1/35 수준, 캐시 히트 시 추가 할인) | 1일 9회 × 뉴스 ~20건 요약. 월 수백 원 미만 예상 |
| Finnhub | 60 calls/min 무료 | 충분 |
| Alpha Vantage | 25 calls/day 무료 | TOP_GAINERS_LOSERS 백업용으로만 |

> ⚠️ DeepSeek는 무료가 아님. 비용 상한을 두려면 (a) 장중에만 요약 실행,
> (b) 직전 요약과 뉴스 ID가 같으면 스킵, (c) max_tokens 제한.

---

## 2. 데이터 파이프라인

### 2.1 10분 주기 (CF Cron: `*/10 * * * *`)

1. Finnhub에서 수집: 주요 지수(SPY, QQQ, DIA, IWM 프록시), VIX, 섹터 ETF 11종 등락률
2. 나스닥 급등 Top 10 / 급락 Top 10 (FMP `biggest-gainers`/`biggest-losers` 또는 Finnhub 스크리닝)
3. R2에 `snapshots/market-latest.json` 저장 (이전본은 `snapshots/YYYY/MM/DD/HHmm.json`)
4. D1 `market_snapshot` 테이블에 요약 1행 upsert (프론트 폴링용)
5. `updated_at` 타임스탬프 기록 → 화면 "데이터 갱신" 표시에 사용

> 미국 장외 시간(한국 시간 새벽 외) 최적화: 크론 핸들러 첫 줄에서
> 현재 UTC가 13:00–21:30(서머타임 기준 프리장~마감) 밖이면 조기 return → API 호출 절약.

### 2.2 뉴스 요약 — 1일 9회 KST 고정 스케줄 (Azure Functions Timer)

**스케줄 (KST 기준, 24시간 커버)**

| KST | 의미 | UTC |
|---|---|---|
| 03:00 | 미국 장중 (개장 후) | 18:00 (전일) |
| 06:00 | 미국 장 마감 직후 | 21:00 (전일) |
| 08:00 | 한국 장 시작 전 | 23:00 (전일) |
| 10:00 | 한국 장중 | 01:00 |
| 12:00 | 점심 | 03:00 |
| 15:00 | 한국 장 마감 | 06:00 |
| 18:00 | 저녁 | 09:00 |
| 21:00 | 밤 | 12:00 |
| 23:00 | 미국 장 시작 전후 | 14:00 |

```
// function.json 또는 [TimerTrigger] — UTC 기준 NCRONTAB
"schedule": "0 0 1,3,6,9,12,14,18,21,23 * * *"
```
> 주의: Azure Functions 타이머는 기본 UTC. `WEBSITE_TIME_ZONE`은 플랜/OS에 따라
> 미지원이므로 **UTC로 직접 환산해 고정**하는 게 안전. 미국 서머타임 종료 시
> "미 장 시작/마감" 시각이 1시간 밀리는 점은 허용 (요약 목적이라 무방).

**처리 절차**

1. Finnhub `/news?category=general` + (선택) Alpha Vantage NEWS_SENTIMENT 수집
2. 직전 처리한 뉴스 ID 목록(Blob 또는 Table Storage)과 비교 → 신규만 추출
3. 신규 뉴스가 있으면 DeepSeek `deepseek-chat` 호출:

```
[System]
당신은 금융 뉴스 요약기입니다. 의견·전망·투자조언을 생성하지 마세요.
사실만 요약합니다.

[User]
다음 뉴스들을 한국어로 요약하세요. 각 항목당 1문장, 전체 시장 요약 2문장.
JSON만 출력: {"market_summary": "...", "items":[{"id","title_ko","summary_ko","category","tickers":[]}]}
카테고리: 거시경제|실적|반도체|AI|금리|지정학|기타
--- 뉴스 원문 ---
{news_json}
```

4. 결과를 CF Worker `/api/ingest/news`로 POST
   - 헤더: `X-Signature: HMAC-SHA256(body, INGEST_SECRET)`, `X-Timestamp` (±5분 검증)
5. CF Worker가 검증 후 D1 `news_summary` 테이블에 저장

### 2.3 일 1회 (CF Cron: `30 21 * * 1-5` UTC = 미 장마감 직후)

1. 전략별 대상 티커 일봉 수집 (Stooq CSV 무료, 백업: yfinance 비공식)
   - ARDS: QQQ + AI 관련 구성종목
   - AMQS: AI 인프라 유니버스
   - MU_Hynix: MU, (SK하이닉스는 KRX 데이터 별도 확인 필요)
2. 각 전략의 룰 적용 → 시그널 산출: `BUY | SELL | HOLD | SHORT_TERM_RISK | SURGE`
3. D1 `signals` 테이블에 기록 (히스토리 보존)
4. 단기 하락 조짐 체크 결과를 `risk_flags`에 기록 (예: 이평 이탈, 변동성 급등, 크라우딩 지표)

> 룰 로직은 `vibe-investing` 레포의 기존 스크립트를 TypeScript로 포팅.
> **포팅 후 기존 Python 결과와 1주일 병행 검증 필수.**

---

## 3. D1 스키마

```sql
-- 시장 스냅샷 (10분 갱신, 최신 1행 + 히스토리)
CREATE TABLE market_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,                -- ISO8601 UTC
  indices_json TEXT NOT NULL,      -- {"QQQ":{"price":..,"chg_pct":..}, ...}
  sectors_json TEXT NOT NULL,      -- 11개 섹터 ETF 등락
  vix REAL,
  breadth_json TEXT                -- 상승/하락 종목수 등
);

-- 급등/급락
CREATE TABLE movers (
  ts TEXT NOT NULL,
  direction TEXT CHECK(direction IN ('gainer','loser')),
  rank INTEGER,
  ticker TEXT, name TEXT, price REAL, chg_pct REAL, volume INTEGER,
  PRIMARY KEY (ts, direction, rank)
);

-- 전략 시그널
CREATE TABLE signals (
  date TEXT NOT NULL,              -- YYYY-MM-DD (미국 거래일)
  strategy TEXT NOT NULL,          -- ARDS | AMQS | MU_HYNIX
  ticker TEXT NOT NULL,
  signal TEXT CHECK(signal IN ('BUY','SELL','HOLD','SHORT_TERM_RISK','SURGE')),
  score REAL,                      -- 전략 내부 점수 (선택)
  detail_json TEXT,                -- 근거 지표 값 (Phase 2에서 프론트 노출, 수집은 1차부터)
  PRIMARY KEY (date, strategy, ticker)
);

-- 뉴스 요약 (Azure → ingest)
CREATE TABLE news_summary (
  id TEXT PRIMARY KEY,             -- 뉴스 원본 ID
  ts TEXT NOT NULL,
  title_ko TEXT, summary_ko TEXT,
  category TEXT, tickers_json TEXT,
  source TEXT, url TEXT
);
CREATE TABLE market_summary (      -- 전체 시장 2문장 요약 (최신 1행 유지)
  id INTEGER PRIMARY KEY CHECK (id = 1),
  ts TEXT, summary_ko TEXT
);

-- 검색 로그 & 랭킹
CREATE TABLE searches (
  ts TEXT NOT NULL,
  date TEXT NOT NULL,              -- 집계용
  ticker TEXT NOT NULL,
  user_hash TEXT                   -- 익명 해시 (선택)
);
CREATE INDEX idx_searches_date ON searches(date, ticker);

CREATE TABLE rankings (            -- 크론이 10분마다 집계해 캐시
  date TEXT NOT NULL,
  rank INTEGER,
  ticker TEXT, search_count INTEGER,
  PRIMARY KEY (date, rank)
);

-- DAU / 누적 AU
CREATE TABLE daily_users (
  date TEXT NOT NULL,
  user_hash TEXT NOT NULL,         -- SHA-256(IP + UA + date + salt)
  PRIMARY KEY (date, user_hash)
);
CREATE TABLE all_users (
  user_hash TEXT PRIMARY KEY,      -- SHA-256(IP + UA + salt) — date 미포함
  first_seen TEXT
);
CREATE TABLE stats_cache (         -- 프론트 표시용 집계 캐시
  key TEXT PRIMARY KEY,            -- 'dau' | 'total_au' | 'last_update'
  value TEXT, ts TEXT
);
```

---

## 4. API 명세 (CF Worker)

| Method | Path | 설명 | 비고 |
|---|---|---|---|
| GET | `/api/dashboard` | 시그널+스냅샷+통계 통합 1콜 | 프론트 초기 로딩용, Cache-Control 60s |
| GET | `/api/search?q=NVDA` | 종목 기본정보 + 해당 종목 시그널 | 검색 로그 D1 INSERT |
| GET | `/api/rankings` | 오늘 검색 Top 5 | rankings 캐시 테이블 읽기만 |
| GET | `/api/movers` | 급등10/급락10 | |
| GET | `/api/news?limit=10` | 최신 뉴스 요약 + 시장 요약 | |
| POST | `/api/track` | DAU/AU 기록 | 응답에 {dau, total_au} 반환 |
| POST | `/api/ingest/news` | Azure 전용 수신 | HMAC + 타임스탬프 검증, 실패 시 401 |

응답 공통 필드: `{"data": ..., "updated_at": "ISO8601", "disclaimer": true}`

---

## 5. 보안 & 시크릿 관리

```bash
# Cloudflare
wrangler secret put FINNHUB_KEY
wrangler secret put FMP_KEY
wrangler secret put INGEST_SECRET        # Azure와 공유하는 HMAC 키

# Azure (Function App 구성)
az functionapp config appsettings set ... \
  DEEPSEEK_API_KEY=... FINNHUB_KEY=... INGEST_SECRET=... CF_INGEST_URL=...
```

- 코드/레포에 키 절대 커밋 금지 (`.gitignore`에 `.dev.vars`, `local.settings.json`)
- `/api/ingest/news`: HMAC 서명 + 타임스탬프 ±5분 + (선택) Azure egress IP 화이트리스트
- 검색 API rate limit: 동일 user_hash 분당 30회 (D1 카운트 또는 단순 메모리)
- user_hash salt는 시크릿으로 관리, 원본 IP는 어디에도 저장하지 않음

---

## 6. Claude Code 작업 절차

### 6.1 사전 준비

```bash
npm install -g wrangler
wrangler login
mkdir vibe-investing-web && cd vibe-investing-web
git clone https://github.com/gameworkerkim/vibe-investing ./ref
claude
```

### 6.2 CLAUDE.md (프로젝트 루트에 배치)

```markdown
# Vibe Investing Dashboard
## 목표
ref/ 내 3개 전략(ARDS, AMQS, MU_Hynix) 대시보드를 단일 페이지로 통합

## 스택
- Cloudflare Workers (static assets + API) + D1 + R2 + Cron Trigger
- Azure Functions (Node 20, Timer): 뉴스 수집 + DeepSeek 요약 → CF ingest
- 프론트: vanilla TS + 단일 번들 (빌드: esbuild), 차트는 경량 SVG 직접 렌더

## 절대 규칙
- 무료 티어 한도 준수: KV 쓰기 금지, D1 쓰기 최소화, Worker CPU 작업 최소화
- API 키는 secret/env만, 하드코딩 금지
- LLM(DeepSeek)은 뉴스 요약 전용. 투자 조언 생성 금지
- 모든 시그널은 ref/의 룰 로직 포팅. 임의 로직 발명 금지, 불명확하면 질문할 것
- 한국어 UI 기본 + 영어 토글

## 디렉터리
/worker        CF Worker (API + cron)
/frontend      정적 프론트
/azure-news    Azure Functions
/migrations    D1 SQL
/docs          본 가이드
```

### 6.3 단계별 프롬프트 (한 번에 하나씩)

| 단계 | Claude Code 지시 | 검수 포인트 |
|---|---|---|
| 1 | "ref/ 의 ARDS, AMQS, MU_Hynix를 읽고 각 전략의 시그널 규칙·입력 데이터·출력 포맷을 docs/STRATEGY-ANALYSIS.md로 정리해줘" | 룰 해석이 원본과 일치하는지 직접 검토 |
| 2 | "wrangler.toml + migrations/0001_init.sql 생성 (본 가이드 §3 스키마)" | 스키마 본 문서와 대조 |
| 3 | "크론 워커 구현: §2.1 10분 파이프라인. 장외시간 스킵 포함" | `wrangler dev --test-scheduled`로 테스트 |
| 4 | "azure-news/ 구현: §2.2. DeepSeek 호출, HMAC 서명, 중복 스킵" | local.settings.json 샘플 확인 |
| 5 | "Worker API 구현: §4 전체 + ingest HMAC 검증" | curl로 401/200 케이스 테스트 |
| 6 | "시그널 포팅: 1단계 분석 기반으로 TS 포팅 + 단위 테스트. Python 결과와 비교용 fixture 포함" | 기존 결과와 수치 대조 |
| 7 | "프론트 구현: PART B 화면 가이드 그대로" | 모바일/데스크톱 확인 |
| 8 | "README + 배포 스크립트" | |

### 6.4 배포

```bash
# Cloudflare
wrangler d1 create vibe-investing-db
wrangler r2 bucket create vibe-snapshots
wrangler d1 migrations apply vibe-investing-db --remote
wrangler deploy

# Azure (예: Flex Consumption)
az group create -n vibe-rg -l koreacentral
az functionapp create -n vibe-news-fn -g vibe-rg ... --consumption-plan-location koreacentral
func azure functionapp publish vibe-news-fn
```

### 6.5 wrangler.toml 핵심

```toml
name = "vibe-investing"
main = "worker/src/index.ts"
compatibility_date = "2026-06-01"
assets = { directory = "./frontend/dist", binding = "ASSETS" }

[triggers]
crons = ["*/10 * * * *", "30 21 * * 1-5"]

[[d1_databases]]
binding = "DB"
database_name = "vibe-investing-db"
database_id = "<생성 후 입력>"

[[r2_buckets]]
binding = "SNAPSHOTS"
bucket_name = "vibe-snapshots"
```

---

## 7. 운영 체크리스트

- [ ] CF 대시보드에서 Worker 에러율/크론 실행 로그 주 1회 확인
- [ ] DeepSeek 비용 알림 설정 (월 상한)
- [ ] Azure Functions 실행 횟수 무료 한도 모니터링
- [ ] D1 쓰기량 80% 도달 시 검색 로그 샘플링 전환
- [ ] 시그널 결과 vs 기존 Python 스크립트 주간 대조 (첫 한 달)
- [ ] Finnhub/FMP 응답 스키마 변경 감지: 파싱 실패 시 직전 스냅샷 유지 + stale 표시
- [ ] Cloudflare Web Analytics 활성화 (보조 지표)

## 8. 면책 문구 (푸터 고정)

```
⚠️ 본 사이트의 모든 시그널은 룰 기반 백테스트 산출물이며, 투자 자문이나
매수·매도 권유가 아닙니다. 투자의 책임은 전적으로 투자자 본인에게 있습니다.
데이터는 지연·오류가 있을 수 있습니다.
This is not investment advice. All signals are rule-based research outputs.
Data may be delayed or inaccurate. Source: github.com/gameworkerkim/vibe-investing
```

---
---

# PART B. 화면 가이드

## 1. 디자인 방향

- **콘셉트**: "터미널 그레이드 리서치 데스크" — Bloomberg/거래 터미널의 밀도 + 에디토리얼 리서치 노트의 신뢰감. 장난감 같은 핀테크 앱 느낌 배제.
- **테마**: 다크 기본 (시세 화면 표준), 라이트 토글 제공
- **폰트**:
  - 숫자/티커: 모노스페이스 — `IBM Plex Mono` 또는 `JetBrains Mono` (탭ular figures 필수)
  - 본문/한글: `Pretendard` (한글 가독성 최우선)
  - 디스플레이(로고/섹션 제목): `Archivo` 계열 컨덴스드
- **금지**: Inter/Roboto, 보라색 그라데이션, 카드 그림자 남발

### 1.1 컬러 토큰 (CSS Variables)

```css
:root {
  --bg:        #0B0E14;   /* 메인 배경 */
  --surface:   #121722;   /* 카드/패널 */
  --line:      #1F2735;   /* 구분선 */
  --text:      #E6EAF2;
  --text-dim:  #8A94A6;

  --up:        #F0524D;   /* 상승/매수 — 한국식 적색 (확정) */
  --down:      #4C8DF5;   /* 하락/매도 — 한국식 청색 */
  --hold:      #8A94A6;   /* 보유 — 중립 회색 */
  --risk:      #F5A623;   /* 단기하락 경고 — 앰버 */
  --surge:     #FF2E92;   /* 급등 — 마젠타 (상승 적색과 명확히 구분) */

  --accent:    #F5A623;   /* 브랜드 포인트 (경고색과 통일감) */
}
```

> ✅ 확정: **한국식(적=상승, 청=하락)** 채택. 미국 시장 데이터지만 주 사용자가
> 한국인이므로 한국 관습 우선. 토큰 값만 교체하면 미국식 전환 가능하게 구현.
> 첫 방문 시 "적색=상승" 안내 툴팁 1회 노출 (해외 방문자 대비).

### 1.2 시그널 배지 규격

| 시그널 | 라벨 | 색 | 모양 |
|---|---|---|---|
| BUY | 매수 | --up | 채움 배지 |
| SELL | 매도 | --down | 채움 배지 |
| HOLD | 보유 | --hold | 아웃라인 배지 |
| SHORT_TERM_RISK | 단기하락 주의 | --risk | 채움 + ⚠ 아이콘 |
| SURGE | 급등 | --surge | 채움 + ▲ 아이콘 |

배지에는 항상 산출 날짜를 작게 병기: `매수 · 06/05 기준`

---

## 2. 페이지 레이아웃 (단일 페이지, 데스크톱 1200px 기준)

```
┌────────────────────────────────────────────────────────────────┐
│ [A] 헤더                                                        │
│  VIBE INVESTING ▮          [검색 ____________ 🔍]  [KO/EN] [☾]  │
│  마지막 갱신: 06-06 09:40 KST · 다음 갱신 ~7분 후               │
├────────────────────────────────────────────────────────────────┤
│ [B] 시장 상황 다이어그램 (전폭)                                  │
│ ┌──────────────┐ ┌───────────────────────────┐ ┌─────────────┐ │
│ │ 시장 온도계   │ │ 섹터 히트맵 (11 타일)      │ │ 지수 스파크  │ │
│ │ Risk-On ◄─►  │ │ 면적=시총, 색=등락         │ │ QQQ SPY VIX │ │
│ │ Risk-Off 게이지│ │                          │ │ 미니 라인    │ │
│ └──────────────┘ └───────────────────────────┘ └─────────────┘ │
│  └ AI 시장 요약 2문장 (DeepSeek, "요약: ..." 라벨 명시)          │
├────────────────────────────────────────────────────────────────┤
│ [C] 전략 시그널 (3열 카드)                                      │
│ ┌─ ARDS ────────┐ ┌─ AMQS ────────┐ ┌─ MU/Hynix ────┐         │
│ │ QQQ   [매수]   │ │ NVDA  [보유]   │ │ MU [단기하락⚠]│         │
│ │ 방어모드: OFF  │ │ AVGO  [매도]   │ │ 000660 [보유] │         │
│ │ 주요지표 3개   │ │ ...           │ │ ...           │         │
│ │ [상세/레포→]   │ │ [상세/레포→]   │ │ [상세/레포→]   │         │
│ └───────────────┘ └───────────────┘ └───────────────┘         │
├────────────────────────────────┬───────────────────────────────┤
│ [D] 나스닥 급등 TOP 10         │ [E] 나스닥 급락 TOP 10         │
│  1 XXXX +18.2%  ...            │  1 YYYY -15.4%  ...           │
├────────────────────────────────┴───────────────────────────────┤
│ [F] 주요 경제 뉴스 요약 (1일 9회 갱신 · 다음 갱신 시각 표시)     │
│  [거시] 제목 — 1문장 요약 · 출처 · 시간                          │
│  [반도체] ...                                          (10건)   │
├──────────────────────────────┬─────────────────────────────────┤
│ [G] 인기 검색 TOP 5 (오늘)    │ [H] 사이트 통계                  │
│  1 NVDA (142회) ...          │  DAU 1,024 · 누적 AU 18,402      │
├──────────────────────────────┴─────────────────────────────────┤
│ [I] 푸터: 레포 링크 3종 · 면책 경고(전문) · ORCID · 저작권       │
└────────────────────────────────────────────────────────────────┘
```

### 모바일 (≤768px)
세로 단일 컬럼, 순서: A → B(온도계+히트맵 축소) → C(가로 스와이프 카드) → D/E(탭 전환)
→ F → G/H → I. 검색은 헤더 아이콘 → 풀스크린 오버레이.

---

## 3. 섹션별 상세 스펙

### [A] 헤더
- 로고: 텍스트 로고 + 커서 블링크(▮) 모션 1회
- **갱신 표시**: `stats_cache.last_update` 기반. 20분 이상 경과 시 앰버로
  `⚠ 데이터 지연 중` 표시 (stale 상태 명시 — 신뢰성 핵심)
- 검색: 티커/회사명 자동완성 (정적 심볼 리스트 번들, 서버 호출 없이 프론트 필터)

### [B] 시장 다이어그램
- **온도계 게이지**: 0~100 단일 점수. 산식(수정 가능):
  `50 + (지수등락 가중) − (VIX z-score×10) + (상승종목비율 보정)` → Risk-Off/중립/Risk-On 3구간
- **섹터 히트맵**: 11개 SPDR 섹터 ETF. SVG treemap, 타일 클릭 → 해당 ETF 검색
- **지수 스파크라인**: 당일 10분 간격 포인트 (R2 스냅샷 히스토리에서)
- AI 요약 문장에는 반드시 `요약(AI)` 라벨 — 사실/생성 구분 표시

### [C] 전략 카드
- 카드 헤더: 전략명 + 한 줄 설명 + 산출 기준일
- 본문: 티커별 시그널 배지 리스트 (최대 6개, 이후 "더보기")
- 핵심 지표 3개 (예: ARDS → 방어모드 on/off, 추세 점수, 크라우딩 지표)
- 푸터: GitHub 해당 폴더 딥링크 + SSRN 페이퍼 링크(있는 경우)
- **단기하락 주의 시그널이 1개라도 있으면 카드 상단에 앰버 스트립**

### [D]/[E] 급등/급락
- 테이블: 순위 · 티커 · 종목명(말줄임) · 현재가 · 등락% · 거래량
- 등락%는 모노스페이스 + 색상, 행 클릭 → 검색 패널로 연결
- 데이터 시점 캡션: "06-06 09:40 기준 (프리장 포함 여부 명시)"

### [F] 뉴스 요약
- 카테고리 칩 필터: 전체 | 거시 | 실적 | 반도체 | AI | 금리 | 지정학
- 항목: `[카테고리칩] 한국어 제목 — 1문장 요약 · 원문 출처 · n분 전`
- 원문 링크는 새 탭. 요약 하단에 `요약: DeepSeek · 원문 책임은 출처에 있음` 캡션
- 헤더에 갱신 스케줄 안내: `다음 갱신 15:00 KST` (§A-2.2 스케줄 기반 계산)

### [G] 인기 검색 TOP 5
- `1. NVDA ▲ 142회` 형식, 전일 대비 순위 변동 화살표
- 빈 상태(서비스 초기): "아직 충분한 검색 데이터가 없습니다" + 인기 기본 티커 제안

### [H] 사이트 통계
- DAU / 누적 AU 두 숫자 크게, 카운트업 애니메이션 1회
- 캡션: "익명 집계 · 개인정보 미저장"

### [I] 푸터
- 3개 레포 딥링크(ARDS / AMQS / MU_Hynix) + 메인 레포 + CTI 레포(선택)
- 면책 전문 (§A-8) — 접지 않고 항상 노출
- `Built with Claude Code · Cloudflare · Azure` (선택)

### 검색 결과 패널 (오버레이)
```
┌──────────────────────────────────────────┐
│ NVDA · NVIDIA Corp            [닫기 ✕]   │
│ $XXX.XX  +X.X%   (06-06 09:40 기준)      │
│ ── 전략 시그널 ──────────────────────────│
│ AMQS: [보유]  근거: 모멘텀 점수 0.62 ...  │
│ (해당 없음 전략은 "유니버스 외" 표시)     │
│ ── 미니 차트 (30일 일봉 스파크) ─────────│
│ ⚠ 투자 조언이 아닙니다 (1줄 면책)         │
└──────────────────────────────────────────┘
```

---

## 4. 모션 & 상태 규칙

- 페이지 로드: 섹션 staggered fade-up (60ms 간격, 1회만)
- 데이터 갱신 시: 변경된 숫자만 플래시 (상승 녹/하락 적 배경 600ms)
- 로딩: 스켈레톤 (스피너 금지)
- 에러/지연: 직전 데이터 유지 + 상단 stale 배너 — 빈 화면 절대 금지
- `prefers-reduced-motion` 존중

## 5. 접근성 & 다국어

- 색상만으로 의미 전달 금지: 배지에 텍스트/아이콘 병기 (색약 대응)
- 등락 색상은 한국식(적=상승) 기본, 토큰 교체로 미국식 전환 가능하게 구현
- KO/EN 토글: UI 문자열 i18n JSON 분리, 뉴스 요약은 KO 고정(EN은 원문 링크)
- 시맨틱 마크업 + aria-live (갱신 영역)

---

## 결정 사항 트래킹 (2026-06-06 업데이트)

1. [x] 등락 색상: **한국식(적=상승, 청=하락)** 확정
2. [ ] SK하이닉스(000660) 시세 소스 — KRX 데이터 무료 소스 확정 필요 (미해결)
3. [x] 뉴스 요약: **24시간 커버, 1일 9회 KST 고정 스케줄** (§A-2.2) 확정
4. [x] 도메인: **1단계 `*.workers.dev` 무료 서브도메인**으로 런칭.
       2단계에서 `vibe-invest.com` 구매 권장 (CF Registrar $10.46/년 원가,
       레포명 `vibe-investing`과 일관, .com이 레퍼런스/인용 신뢰도 최우선).
       차선: `vibeinvest.org` (공익 리서치 톤, $8.50 첫해).
       비추천: `.uk`(영국 타깃 + 등록 요건), `.info`/`.ltd`(가격 대비 가치 낮음).
       커스텀 도메인 연결은 CF 대시보드에서 무료, 코드 변경 불필요.
5. [△] 시그널 "근거 지표" 노출: **1차 출시는 시그널+날짜만, 근거 지표는 추후 보강** (Phase 2)
6. [x] DAU 집계: **user_hash 방식** 확정 (SHA-256(IP+UA+date+salt), 원본 미저장)
