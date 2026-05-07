# AI Investor — 증권당

### 앱 서비스 명
한국어 명칭 증권당
영문 명칭 AI Investor
중문 명칭 证王殿
일본어 명칭 証券堂

LLM 기반 텔레그램 봇 + Mini App. 투자 대가의 페르소나로 종목을 분석하고,
사주에 맞는 주식을 추천하며, 매시간 매치업 예측으로 자랑할 수 있는 게이미피케이션
플랫폼. 한국 retail · global 시장 모두 지원.

- **상태**: Production ([@AI_vibe_investor_bot](https://t.me/AI_vibe_investor_bot)) · Azure Functions Flex Consumption + Static Web App
- **백엔드 LLM**: DeepSeek (`deepseek-chat`) — OpenAI 호환, 1/35 비용
- **데이터**: Yahoo Finance (yfinance) · CoinGecko 호환 (top 30 crypto)
- **언어**: 한국어 / English / 日本語 / 中文 (`/lang` 또는 미니앱 4 버튼)
- **응답 속도**: hot 티커 ~1초 (commentary cache hit) / cold ticker ~5–10초
- **테스트**: 211 passing

> **Disclaimer**: 본 봇은 투자 자문이 아닙니다. 사주 분석은 일주 기준 오행
> 우세와 일진 상생/상극의 간이 결과로, 명리학의 통변을 대체하지 않습니다.
> 모든 투자 판단의 책임은 사용자에게 있습니다.

---

## ✨ 핵심 기능

| 영역 | 기능 | 진입점 |
|---|---|---|
| **페르소나 분석** | Buffett · Dalio · Wood 시각으로 종목 해설 + 고급 분석(3 페르소나 + 라이벌) | 봇 자유 입력 / 미니앱 Persona 탭 |
| **사주 추천** | 일주 기준 오행 우세 → 296종목 중 5선 (1 free / 4 잠금) · 5운(재물·사업·학업·연애·건강) · 첫 5일 무료 | 미니앱 Saju 탭 |
| **매치업 예측** | 매시간 ≥3건 (주식↔주식 / 코인↔코인 / 주식↔코인) · 전일 상승률 기반 · 30분 단위 게이지 · 정답 +30 P | 미니앱 Predict 탭 |
| **단일 자산 예측** | KOSPI / NASDAQ / TSLA / NVDA / BTC UP/DOWN · 매일 마감 시점 결산 | 미니앱 Predict 탭 |
| **포인트 게이미피케이션** | 출석 streak / 초대 보너스 / 매치업 정답 / 프리미엄 잠금 해제 | 미니앱 Home 탭 |
| **티어 시스템** | Bronze → Silver → Gold → Platinum → Diamond × 5 stage (▼▼ ~ ▲▲) · 시즌별 + 누적 | 미니앱 Home 탭 |
| **친구 초대** | 8자 invite code · ref 링크 + QR 코드 + 텔레그램 share + 4가지 share template · 초대왕 최대 1,000 USDT 리워드 | 미니앱 Invite 탭 |
| **자랑 카드** | 4종 (티어 승급 / 정확도 streak / 베팅 수익 / 스테이킹) · Pillow PNG 동적 생성 · 텔레그램 공유 +50 P | 미니앱 Rank 탭 |
| **USDT 도네이션** | TON · TRON 양 체인 USDT (1/10/50/100/500/1000) · 5분 cron 자동 검증 + tx_hash 직접 입력 fallback | 미니앱 Invite 탭 하단 |
| **시황 리포트** | 6슬롯 자동 (KST 06/08/12/15:30/21/23) · 페르소나별 캐시 | 미니앱 Home 탭 |

---

## 아키텍처

```
Telegram Bot ←─── webhook ───→ Azure Functions (Flex)
                                   │
                                   ├── Mini App (Static Web App)
                                   │     └── 6 탭: Home / Predict / Saju / Invite / Rank / Persona
                                   │
                                   ├── DeepSeek API (페르소나 + 시황)
                                   ├── yfinance (스냅샷, 매치업 mover)
                                   ├── TonAPI / TronGrid (도네이션 검증)
                                   └── Azure Blob Storage
                                         ├── users/                   프로필 (TTL 5min memory)
                                         ├── prewarm/snapshots/       252 ticker 스냅샷 (4h)
                                         ├── prewarm/commentary/      600 commentary (4h)
                                         ├── ticker-cache/            3-tier ticker price feed
                                         ├── slot-reports/            6슬롯 시황 (페르소나별)
                                         ├── matchups/                매치업 + 예측 (KST일자/시간)
                                         ├── matchup-movers/          전일 상승률 캐시 (일별)
                                         ├── donation-intents/        USDT 후원 의도 (24h TTL)
                                         ├── share-cards/             자랑 카드 PNG
                                         └── logs/                    NDJSON 사용 로그
                                   
Timer Triggers (매일 cron):
  - 06/08/12/15:30/21/23 KST: 슬롯 시황 생성
  - 30분: prewarm 갱신 + 매치업 게이지 폴링
  - 5분: 매치업 결산 + 도네이션 입금 검증
  - 매시간 :00: 매치업 ≥3건 생성 (ss/cc/sc)
  - 매일 02:00 KST: hot ticker 회전
```

---

## 작업 히스토리

> 시간순 핵심 마일스톤. 자세한 설계 문서는 [docs/](docs/) 참조.

### Phase 1 — MVP 봇 (2026-04 ~ 2026-04 중순)
- 6단계 온보딩: greeting → intro → 페르소나 → 시황 offer → 관심사 → 자유 질의
- DeepSeek 페르소나 3종 (Buffett/Dalio/Wood) + 4국어 i18n
- yfinance 스냅샷 + 5min 메모리 캐시
- 252 ticker 사전 캐싱 (4시간 cron) → cold→1.5초

### Phase 2 — Azure 이전 + Mini App 골격 (2026-04 후반)
- Azure Functions Flex Consumption + Static Web App
- Telegram WebApp init_data HMAC 인증
- 6 탭 미니앱 (Home / Predict / Invite / Rank / Persona)
- 시황 6슬롯 자동 생성 (페르소나별 블롭 캐시)
- §A4 페르소나 swap, §A5 오늘의 시황 카드, §A6 BTC auto-refresh

### Phase 3 — T2E 게이미피케이션 (Stage 1 모각)
- §T2E-A 포인트 ledger (atomic earn / spend / penalty / season rollover)
- §T2E-B 출석 + streak 보너스
- §T2E-C 친구 초대 (8자 코드 + landing → validation → zombie 추적)
- §T2E-D 티어 시스템 (5 tier × 5 stage)
- §T2E-E Mini App invite pack (링크 + QR + 4 share template + stats)
- §T2E-N 친구 1-tap value (`/start ref_X_q_NVDA_p_wood` → 즉시 추천 미리보기)
- §T2E-O 자랑 카드 (Pillow PNG · 4 종)

### Phase 4 — 사주 + 매치업 + 도네이션 (2026-05 초중반) ★ 본 작업
| 커밋 | 목적 |
|---|---|
| `4affbed` | **사주 엔진**: 60갑자 일주/일진 계산 + 5운 점수 + 296종목 오행 분류 + Mini App 사주 탭 (1 free / 4 locked, 5일 무료) |
| `bfe9208` | KOSPI 마감 14:00 / TSLA·NVDA 추가 / BTC UP-DOWN 변경 / 자랑 카드 URL 수정 / 시황 모달 |
| `b06c8ca` | **매치업 예측**: 매시간 ≥3건 (ss/cc/sc) + 30분 게이지 + 결산 cron / **도네이션**: TON·TRON USDT 검증 |
| `b585a14` | 사주 생년월일 입력 UX (date picker → 연도 숫자 + 월/일 select, 1988 기본) |
| `e0e1612` | `/start` 페르소나 키보드 제거 → 사주 후킹 메시지 + 미니앱 버튼 |
| `07e2a25` | 미니앱 4국어 언어 스위치 + 페르소나 분석 흐름 (한국 선호 15종 + 검색) + 고급 분석(3 페르소나 + 라이벌, 5일 무료) |
| `f79d191` | 매치업 마감 30분 → 55분 + 프론트가 마감 시각 체크해 410 에러 차단 |
| `4398b31` | 언어 버튼 2열 + 개인정보 처리방침 / 이용약관 정적 페이지 |
| `7bb73b4` | 도네이션 "지금 확인" 버튼 + tx_hash 직접 입력 (5분 cron 우회) |
| `805f710` | iOS safe-area-inset-bottom 반영 (탭 바 / 콘텐츠 끝 가림 수정) |
| `85be12a` | 종목 분석 응답 끝에 미니앱 + 초대 리워드 promo + 미니앱 실행 버튼 |
| `1c7321b` | `/start` 후킹 4기능 모두 노출 (페르소나 + 사주 + 예측 + 초대 리워드) |
| `3a1c060` | 도네이션 카피 세련화 + 홈 업셀 카드 (포인트 부족 시 초대/후원 유도) |
| `518c5f4` | persona 분석 캐싱 + Telegram 언어 자동 적용 + 누적 CSV (24h/7d/30d/90d/1y) + Azure 과금 위젯 |

### Phase 5 — 게이미피케이션 + 리더보드 + 유저 유입 (다음 단계, 미완)
잔여 작업은 [§ 잔여 작업 목표](#-잔여-작업-목표) 섹션 참고.

---

## 목표 (Why)

1. **AI 페르소나 + 사주 + 게이미피케이션의 융합** — 정량 분석만으로는 retail 사용자의
   "왜 이 종목을 골라야 하는가?"라는 결정 피로를 낮추기 어렵다. 페르소나는 시각의
   다양성을, 사주는 사용자 본인 서사를, 게이미피케이션은 학습/지속을 제공한다.

2. **미니앱이 메인 진입점 — 봇은 후킹 채널** — `/start`는 미니앱으로 즉시 유도하고,
   봇 채팅의 분석 응답에는 항상 "🚀 미니앱 열기" 버튼을 동봉. Telegram WebApp의
   네이티브 경험으로 사용자 잔존 시간을 늘린다.

3. **자랑할 수 있는 시스템** — 자랑 카드 + 티어 승급 + 매치업 정답 streak +
   초대 리더보드를 통해 사용자가 본인의 인사이트와 통찰을 SNS로 공유하게 만든다.
   Top 인플루언서 사용자가 자체 마케팅을 한다.

4. **무료 진입 + 후원/초대 매출 모델** — 첫 5일 모든 프리미엄 무료 → 지속 사용 시
   포인트 부족 → 친구 초대 (자체 마케팅) 또는 USDT 후원 (직접 매출). LLM 비용은
   캐싱(prewarm + persona analyze cache)으로 70% 절감.

---

## 잔여 작업 목표

> 게이미피케이션 + 미니앱 유입 + 리더보드 자랑 동선 완성을 위한 우선순위.

### 🥇 1 — 리더보드 본격 가동 (T2E-D Stage 2)
**목적**: "내가 누구보다 잘 나가는지" 확인 + 자랑 시스템의 종착점.

- [ ] **Multi-axis 리더보드 17-21종**:
      - 매치업 정확도 (전체 / 일별 / 주별)
      - 매치업 정답 streak
      - 예측 제출 수 (KOSPI / NASDAQ / 종목 / BTC)
      - 초대 검증 수 (전체 / 이번 달)
      - 도네이션 액수 (anonymized rank only)
      - 포인트 누적 / 시즌
      - 사주 종목 unlock 횟수
- [ ] **Top 10 노출** + 본인 순위 위치 표시 (1,234위 / 5,678명)
- [ ] **opt_in_leaderboard 필드 활용** — 사생활 보호 동의 시만 노출
- [ ] **익명/공개 모드 전환** (display_name vs `User_<anon[:4]>`)
- [ ] **자랑 카드 자동 생성**: top 10 진입 / 등급 변동 시 brag card 트리거

### 🥈 2 — 게이미피케이션 깊이 + 자랑 카드 퀄리티
**목적**: 자랑하고 싶을 만큼 시각적으로 매력적인 결과물.

- [ ] **자랑 카드 배경 템플릿 4종 디자인** (사용자가 디자인 제공 예정)
      - `tier_promotion.png` — 트로피 + 골드/플래티넘 그라디언트
      - `streak_accuracy.png` — 다트/타겟 + 불꽃
      - `bet_profit.png` — 차트 그래프 + 코인
      - `staking_size.png` — 코인 더미
      - 1080×1920 (모바일 풀스크린) + 텍스트 영역(중앙 60%)은 비워두면 Pillow가 채움
- [ ] **자랑 카드 트리거 추가**: 매치업 5연승 / 사주 첫 unlock / 도네이션 후원자 / 첫 1,000 P
- [ ] **공유 미리보기 메타 태그** (Telegram preview / OG card) — 자랑 카드 URL이 채팅에 붙을 때 큰 이미지 미리보기
- [ ] **이모지 폰트 누락 디버깅** — 현재 brag card 이미지가 일부 환경에서 깨지는 이슈

### 🥉 3 — 미니앱 유입 동선 강화
**목적**: 봇 → 미니앱 → 친구 초대 flywheel 완성.

- [ ] **Telegram menu button 영구 설정** (`setChatMenuButton`) — 채팅창 좌하단에서 한 탭으로 미니앱
- [ ] **첫 진입 시 사주 탭 자동 라우팅** — `saju_first_used_at` 비어있으면 Home 대신 Saju 탭 (후킹 메시지 정합성)
- [ ] **친구 1-tap value 확장** — 현재 `ref_X_q_NVDA_p_wood`만 지원 → `ref_X_saju=1990-05-15` (사주 미리보기) / `ref_X_matchup=2026-05-07-h14-m1` (매치업 공유)
- [ ] **Welcome event 부활** — 신규 사용자 첫 BTC 예측 모드 (현재 stub) 활성화 + 정답 시 200 P 보너스
- [ ] **공유 텍스트 SEO** — `@AI_vibe_investor_bot` 멘션 + 추천 ticker 동봉 → 공유 받은 사람이 클릭 시 즉시 분석 미리보기

### 4 — 종목 풀 보강
- [ ] S&P 500 + NASDAQ top 300 중 미분류 ~300 종목 LLM 배치 자동 분류 (현재 296)
- [ ] 한국인 선호 종목 CSV 14종 → 30종 확장 (PLTR, SOXL 등 최근 트렌드 반영)
- [ ] 매치업 mover 풀 확장 (현재 yfinance 296 + crypto 30) — KOSPI 200 추가 검토

### 5 — 운영 도구
- [ ] 대시보드에 매치업 / 도네이션 / 사주 사용량 별도 위젯
- [ ] **자랑 카드 이미지 깨짐 fix** — Azure Functions 컨테이너 한글/이모지 폰트 누락 가능성 조사
- [ ] **Cost Management Reader 권한** managed identity 자동 할당 Bicep
- [ ] 슬롯 리포트 6개 → 12개 (4개국어 × 3 페르소나 = 12 페르소나-언어 조합) 사전 생성 cron 분리

---

## 빠른 시작

### 로컬 개발

```bash
cd AIInvestor
cp .env.example .env
# .env에 TELEGRAM_BOT_TOKEN, DEEPSEEK_API_KEY 채우기
chmod 600 .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

### Azure 배포

```bash
# 1. Bicep으로 인프라 프로비저닝
az deployment group create -g rg-aiinvestor -f infra/main.bicep

# 2. GitHub Actions가 main 푸시 시 자동 배포
git push origin main
```

환경 변수:
- `TELEGRAM_BOT_TOKEN` — BotFather
- `DEEPSEEK_API_KEY` — platform.deepseek.com
- `STORAGE_ACCOUNT_NAME`, `USER_ID_SALT`
- `MINIAPP_URL` (default: `https://black-plant-...azurestaticapps.net/miniapp/`)
- `AZURE_SUBSCRIPTION_ID` (대시보드 과금 위젯용 — Cost Management Reader 권한 필요)
- `TONAPI_KEY` / `TRONGRID_API_KEY` (선택 — 무설정 시 free tier)
- `DASHBOARD_KEY` (admin 대시보드 가드)

---

## 텔레그램 명령

| 명령 | 동작 |
|---|---|
| `/start` | 사주 후킹 + 🚀 미니앱 열기 버튼 |
| `/miniapp` | 미니앱 열기 (별도 동선) |
| `/persona` / `/personas` | 페르소나 전환 (Buffett/Dalio/Wood) |
| `/lang` | 언어 전환 (ko/en/ja/zh) |
| `/attend` / `/points` / `/tier` | 게이미피케이션 상태 |
| `/invite` | 친구 초대 링크 |
| `/today` / `/market` | 오늘의 시황 |
| `/recommend [섹터]` | 섹터 추천 |
| `/compare A B` | 두 종목 비교 |
| `/feedback <text>` | 운영자 피드백 |
| `/forget` | 데이터 삭제 |
| 자유 입력 | 티커 또는 다국어 회사명 → 페르소나 분석 |

---

## 설계 문서

- **[paper_plan.md](docs/paper_plan.md)** — 통합 아키텍처 + 사용자 플로우 + 로드맵
- **[postmortem.md](docs/postmortem.md)** — 응답 지연 진단·수정 + 사전 캐싱 도입
- **[ticker-data-caching-architecture.md](docs/ticker-data-caching-architecture-v1.0-ko.md)** — 3-tier ticker price cache
- **[report-generation-policy.md](docs/report-generation-policy-v1.0-ko.md)** — 6슬롯 시황 정책
- **[t2e-gamification-architecture.md](docs/t2e-gamification-architecture-v2.0.md)** — 포인트/티어/초대 시스템 (있으면)

---

## 주의 고지

- 시스템 프롬프트가 **데이터 블록 외 수치 환각 금지**
- 명시적 **매수/매도 권고 금지** — 'I'd be inclined to wait' 같은 stance 표현
- 모든 응답 끝에 면책 한 줄 강제
- **사주 분석 disclaimer**: "명리학 통변 불완전 — 전문가 상담 권장 — 결과 책임 없음"
- Telegram WebApp init_data **HMAC-SHA256 검증** (모든 미니앱 API 호출)
- 사용자 ID **SHA-256 해시 + salt 회전** 익명화

---

## 라이선스 / 면책

본 프로젝트는 **Vibe Investing 연구 프로젝트의 실증 테스트**이며, AI Quant
페르소나 연구의 결과물입니다. AI 환각 및 오류가 발생할 수 있으며, 투자
자문이 아닙니다. 모든 투자 판단의 책임은 사용자에게 있습니다.

서비스는 [개인정보 처리방침](static_web/policy.html)과 [이용약관](static_web/terms.html)을
따릅니다. 익명화된 검색 로그가 학술 연구·모델 학습에 활용될 수 있으며,
거부 시 봇에서 `/forget` 명령으로 삭제 요청 가능합니다.
