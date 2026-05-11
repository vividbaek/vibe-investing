# 증권당 — Azure → Cloudflare 전면 이전 설계 v1.0

**문서 버전**: v1.0 (2026-05-11)
**작성자**: Dennis Kim
**목적**: 아시아 서비스 확대 전 인프라 재검토. Azure(Korea Central 단일) →
Cloudflare(아시아 15+ POP) 이전을 통한 지연시간·가용성·비용 개선 검토.

Azure Free Tier + Azure Function + static page + blob의 경우 동작은 하지만, 사용성, 유저 경험을 헤치는 부분이 있어 이 부분을 cloudFlare로 이전할 경우의 장점, 플랜, 어느 정도 코드를 갈아 엎어야할지에 대해서 정리

---

## 0. 한눈에 요약

| 비교 축 | Azure 현재 | Cloudflare 이전 후 (Plan B) |
|---|---|---|
| 콜드스타트 | 750ms (PTB initialize) | **~5ms** (V8 isolate) |
| 일본·싱가포르 사용자 응답 p50 | ~250ms | **~25ms** |
| 시간당 매치업 생성 cron 지연 | 평균 6초 | **<1초** (DO alarm) |
| Mini App API edge cache | 없음 | **Workers cache + KV** |
| 월 비용 (DAU 10k 가정) | ~$15–30 | **$0–5** (Bundled 옵션) |
| 데이터 주권 / Latency | 한국 중심 | **15+ 아시아 POP 자동 분산** |

**결론**: Plan A (Workers 프록시 + Azure 백엔드 유지) 가 즉시 효과 큰 단계,
Plan B (전면 이전) 가 3–4주 작업 후 최대 효과.

---

## 1. 현재 아키텍처 (Azure)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         사용자 (한국 / 아시아)                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ Telegram     │  │ Telegram     │  │ Web 브라우저 │
        │ 봇 (chat)    │  │ Mini App     │  │ (대시보드)   │
        │ Webhook POST │  │ (WebView)    │  │              │
        └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
               │                 │ HTTPS+initData   │
               │ HTTPS           │ HMAC SHA-256     │
               ▼                 ▼                  ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Azure Static Web Apps (Korea Central)                  │
    │  ├── /miniapp/ (HTML + JS)                              │
    │  ├── /dashboard.html (admin)                            │
    │  └── /policy.html, /terms.html                          │
    └────────────────────────────┬────────────────────────────┘
                                 │ API proxy
                                 ▼
    ┌─────────────────────────────────────────────────────────┐
    │  Azure Functions Flex Consumption (Korea Central)       │
    │  Python v2 · PTB v22 (async)                            │
    │                                                          │
    │  HTTP routes (~50개):                                    │
    │   /telegram/webhook · /profile/check · /profile/onboard │
    │   /fortune/{today,unlock,reroll}                        │
    │   /matchup/{active,predict,history}                     │
    │   /single_pred/{active,predict}                         │
    │   /predictions/{create,mine,*}                          │
    │   /rankings/{predictions,referrers}                     │
    │   /donate/{info,intent,intent/{id}}                     │
    │   /saju/{profile,today,unlock}                          │
    │   /persona/{analyze,analyze_advanced}                   │
    │   /data/{ticker} · /today_market · /attend              │
    │   /dashboard_{stats,export,billing,pm_stats,*}          │
    │                                                          │
    │  Timer triggers (14개):                                  │
    │   매시간 :00 — matchup_hourly + single_pred_hourly      │
    │   30분 — prewarm + gauge × 2 (matchup + single)         │
    │   5분 — resolve × 2 + donate_verify + clicks            │
    │   KST 03:00 — ranking rebuild + reward                   │
    │   KST 04:00 — referrer milestone payout                  │
    │   KST 02:30 — predictions expire                         │
    │   KST 16:00 — predictions settle                         │
    │   매일 02:00 — hot ticker rotation                       │
    │   6 슬롯 (KST 06/08/12/15:30/21/23) — 시황 생성           │
    └────────────────────────────┬────────────────────────────┘
                                 │
        ┌────────────────────────┼──────────────────────────────┐
        │                        │                              │
        ▼                        ▼                              ▼
┌──────────────────┐ ┌─────────────────────────────┐ ┌─────────────────┐
│ Azure Blob       │ │ External APIs                │ │ Azure ARM        │
│ Storage          │ │  · DeepSeek (OpenAI-compat)  │ │  · KeyVault     │
│ (8+ containers)  │ │  · yfinance (no key)         │ │  · Managed ID    │
│                  │ │  · TonAPI / TronGrid         │ │  · Cost Mgmt API │
│ ├ users/         │ │  · CoinGecko (top 100)       │ │                  │
│ ├ predictions/   │ └─────────────────────────────┘ └─────────────────┘
│ ├ matchups/      │
│ ├ single-pred./  │
│ ├ rankings/      │
│ ├ donation-int./ │
│ ├ logs/          │
│ ├ share-cards/   │
│ ├ prewarm/       │
│ ├ matchup-mov./  │
│ ├ ticker-cache/  │
│ └ slot-reports/  │
└──────────────────┘
```

### 1.1 현재 아키텍처의 한계

| 한계 | 원인 | 영향 |
|---|---|---|
| **콜드스타트** | Flex Consumption ZIP 압축 + PTB initialize() | 첫 webhook 750ms 지연 |
| **단일 리전** | Korea Central만 사용 | 일본/싱가포르 ~150-250ms 추가 |
| **Blob 스캔** | list_blobs는 prefix 기반, 정렬 안 됨 | matchup 누적 시 3-5초 (현재 summary blob으로 완화) |
| **메모리 캐시 휘발** | Functions 인스턴스 재시작 시 cache 비움 | 매번 첫 요청 cold |
| **WebSocket 미지원** | Flex Consumption은 HTTP only | 매치업 게이지 폴링 (30s) |
| **외부 API 의존** | yfinance/TonAPI rate limit | 매시간 cron 한계 |
| **비용 가시성** | Cost Management API 별도 권한 필요 | 청구 후 비용 인지 |

---

## 2. Plan A — Workers 프록시 + Azure 유지 (즉시 효과, 1주)

> "edge에서 90% 흡수, 나머지 10%만 Azure로" — 최소 변경 + 최대 임팩트.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Cloudflare Edge (15+ 아시아 POP)                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Cloudflare Workers (TS · V8 isolate, ~5ms cold)              │  │
│  │  · DNS / TLS 종단                                              │  │
│  │  · Init-data HMAC 검증 (edge에서 인증 처리 → Azure 부하 ↓)    │  │
│  │  · 정적 응답 캐시 (Cache API) :                                │  │
│  │    /data/{ticker} (TTL 30s)                                    │  │
│  │    /today_market (TTL 60s)                                     │  │
│  │    /matchup/active (TTL 20s, locale-aware)                     │  │
│  │    /single_pred/active (TTL 20s)                               │  │
│  │    /fortune/today (TTL 60s, per-user via KV key)               │  │
│  │  · Rate limit (Workers Rate Limiting Free)                     │  │
│  │  · 지역(Country) 라우팅                                         │  │
│  └────────────────────┬─────────────────────────────────────────┘  │
│                       │                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Cloudflare Pages (정적 호스팅, unlimited bandwidth)          │  │
│  │  · /miniapp/* (HTML/JS/CSS — SWA에서 단순 복사)               │  │
│  │  · /dashboard.html                                            │  │
│  │  · /policy.html, /terms.html                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ KV (Edge cache state)                                         │  │
│  │  · anon_profile_check:<anon>  (TTL 5min)                      │  │
│  │  · session_user_key:<initdata_hash>  (TTL 1h)                 │  │
│  │  · matchup_summary:<date>  (mirror of Azure Blob, 1m write)   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │ 캐시 미스만 origin으로
                                  ▼
              ┌─────────────────────────────────────┐
              │ Azure Functions (Korea Central)     │
              │ — 모든 기존 Python 코드 그대로       │
              │ — Timer trigger도 그대로 (Cron)      │
              │ — Blob도 그대로                      │
              └─────────────────────────────────────┘
```

### 2.1 변경 항목

1. **Cloudflare Pages**: Mini App 정적 파일 그대로 배포 (1일)
2. **Cloudflare Workers**: `api.jeunggwondang.com` 도메인 → Workers로 라우팅 (1일)
3. **Workers 코드** (TypeScript): 다음 6개 핵심 핸들러만 edge에서 처리 (3-4일)
   - `/profile/check` — KV 5분 캐시 직격 (콜드 100ms → 5ms)
   - `/data/{ticker}` — KV 30초 캐시 + R2 fallback (현재 4시간 ticker-cache 그대로 활용)
   - `/today_market` — KV 60초 캐시
   - `/matchup/active`, `/single_pred/active` — KV 20초 캐시 + per-user mask 처리
   - `/fortune/today` — per-anon KV 캐시
   - 나머지 모든 요청: Azure로 reverse proxy (변경 없음)
4. **Workers Secrets**: Azure 토큰 / DeepSeek API key 등 환경변수 이전
5. **DNS** Cloudflare로 이전 (이미 Cloudflare 사용 중일 수 있음)

### 2.2 효과

| 메트릭 | 변경 전 | 변경 후 |
|---|---|---|
| `/profile/check` p50 (서울) | 80ms | **5ms** |
| `/profile/check` p50 (싱가포르) | 220ms | **15ms** |
| `/matchup/active` p50 (도쿄) | 150ms | **20ms** |
| Azure Functions 호출량 | 100% | **~10%** (90% edge hit) |
| 월 Azure 비용 (DAU 10k) | $20 | **$3** (Functions 호출량 1/10) |
| 월 Cloudflare 비용 | $0 | **$0** (Workers Free 100k req/day) |

### 2.3 위험 / 한계

- **HMAC 검증 분기**: Workers가 init-data 검증 → user_key를 Azure로 전달 시 신뢰 체인 필요 (서명된 헤더 추가)
- **캐시 무효화**: 매치업 게이지 30분 갱신 / fortune unlock 후 캐시 evict 메커니즘 필요 (KV `put` with TTL 또는 `delete` 명시 호출)
- **트래픽 폭증**: Free 100k req/day는 DAU ~3k 안전선. Bundled $5/mo로 10M/mo (DAU 30k+)

---

## 3. Plan B — Cloudflare 전면 이전 (3-4주 작업, 최대 효과)

> Python 전체를 TypeScript Workers로 재작성. R2/D1/DO 본격 활용.

```
┌─────────────────────────────────────────────────────────────────────┐
│              Cloudflare Edge — 15+ 아시아 POP                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Pages (Mini App + Dashboard)                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Workers (TypeScript, ~5ms cold)                               │  │
│  │  ├ apps/api/* — 50개 HTTP route                                │  │
│  │  ├ apps/bot/* — Telegram webhook + PTB-like state machine     │  │
│  │  └ apps/persona/* — DeepSeek 호출 (외부 HTTP)                  │  │
│  └────────────┬───────────────┬───────────────┬─────────────────┘  │
│               │               │               │                      │
│               ▼               ▼               ▼                      │
│  ┌──────────────┐  ┌─────────────────┐  ┌─────────────────────┐    │
│  │ D1 (SQLite)  │  │ R2 (Object)     │  │ Durable Objects     │    │
│  │  · users     │  │  · share-cards/ │  │  · MatchupHour      │    │
│  │  · profiles  │  │  · slot-reports │  │    (per-hour state) │    │
│  │  · predict.  │  │  · prewarm/     │  │  · SinglePredHour   │    │
│  │  · rankings  │  │  · logs/        │  │  · UserSession      │    │
│  │  · matchups  │  │  · brag-cards   │  │  · LiveGauge        │    │
│  │  · invites   │  │                 │  │    (WS push)        │    │
│  │  · donations │  │                 │  │                     │    │
│  └──────────────┘  └─────────────────┘  └─────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ KV (Hot reads)                                                │  │
│  │  · ticker-price:<ticker>  (30s)                                │  │
│  │  · hot-tickers (1h)                                            │  │
│  │  · session:<initdata>  (1h)                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Cron Triggers (Workers Scheduled)                             │  │
│  │  · 매시간 :00 — matchup + single_pred 생성                     │  │
│  │  · 30분 — gauge refresh × 2                                   │  │
│  │  · 5분 — resolve × 2 + donate verify + click aggregate         │  │
│  │  · KST 02-04 — ranking + milestone + expire                    │  │
│  │  · KST 06/08/12/15:30/21/23 — 6 슬롯 시황                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
              ┌───────────────────┼──────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌────────────┐   ┌────────────────┐   ┌────────────────┐
       │ DeepSeek   │   │ TonAPI         │   │ Yahoo Finance  │
       │ Chat API   │   │ + TronGrid     │   │ (yfinance      │
       │            │   │                │   │  대체 → CF     │
       │            │   │                │   │  Workers fetch │
       │            │   │                │   │  + 캐시)        │
       └────────────┘   └────────────────┘   └────────────────┘
```

### 3.1 마이그레이션 매핑

| Azure 서비스 | Cloudflare 대체 | 변경 작업 |
|---|---|---|
| Functions HTTP (Python) | Workers (TypeScript) | 전면 재작성 — 약 4000줄 |
| Functions Timer | Workers Cron Triggers | 14개 timer 그대로 이전 |
| Static Web App | Pages | 정적 파일 그대로 |
| Blob Storage | R2 (객체) + D1 (구조화) | 8 container → R2 3 bucket + D1 12 table |
| Managed Identity / KeyVault | Workers Secrets | 환경변수 형식 (1회 셋업) |
| App Insights | Workers Analytics Engine | 무료 1억 이벤트/월, KQL→SQL |
| Cost Management | Cloudflare Dashboard | 단순화 (R2/Workers Free) |
| In-process memory cache | KV (TTL) + Cache API | 별도 설계 필요 |

### 3.2 Python → TypeScript 재작성 주요 모듈

| 모듈 | 줄 수 (현재) | 재작성 난이도 | 핵심 의존성 |
|---|---|---|---|
| `saju_engine` | 350 | ★ 낮음 | 순수 함수, 60갑자 계산 |
| `fortune_match` | 130 | ★ 낮음 | SHA-256 + 결정론 |
| `stock_classifier` | 220 | ★ 낮음 | dict 기반 분류 |
| `stock_recommender` | 150 | ★ 낮음 | CSV → D1 마이그레이션 |
| `matchup_service` | 600 | ★★ 중 | Blob → D1 + R2 |
| `single_pred_service` | 480 | ★★ 중 | Blob → D1 + R2 |
| `prediction_repo` | 240 | ★ 낮음 | D1 SQL |
| `prediction_settler` | 140 | ★ 낮음 | yfinance HTTP fetch |
| `ranking_builder` | 250 | ★★ 중 | Wilson score (math.sqrt) |
| `donation_service` | 600 | ★★ 중 | Blob → D1, HTTP 그대로 |
| `chain_clients` | 200 | ★ 낮음 | fetch + JSON |
| `persona_engine` | 380 | ★★★ 높음 | DeepSeek streaming, 4국어 |
| `brag_card_service` | 350 | **★★★★ 최고** | Pillow → @vercel/og (HTML→PNG) |
| `bot/telegram_handler` | 2000+ | ★★★ 높음 | PTB → grammY (TS) |

### 3.3 데이터 모델 변환 — Blob → D1 (SQLite at edge)

```sql
-- D1 스키마 (요약)
CREATE TABLE users (
  user_key TEXT PRIMARY KEY,
  anon_user_id TEXT NOT NULL UNIQUE,
  persona_key TEXT NOT NULL DEFAULT 'buffett',
  language TEXT NOT NULL DEFAULT 'ko',
  points_balance INTEGER NOT NULL DEFAULT 0,
  points_cumulative INTEGER NOT NULL DEFAULT 0,
  tier TEXT NOT NULL DEFAULT 'bronze',
  saju_birth_date TEXT,
  saju_birth_hour INTEGER DEFAULT -1,
  donation_total_usdt REAL DEFAULT 0,
  invited_by_anon TEXT,
  invite_validated_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_users_anon ON users(anon_user_id);
CREATE INDEX idx_users_invited_by ON users(invited_by_anon);

CREATE TABLE predictions (
  id TEXT PRIMARY KEY,
  user_key TEXT NOT NULL REFERENCES users(user_key),
  ticker TEXT NOT NULL,
  direction TEXT NOT NULL,  -- 'up'|'down'
  status TEXT NOT NULL,      -- 'pending'|'settled'|'no_data'
  created_price REAL NOT NULL,
  target_date TEXT NOT NULL,
  result TEXT,
  click_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  settled_at TEXT
);
CREATE INDEX idx_predictions_user ON predictions(user_key);
CREATE INDEX idx_predictions_status_target ON predictions(status, target_date);

CREATE TABLE matchups (
  id TEXT PRIMARY KEY,
  kst_date TEXT NOT NULL,
  hour INTEGER NOT NULL,
  type TEXT NOT NULL,        -- 'ss'|'cc'|'sc'
  premium_only INTEGER NOT NULL DEFAULT 0,
  asset_a_ticker TEXT, asset_a_anchor REAL,
  asset_b_ticker TEXT, asset_b_anchor REAL,
  status TEXT NOT NULL,
  winner TEXT
);
CREATE INDEX idx_matchups_date_hour ON matchups(kst_date, hour);

CREATE TABLE matchup_predictions (
  matchup_id TEXT NOT NULL REFERENCES matchups(id),
  user_key TEXT NOT NULL,
  side TEXT NOT NULL,
  submitted_at TEXT NOT NULL,
  PRIMARY KEY (matchup_id, user_key)
);
-- ... 나머지 9 테이블도 동일 패턴
```

**핵심 이점**:
- Blob `list_blobs` (O(N) 스캔) → SQL `WHERE` (인덱스 활용 O(log N))
- 매치업 history 24시간 그리드 — 단일 SQL 쿼리로 즉시
- Ranking Wilson score — `SELECT user_key, SUM(...) GROUP BY user_key`

### 3.4 Durable Objects 활용

```typescript
// 시간당 매치업 상태 = 1 Durable Object instance
// 모든 사용자가 같은 DO를 hit → consistency 보장 + WebSocket 푸시 가능

export class MatchupHour extends DurableObject {
  async fetch(req: Request) {
    // /gauge → 30s마다 yfinance fetch 후 storage에 캐시
    // /submit → DB write + 같은 시간 다른 사용자에게 WS broadcast
  }
  async alarm() {
    // KST :00 — 새 매치업 10개 생성, broadcast '새 hour 시작'
  }
}
```

**효과**: 매치업 게이지가 사용자 폴링이 아닌 WS 푸시로 즉시 갱신 → "1시간 후 결산
직전 누가 이기고 있는지" 실시간 표시 가능.

### 3.5 비용 시뮬레이션

DAU 10k, 사용자당 50 API call, 100KB 데이터 가정:
- 총 일일 요청: **500k**
- 총 월 요청: **15M**

| 자원 | Free 한도 | 사용량 | 초과분 |
|---|---|---|---|
| Workers req | 100k/일 | 500k/일 | $0 (Bundled 10M/mo $5) |
| Workers CPU | 10ms/req | 평균 3ms | 안전 |
| D1 read | 5M/일 | 2M/일 | 무료 |
| D1 write | 100k/일 | 50k/일 | 무료 |
| R2 storage | 10GB | 2GB (현재) | 무료 |
| R2 Class A | 1M/월 | 100k/월 | 무료 |
| R2 egress | 무제한 | — | **무료** (Azure 30%) |
| KV read | 100k/일 | 80k/일 | 무료 |
| Pages bandwidth | 무제한 | — | 무료 |
| DO req | 1M/일 | 200k/일 (게이지) | 무료 |
| Analytics Engine | 100M/월 | 5M/월 | 무료 |

**합계**: $0/월 (Bundled 가입 시 $5/월) **— Azure $20 대비 75-100% 절감**.

---

## 3.6 ★ Plan A+ 하이브리드 — Chat API/실시간 → Workers, Batch → Azure

> 외부 검토 의견 반영. Plan A의 "캐시 hit률" 관점에서 **"실시간 vs 배치"
> SLA 관점**으로 재분류하면 결정이 더 명확하다.

### 핵심 통찰

> "사용자 경험에 직접 영향을 주는 **실시간 Chat API**는 반드시 Workers로.
> 백그라운드 **배치 (timer cron)** 는 Azure에 남겨도 무방."

Plan A (단순 프록시)의 한계: 캐시 hit률이 90%여도 **cache miss 10% (= persona
분석 등 사용자가 직접 기다리는 호출)** 가 여전히 Azure cold start 750ms를
탄다. 이게 가장 자주 사용자가 짜증나는 순간 — 새 종목을 분석 요청한 직후.

### 분류 매트릭스 — 어떤 endpoint를 어디로?

| Endpoint | 분류 | 위치 (Plan A+) | 이유 |
|---|---|---|---|
| `POST /telegram/webhook` | 실시간 | **Workers (grammY)** | 모든 사용자 진입점, cold 절대 안 됨 |
| `POST /persona/analyze` | **실시간 Chat** | **Workers** | DeepSeek HTTP, 외부 fetch + 후처리만, TS 포팅 쉬움 |
| `POST /persona/analyze_advanced` | **실시간 Chat** | **Workers** | 3 페르소나 병렬 fetch, gather() → Promise.all() |
| `POST /matchup/predict` | 실시간 | **Workers** | UI 즉시 응답 필요 |
| `POST /single_pred/predict` | 실시간 | **Workers** | 동일 |
| `POST /predictions/create` | 실시간 | **Workers** | 동일 |
| `POST /fortune/unlock` | 실시간 | **Workers** | 동일 |
| `POST /profile/onboard` | 실시간 | **Workers** | 사용자 첫 진입 |
| `GET /profile/check` | 실시간 | **Workers + KV** | 콜드스타트 회피 핵심 |
| `GET /data/{ticker}` | 실시간 (캐시) | **Workers + KV** | 30s cache |
| `GET /today_market` | 실시간 (캐시) | **Workers + KV** | 60s cache |
| `GET /matchup/active` | 실시간 (캐시) | **Workers + KV** | 20s cache |
| `GET /single_pred/active` | 실시간 (캐시) | **Workers + KV** | 20s cache |
| `GET /fortune/today` | 실시간 (캐시) | **Workers + KV** | per-user 60s |
| `GET /rankings/{kind}` | 실시간 (캐시) | **Workers + KV** | 5min cache |
| `GET /predictions/mine` | 실시간 | **Workers (D1 read)** | 사용자별, 인덱스로 빠름 |
| `GET /matchup/history` | 실시간 (캐시) | **Workers + KV** | 2min cache |
| ─── 배치 / 무거운 작업 ─── | | | |
| Timer `매시간 :00` 매치업 생성 | 배치 | **Azure (Cron)** | yfinance fetch + Blob 쓰기, 30초 가능 |
| Timer `매시간 :00` 단일 생성 | 배치 | **Azure (Cron)** | 동일 |
| Timer `30분` gauge 갱신 | 배치 | **Azure (Cron)** | yfinance N개 병렬, ~10초 |
| Timer `5분` resolve | 배치 | **Azure (Cron)** | yfinance + point ledger 쓰기 |
| Timer `5분` donate verify | 배치 | **Azure (Cron)** | TonAPI / TronGrid 폴링 |
| Timer `KST 03:00` ranking rebuild | 배치 | **Azure (Cron)** | 전체 사용자 스캔, 1분+ |
| Timer `KST 04:00` milestone payout | 배치 | **Azure (Cron)** | 30일 holding 정산 |
| Timer `KST 06/08/12/15:30/21/23` 시황 | 배치 | **Azure (Cron)** | DeepSeek × 4국어 × 3 페르소나 = 12 LLM call |
| Timer `4시간` prewarm 252 ticker × 600 commentary | 배치 | **Azure (Cron)** | 가장 무거운 LLM 워밍업 |
| **Pillow brag card 생성** | 배치 | **Azure (도구상자)** | Pillow Python only, Workers 불가 |

### 데이터 위치

| 데이터 | 위치 | 이유 |
|---|---|---|
| 사용자 프로필 (D1 schema) | **D1** | SQL 인덱스, 빠른 lookup |
| 핫 캐시 (profile_check, ticker price) | **KV** | edge 분산, TTL |
| 매치업/단일 summary blob | **R2** | 큰 JSON, Workers/Azure 양쪽 read |
| 자랑 카드 PNG | **R2 + Azure 둘 다** | 생성=Azure, 서빙=Workers→R2 미러 |
| 로그 NDJSON | **R2** | append-only, Azure batch가 write |
| 슬롯 시황 리포트 | **R2** | Azure가 생성, Workers가 read+cache |

### Workers ↔ Azure 통신 계약

```typescript
// Workers → Azure (배치 트리거)
POST https://func-aiinvestor-prod.azurewebsites.net/api/internal/cron/<name>
Headers:
  X-Internal-HMAC: <hmac-sha256(secret, body)>
  X-Internal-Source: cf-worker
Body: { trigger_name, kst_now, params }
```

```typescript
// Azure → R2 (write summary)
PUT /matchup-summary/2026-05-11.json
Authorization: Bearer <S3-compatible-creds>
Body: <aggregated JSON>
```

```typescript
// Workers → R2 (read summary, then KV cache)
const cached = await env.KV.get(`matchup_sum:${date}`);
if (cached) return JSON.parse(cached);
const obj = await env.R2.get(`matchup-summary/${date}.json`);
const text = await obj.text();
ctx.waitUntil(env.KV.put(`matchup_sum:${date}`, text, {expirationTtl: 60}));
return JSON.parse(text);
```

### Plan A+ 작업 타임라인 (외부 의견 기반 정제)

| Phase | 기간 | 작업 |
|---|---|---|
| **준비** | 3일 | persona_engine 모듈 분석 / TS 포팅 식별 / API 계약 정의 |
| **Workers Chat API** | 1주 | TS 포팅 (persona_engine, 사주, 매치업, 단일) + DeepSeek streaming + Workers Secrets |
| **Azure Cron 정리** | 3일 | HTTP 트리거 제거 (실시간만) → Timer만 잔류, Workers가 HMAC으로 internal cron 호출 |
| **통합 테스트** | 3일 | dev 환경 e2e + Telegram 봇 cutover + 24h 모니터링 |
| **합계** | **약 2.5주** | Plan A(1주) 와 Plan B(3-4주) 사이 |

### Plan A+ 비교 우위

| 평가 축 | Plan A (단순) | **Plan A+ 하이브리드** | Plan B (전면) |
|---|---|---|---|
| 사용자 체감 (실시간) | 캐시 hit만 빠름 | **모든 실시간 빠름** | 전부 빠름 |
| 콜드스타트 영향 | persona_analyze 등 OK | **모두 회피** | 모두 회피 |
| Pillow / yfinance 처리 | Azure 그대로 | **Azure 도구상자** | 재구현 필요 |
| 작업 기간 | 1주 | **2.5주** | 3-4주 |
| 운영 복잡도 | Azure full + Workers | **Azure batch + Workers main** | Cloudflare 단일 |
| Azure 비용 절감 | 80% | **70%** (cron 유지) | 100% |
| 향후 Plan B 전환 | 추가 작업 큼 | **점진 가능** | 종료 |

### Plan A+ 위험과 완화

- **Workers → Azure cron 호출 신뢰성**: HMAC + retry + idempotency key
- **Workers/Azure cron 충돌**: Azure Timer만 사실상 신뢰원 (Workers는 트리거만)
- **Pillow brag card 지연**: 자랑 카드는 비-실시간이므로 OK (생성 후 push 알림)
- **D1 + Azure SQLite 동기화**: 사용자 데이터 dual-write 1주 후 D1 단독

---

## 4. 세 안 비교 — 어느 쪽?

| 평가 축 | Plan A (Proxy) | **Plan A+ (하이브리드)** | Plan B (전면) |
|---|---|---|---|
| 작업 기간 | 1주 | **2.5주** | 3-4주 |
| 위험도 | 낮음 (롤백 쉬움) | **낮음-중** (단계 가능) | 중 (Python 재작성) |
| 실시간 API 개선 | 캐시 hit만 | **모든 실시간 5ms** | 모든 API 5ms |
| 콜드스타트 영향 | 비-캐시 경로 잔존 | **완전 회피** | 완전 회피 |
| Chat API 응답 (페르소나 분석) | Azure cold 750ms | **Workers 5ms + DeepSeek** | Workers 5ms |
| 월 Azure 비용 | $3 (호출 90%↓) | **$3-5** (배치만) | $0 |
| 월 Cloudflare 비용 | $0 | $0 | $0-5 |
| 운영 복잡도 | 두 시스템 병행 | **두 시스템, 역할 분리 명확** | Cloudflare 단일 |
| Pillow brag card | Azure (그대로) | **Azure 도구상자 (그대로)** | @vercel/og 재구현 필요 |
| yfinance | Azure (그대로) | **Azure 배치 (그대로)** | Workers fetch + 캐시 재설계 |
| Python 자산 활용 | 100% | **80% (실시간만 TS 포팅)** | 0% |

### 추천 경로 — **Plan A+ 하이브리드로 직행** (외부 의견 채택)

```
[현재 Azure] ───2.5주───> [Plan A+ 하이브리드] ────[선택]────> [Plan B 전면]
                          • 실시간 → Workers           • Pillow/yfinance도 TS
                          • 배치 → Azure               • Azure 완전 폐기
                          • 사용자 체감 100%↑          • $0/월
                          • 비용 80%↓                  • 6개월~1년 후 검토
```

### 왜 Plan A보다 Plan A+가 더 나은가

- Plan A는 **캐시 hit률 90%** 기준 비교지만, 캐시 miss 10%가 곧 **persona
  analyze 등 사용자가 직접 기다리는 호출**이다. 정확히 가장 짜증나는 순간에
  Azure cold 750ms를 탄다.
- Plan A+는 **"실시간/배치" 분리** 기준이라 cache 여부와 무관하게 사용자
  대기 경로는 모두 Workers (5ms + 외부 API). 사용자 체감 100% 개선.
- Plan B 대비 작업 부담 50% — Pillow / yfinance처럼 어려운 부분은 Azure에
  그대로 두고 점진 이전.

### Plan A+ 실행 단계 (외부 검토 의견 + 본 문서 합본)

**Phase 1 — 준비 (3일)**
- [ ] persona_engine 모듈 분석 + TS 포팅 식별
- [ ] Workers ↔ Azure HMAC 계약 정의 (`X-Internal-HMAC` 헤더)
- [ ] D1 schema 초안 (users / predictions / matchups / matchup_predictions)
- [ ] R2 bucket 설계 (share-cards, summary, logs)
- [ ] KV namespace 설계 (profile_check, session, ticker_price, matchup_sum)

**Phase 2 — Workers 실시간 구축 (1주)**
- [ ] Cloudflare Pages: `static_web/` 배포 (1일)
- [ ] Workers 프로젝트 셋업 + Secrets 등록 (DeepSeek key, Telegram token)
- [ ] persona_engine TypeScript 포팅 (DeepSeek fetch + 4국어 + disclaimer append)
- [ ] /telegram/webhook on Workers (grammY 사용) — Telegram 봇 진입점
- [ ] /persona/analyze + /persona/analyze_advanced — DeepSeek streaming
- [ ] /predict, /fortune/unlock, /matchup/predict, /single_pred/predict — 실시간 쓰기 경로
- [ ] /profile/check, /data/ticker, /today_market 등 read 경로 + KV cache

**Phase 3 — Azure 배치 정리 (3일)**
- [ ] Azure Functions의 HTTP route 모두 제거 (Timer만 잔류)
- [ ] Azure를 "internal cron + Pillow tool box"로 재포지셔닝
- [ ] Workers Cron Triggers 검토 — Azure Timer를 Workers Cron으로 옮길 수 있는지
  - 단순 cron (ranking rebuild 같은 D1만 건드리는 것) → Workers Cron 즉시 가능
  - yfinance batch / Pillow / DeepSeek prewarm → Azure 유지

**Phase 4 — 통합 테스트 & cutover (3일)**
- [ ] dev 환경에서 Workers ↔ Azure HMAC e2e
- [ ] DNS TTL 낮춤 (60s) → cutover
- [ ] Telegram BotFather에서 webhook URL → Workers로 변경
- [ ] 24h 모니터링 (Workers Analytics + Azure App Insights 병행)
- [ ] 롤백 계획 (DNS 한 줄 변경으로 즉시 원복)

---

## 5. Asia 확대 시 추가 고려사항

### 5.1 지역별 KV namespace 분리

Cloudflare KV는 전역 자동 복제. 하지만 D1은 **현재 단일 region**.
- D1 Read Replication (beta) 활용 → 아시아 4개 region (Tokyo, Singapore, Seoul, Sydney)
- Write는 leader (Tokyo) → eventually consistent (1-2초)

### 5.2 결제 / 후원 region 차등

- TON Wallet — 글로벌 (POP 무관)
- TRON USDT — 중국·아시아 사용자 친숙도 ↑
- 한국 사용자 추가 옵션: Toss / 카카오페이 (KSP 게이트웨이 연동 별도 검토)

### 5.3 컴플라이언스

- **일본**: 자금결제법 — 후원 USDT 받기는 OK, 환금형은 라이선스 필요
- **싱가포르**: MAS 가이드라인 — 디지털자산 서비스 라이선스 검토
- **한국**: 가상자산 사업자 신고 (현재는 Telegram WebApp 기반 후원으로 회피 가능)

### 5.4 다국어 LLM 비용 최적화

DeepSeek 4국어 모두 한 모델 — 비용 변화 없음.
프롬프트 캐싱은 Cloudflare AI Gateway로 통합 (DeepSeek 응답 24h cache).

---

## 6. 실행 체크리스트

### Phase A (1주) — Plan A 실행

- [ ] Cloudflare 계정 생성 + DNS 이전
- [ ] Cloudflare Pages — `static_web/` 그대로 배포 (5분)
- [ ] Workers 프로젝트 셋업 (`wrangler init`)
- [ ] HMAC 검증 함수 TS 포팅 (1시간)
- [ ] 6 핵심 API edge cache 구현 (3일)
- [ ] Pages 사용자 정의 도메인 `app.jeunggwondang.com`
- [ ] Workers `api.jeunggwondang.com` 라우팅 → Azure origin
- [ ] 모니터링: Workers Analytics + Azure App Insights 병행
- [ ] DNS TTL 낮춤 (1시간 → 60초) 후 cutover

### Phase B (검증 후 3주) — Plan B 전환

- [ ] D1 schema 작성 + 마이그레이션 스크립트 (Python → SQL bulk insert)
- [ ] **Dual-write 1주**: Azure Blob + D1 동시 기록, read는 D1 우선
- [ ] 6 모듈 TypeScript 재작성 우선순위:
  - week 1: fortune_match, fortune_service, saju_engine, prediction_repo
  - week 2: matchup_service, single_pred_service, ranking_builder
  - week 3: donation_service, persona_engine, telegram_handler
- [ ] @vercel/og로 brag_card 재구현
- [ ] DO `MatchupHour` 구현 + WS 클라이언트
- [ ] Azure Functions 단계적 폐기 (cron 우선, HTTP는 마지막)
- [ ] Cost Management 위젯 → Cloudflare Dashboard로 교체

---

## 7. 결론 (외부 검토 의견 통합)

### 최종 추천 — **Plan A+ 하이브리드로 직행**

외부 LLM 검토 의견의 핵심 통찰 채택:
> "사용자 경험에 직접 영향을 주는 실시간 Chat API는 반드시 Workers로,
> 백그라운드 배치는 Azure에 남겨도 무방."

이 분류 기준이 Plan A의 "캐시 hit률" 기준보다 **사용자 체감 측면에서 더
직관적이고 효과 큰** 접근이다. 캐시 miss 10%가 곧 persona 분석 등 가장
짜증나는 순간이라는 점이 결정적.

### 단계 권장

| 단계 | 기간 | 결정 사항 |
|---|---|---|
| **A+** | **2.5주 (즉시 시작)** | 실시간 → Workers, 배치 → Azure |
| 검증 6개월 | — | 사용자 만족도 + 비용 + Pillow 대체 가능성 |
| **B로 전환** | 추가 2주 (선택) | Pillow → @vercel/og, yfinance → Workers fetch |

### 예상 ROI (DAU 10k 6개월 기준)

| 시나리오 | 인프라 비용/년 | 사용자 체감 | 운영 복잡도 |
|---|---|---|---|
| Azure 유지 | $120 + 한국 외 latency 손실 | 한국 OK / 아시아 부족 | 단일 |
| Plan A (proxy) | $18 | 캐시 hit만 빠름, persona 분석 느림 | 중간 |
| **Plan A+ (하이브리드)** | **$36–60** (Azure 배치만) | **모든 실시간 5ms, 어디서나** | **중간, 역할 분리 명확** |
| Plan B (전면) | $0–60 | 전부 5ms + WebSocket | 단일 (Cloudflare) |

### 위험 / 완화

| 위험 | Plan A+에서의 완화 |
|---|---|
| Pillow brag card 복잡도 | Azure 도구상자로 유지 — 우회 |
| yfinance Workers 호출 안정성 | Azure batch가 4시간마다 R2 mirror → Workers는 R2 read |
| Workers ↔ Azure 신뢰 체인 | HMAC + retry + idempotency key (Workers Secrets) |
| DeepSeek streaming (Workers) | Workers는 SSE 지원, fetch streaming OK |
| D1 단일 region (현재) | 초기는 Tokyo, Asia POP read replica (beta) 활성화 |

### 다음 결정 사항

**Q1**: Plan A+ 즉시 시작? (2.5주 작업, 외부 의견 + 본 문서 합본 plan)
**Q2**: 작업 우선 모듈 — persona_engine (Chat API)부터? 아니면 /profile/check (cache miss 최다)부터?
**Q3**: D1 Tokyo region 단일 시작 vs Asia 4-region read replica 즉시 활성화?

---

## 8. 외부 검토 의견 — 비교 분석 (참고)

본 문서 작성 후 별도 LLM의 의견을 검토했고, 두 가지 점에서 본 문서가 보완되었다:

### 채택한 점

1. **"실시간 vs 배치" 분류**가 "캐시 hit/miss" 분류보다 더 직관적이고
   사용자 체감 개선 효과가 크다 — Plan A+로 정식 채택
2. **Azure 도구상자 패턴** (Workers + Azure로 작업 위임) — Plan B의 점진
   경로로 활용
3. **Phase 1-4 타임라인** (3+7+3+3 = 약 2.5주) — 본 문서의 Plan B "3-4주"
   보다 정확한 분해

### 보완한 점

1. **외부 의견은 Plan A+를 최종 권장**으로 종결지만, 본 문서는 **Plan B로의
   점진 전환 경로**를 추가로 제시 — Asia 확대 시 D1 read replica + WebSocket
   필요성 강조
2. **외부 의견은 "Workers + Queue 기반"을 대안으로** 언급했는데, 이는 본
   문서의 Plan B 변종에 해당 — 명시적으로 두 안 다 통합
3. **데이터 모델 변환 (Blob → D1 SQL)** 세부는 본 문서가 더 상세 — 추후
   재작성 시 활용
4. **비용 시뮬레이션 (DAU 10k)** 은 본 문서가 더 정밀 — 외부 의견은 정성
   비교만

### 한 줄 합본 결론

> **Plan A+ 하이브리드로 직행 (2.5주)** → 6개월 검증 후 Asia 확대 직전
> Plan B로 전환 검토. Pillow / yfinance는 마지막까지 Azure 잔류 OK.
