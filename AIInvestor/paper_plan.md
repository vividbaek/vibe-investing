# AI Investor — 아키텍처 및 개발 계획

**서비스 코드명**: AI Investor (jeunggwon chatbot)
**소유자**: 김호광 (Dennis Kim)
**문서 버전**: 2.2 — 2026-05-05 (1차 작업 100% 완료 — 6단계 플로우 + 일일 시황 리포트 + 다국어 티커 매핑 + pytest 49건 + /forget + requirements.lock. §15 진행 현황 참조)
**문서 범위**: 현재 구현된 텔레그램 MVP의 기술 검토 + Azure 서버리스/CDN 기반 v1 설계 + 사용자 플로우 정의 + 향후 확장 로드맵
**연구 동반 문서**: 본 문서 §13 *Empirical Validation of Semantic Edge Caching for Repetitive LLM Queries* (IEEE Trans. Cloud Computing 투고 예정)

---

## 0. Executive Summary

AI Investor는 **유명 투자자 페르소나로 미국 시황(NASDAQ / S&P 500)을 해설하는 텔레그램 챗봇**입니다. 현재 구현은 단일 프로세스 폴링 방식의 Python MVP이며, 1차 운영 목표는 **Azure 서버리스(Functions Flex Consumption) + Azure CDN** 기반의 저비용 상시 가동 형태로 이전하는 것입니다. 사용자는 봇에 입장 → 서비스 설명 → 페르소나 선택 → 오늘의 시황 리포트 수신 → 자유 질의의 5단계 플로우로 진행하며, 모든 LLM 호출은 DeepSeek (`deepseek-chat` / `deepseek-reasoner`)에 위임합니다.

본 문서는 다음 다섯 가지를 한 곳에 통합합니다.

1. **MVP 아키텍처 도식 + 모듈 책임 (§1–4)**
2. **현재 소스 코드의 기술 검토 결과 — 발견된 이슈 및 우선순위 (§5)**
3. **사용자 플로우 5단계 정의 (§6)**
4. **Azure 서버리스 + CDN 마이그레이션 설계 (§7–11)**
5. **연구 데이터 수집 계획 (§13, 학술 논문용)**

---

## Table of Contents

1. [현재 시스템 (MVP) 개요](#1-현재-시스템-mvp-개요)
2. [모듈 구조 및 책임](#2-모듈-구조-및-책임)
3. [데이터 흐름 — 단일 메시지 처리](#3-데이터-흐름--단일-메시지-처리)
4. [현재 의존성 및 환경](#4-현재-의존성-및-환경)
5. [기술 검토 / 코드 리뷰](#5-기술-검토--코드-리뷰)
6. [사용자 플로우](#6-사용자-플로우)
7. [Azure 서버리스 + CDN 목표 아키텍처](#7-azure-서버리스--cdn-목표-아키텍처)
8. [Azure 리소스 목록 및 비용 가이드](#8-azure-리소스-목록-및-비용-가이드)
9. [배포 파이프라인](#9-배포-파이프라인)
10. [관측성·로깅·시크릿](#10-관측성로깅시크릿)
11. [개발 로드맵](#11-개발-로드맵)
12. [리스크 및 미해결 항목](#12-리스크-및-미해결-항목)
13. [연구 데이터 수집 계획 (학술 동반 자료)](#13-연구-데이터-수집-계획-학술-동반-자료)
14. [지역별 지연 분석 — 콜드 스타트·레이턴시 (참고)](#14-지역별-지연-분석--콜드-스타트레이턴시-참고)
15. [진행 현황 (2026-05-05 23:10 KST 기준)](#15-진행-현황-2026-05-05-2310-kst-기준)
16. [사전 캐싱 데몬 — 인기 종목·ETF Blob/CDN 사전 적재](#16-사전-캐싱-데몬--인기-종목etf-blobcdn-사전-적재)

---

## 1. 현재 시스템 (MVP) 개요

### 1.1 한 줄 정의

> Telegram 메시지를 받아 yfinance 펀더멘털 스냅샷을 조회하고, DeepSeek LLM에 페르소나 시스템 프롬프트와 함께 던져 한국어/영어 시황 해설을 회신하는 단일 프로세스 봇.

### 1.2 시스템 구성도 (현재)

```
┌──────────────┐         ┌────────────────────────────┐
│   Telegram    │ HTTPS  │   AI Investor (local)       │
│   사용자       ├───────▶│   python-telegram-bot v22   │
└──────────────┘ getUpd. │   (long polling)            │
                          │                              │
                          │   ┌──────────────────────┐  │
                          │   │ services.stock_svc   │──┼──▶ Yahoo Finance (yfinance)
                          │   ├──────────────────────┤  │
                          │   │ services.persona_eng │──┼──▶ DeepSeek API
                          │   └──────────────────────┘  │
                          │                              │
                          └────────────────────────────┘
```

- **상태 저장소**: 없음 (페르소나 선택은 `chat_data` 인메모리 — 재시작 시 소실)
- **인증/시크릿**: `.env` 파일 (`TELEGRAM_BOT_TOKEN`, `DEEPSEEK_API_KEY`)
- **운영 형태**: 로컬 개발 머신 또는 단일 호스트에서 `python main.py` (긴 폴링)

### 1.3 현재 제공 기능

| 명령 | 동작 |
|---|---|
| `/start` | 환영 메시지 + 현재 페르소나 표시 |
| `/help` | 명령 목록 |
| `/personas` | 사용 가능한 페르소나 목록 |
| `/persona <key>` | 페르소나 전환 (`buffett` / `dalio` / `wood`) |
| 일반 텍스트 | 티커로 간주 → yfinance 조회 → 페르소나 해설 응답 |

### 1.4 의도적으로 *아직* 제공하지 않는 것

- 시황 일일 리포트 자동 생성/전송 (목표 플로우의 핵심, §6 참조)
- 멀티턴 대화 / 후속 질문 처리
- 페르소나 선택 UI (현재는 `/persona <key>` 명령 입력 필요)
- 사용자 개인 포트폴리오 연동
- 결제·구독

---

## 2. 모듈 구조 및 책임

### 2.1 디렉토리

```
AIInvestor/
├── main.py                       엔트리 포인트, DI 와이어링
├── config.py                     .env 로딩 + 로깅 설정
├── bot/
│   ├── __init__.py
│   └── telegram_handler.py       명령/메시지 라우팅, 페르소나 상태
├── services/
│   ├── __init__.py
│   ├── persona_engine.py         페르소나 정의 + DeepSeek 호출
│   └── stock_service.py          yfinance 스냅샷 + 1년치 기간변동률
├── requirements.txt
├── .env / .env.example
└── README.md (이 문서가 향후 통합되는 대상)
```

### 2.2 클래스 책임

| 클래스 / 함수 | 위치 | 역할 |
|---|---|---|
| `Config` | [config.py](config.py) | 환경변수 검증, `Config.load()` 가 부재 시 즉시 실패 |
| `Persona` | [services/persona_engine.py](services/persona_engine.py) | 키·이름·시스템 프롬프트의 불변 데이터 |
| `PERSONAS` (dict) | 동 파일 | 새 페르소나 추가는 dict 한 줄이면 자동으로 `/personas`/`/persona` 노출 |
| `PersonaEngine` | 동 파일 | OpenAI SDK로 DeepSeek 호출, 시스템 프롬프트 + 펀더멘털 블록 → 응답 |
| `StockSnapshot` | [services/stock_service.py](services/stock_service.py) | 21개 펀더멘털·가격 필드를 담는 dataclass |
| `StockService.get_snapshot` | 동 파일 | yfinance `info` + 1년치 종가에서 1M/6M/1Y 변동률 계산 |
| `BotDependencies` | [bot/telegram_handler.py](bot/telegram_handler.py) | 핸들러가 공유하는 의존성 묶음 |
| `build_application` | 동 파일 | python-telegram-bot Application 조립 |

### 2.3 페르소나 시스템 프롬프트의 안전 장치 (현행)

세 페르소나(Buffett / Dalio / Wood) 모두 다음 4가지를 시스템 프롬프트에서 강제:

1. **수치 환각 금지** — 제공된 데이터 블록 외의 수치 인용 불가
2. **명시적 매수/매도 권고 금지** — 'I'd be inclined to wait' 같은 stance 표현으로 우회
3. **마무리 면책** — `This is not financial advice.` 한 줄 강제
4. **role-play 톤** — 페르소나별 화법 규정

---

## 3. 데이터 흐름 — 단일 메시지 처리

```
User → Telegram → getUpdates → _on_message
   1. text = "AAPL"
   2. StockService.get_snapshot("AAPL")
      └─ yfinance.Ticker("AAPL").info       (HTTP)
      └─ yfinance.Ticker("AAPL").history()  (HTTP, 1y daily)
      └─ 1M/6M/1Y % change 계산
      → StockSnapshot
   3. PersonaEngine.generate(persona, snapshot)
      └─ OpenAI(base_url=https://api.deepseek.com).chat.completions.create()
      → str (LLM reply)
   4. update.message.reply_text(f"[{persona.display_name} on {ticker}]\n\n{reply}")
```

평균 지연 (현재):
- yfinance 2회 라운드트립: 0.5–1.5s
- DeepSeek `deepseek-chat`: 2–5s (출력 토큰 ~600)
- 합계 p50 ≈ **3–6초** (인터랙티브 봇 기준 허용 가능, 캐싱 도입 시 0.2–0.5s 목표)

---

## 4. 현재 의존성 및 환경

### 4.1 requirements.txt

```
python-telegram-bot>=20.7
openai>=1.40.0           # DeepSeek가 OpenAI-compatible이라 동일 SDK 사용
yfinance>=0.2.40
pandas>=2.0
python-dotenv>=1.0.0
```

### 4.2 환경 변수 ([.env.example](.env.example))

| 키 | 설명 | 필수 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather에서 발급 | 예 |
| `DEEPSEEK_API_KEY` | platform.deepseek.com/api_keys | 예 |
| `DEEPSEEK_BASE_URL` | 기본 `https://api.deepseek.com` | 아니오 |
| `DEEPSEEK_MODEL` | `deepseek-chat`(V3) 또는 `deepseek-reasoner`(R1) | 아니오 |
| `DEFAULT_PERSONA` | `buffett` / `dalio` / `wood` | 아니오 |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` | 아니오 |

### 4.3 Python 호환성

코드 내부에 `from __future__ import annotations` 가 있어 Python 3.9에서도 PEP 604 union 어노테이션이 실행되지만, **타입 검사기(mypy 등) 사용 시에는 3.10+** 권장.

---

## 5. 기술 검토 / 코드 리뷰

현재 소스를 라인 단위로 점검한 결과를 우선순위별로 정리합니다.

### 5.1 즉시 수정 권고 (Severity: High)

| # | 위치 | 문제 | 권고 |
|---|---|---|---|
| H1 | [bot/telegram_handler.py:19](bot/telegram_handler.py#L19) | `DEFAULT_PERSONA_KEY` 를 import 하지만 사용처가 없음 | 죽은 import 제거 (linter가 잡아주지 못하는 이유는 tree에 등장하기 때문) |
| H2 | [main.py:40](main.py#L40) | `app.run_polling(allowed_updates=None)` — `None` 은 모든 업데이트 타입 허용. v1 운영 단계에서는 `["message"]` 등으로 좁혀서 텔레그램 측 부하/대역폭 절감 |
| H3 | [bot/telegram_handler.py:111](bot/telegram_handler.py#L111) | `_on_message` 가 입력을 항상 티커로 해석. "Tesla" / "엔비디아" 같은 회사명·한글·자유 질의 처리 분기 부재. §6 사용자 플로우의 "오늘의 리포트" / "추가 질문" 단계가 막힘 | 분류기 도입: (1) 정규식으로 티커 후보, (2) 그 외는 LLM 의도 분류 또는 룰 기반 키워드 매칭 |
| H4 | [services/stock_service.py:127](services/stock_service.py#L127) (`_safe_info`) | yfinance가 자주 던지는 `JSONDecodeError`/`HTTPError` 를 일반 `Exception` 으로 swallowing → 디버깅 어려움 | 구체적 예외 타입을 잡고 메트릭 카운터를 분리 (yfinance_failure_total) |
| H5 | [services/persona_engine.py:107](services/persona_engine.py#L107) | OpenAI 클라이언트가 동기 블로킹 호출. python-telegram-bot v22는 asyncio 기반이므로 LLM 호출 동안 이벤트 루프 블록됨. 동시 사용자 ≥ 2 시 응답 지연이 누적 | `AsyncOpenAI` 로 교체 + `await` 또는 최소한 `asyncio.to_thread(...)` 로 격리 |

### 5.2 중간 우선순위 (Severity: Medium)

| # | 위치 | 문제 | 권고 |
|---|---|---|---|
| M1 | [bot/telegram_handler.py:107](bot/telegram_handler.py#L107) | `chat_data` 에 페르소나 저장 — 프로세스 재시작 시 소실. 서버리스 환경에서는 매 요청 콜드 가능 | 영구 저장소(Cosmos DB / Table Storage)로 이전 |
| M2 | [services/stock_service.py:79](services/stock_service.py#L79) (`_normalize`) | `query.strip().upper().split()[0]` — 한글 회사명 입력 시 그대로 대문자화되어 yfinance가 못 찾음 | 회사명 → 티커 매핑 테이블 (S&P 500 + NASDAQ 100 ~600개 정도면 충분) |
| M3 | [services/persona_engine.py:107](services/persona_engine.py#L107) | LLM 응답에 timeout/retry 부재. DeepSeek 측 일시 장애 시 사용자가 30s 이상 대기 | `timeout=20`, 재시도 1회, 실패 시 fallback 메시지 |
| M4 | [services/stock_service.py:103](services/stock_service.py#L103) (`history`) | 모든 메시지마다 1년치 일봉을 다시 받음 (수십 KB × 호출 수) | 동일 티커 5분 캐싱 (인메모리 → 추후 Azure Cache for Redis) |
| M5 | [bot/telegram_handler.py:147](bot/telegram_handler.py#L147) | `_on_error` 가 모든 예외를 로깅만 — 사용자에게는 응답이 안 감 | 사용자에게 일반화된 사과 메시지 회신 추가 |

### 5.3 낮은 우선순위 (Severity: Low / Nice-to-have)

| # | 항목 | 권고 |
|---|---|---|
| L1 | 페르소나 시스템 프롬프트가 영어로만 작성 | 한국어 사용자를 위해 시스템 프롬프트 끝에 "Respond in the language of the user's most recent message" 추가 |
| L2 | 페르소나 3종만 존재 | 추가 후보: Charlie Munger, Peter Lynch, Howard Marks, 한국 가치투자자 등 |
| L3 | 단위 테스트 부재 | 최소한 `StockSnapshot.to_prompt_block()` 과 `_normalize` 의 pytest 추가 |
| L4 | `requirements.txt` 미고정 | `pip-compile` 로 `requirements.lock` 생성 — 재현성 확보 |

### 5.4 보안 / 컴플라이언스 점검

| 항목 | 상태 |
|---|---|
| `.env` 가 `.gitignore` 에 포함 | ✅ 루트 + AIInvestor 양쪽 |
| 키가 git 히스토리에 노출된 적 있는지 | ✅ 0건 |
| `.env` 파일 권한 | ✅ `0600` |
| 시크릿이 로그에 출력되는지 | ⚠ [main.py:34](main.py#L34) 가 `base_url` 만 로깅, 토큰은 노출되지 않음 — OK. 다만 `python-telegram-bot` 라이브러리가 디버그 레벨에서 토큰을 URL로 찍는 케이스 있음 → 로그 레벨을 INFO로 유지 |
| 페르소나 프롬프트 인젝션 | ⚠ 사용자 입력이 LLM `user` 메시지에 그대로 들어가지만, 시스템 프롬프트가 강하게 잠겨 있어 영향 제한적. 그래도 `</system>` 류 토큰은 sanitize 권장 |

### 5.5 종합 의견

현재 코드는 **MVP로서는 깔끔하고 모듈 분리도 합리적**이지만, 운영 단계로 진입하려면 위의 H1–H5 다섯 가지를 먼저 해결해야 합니다. 특히 **H5 (블로킹 LLM 호출)** 은 동시 사용자가 두 자릿수만 되어도 체감 응답이 무너지는 구조입니다.

---

## 6. 사용자 플로우

### 6.1 6단계 골든 패스 (1차 작업 범위)

```
[1] 인사            → /start 또는 봇 추가
                       "안녕하세요, AI Investor 입니다."
                       "당신만의 투자 멘토 페르소나로 매일의 미국 시황을 해설해 드립니다."

[2] 소개            → 자기소개 + 면책 + 데이터 출처 (1회 노출)
                       "yfinance · DeepSeek 기반 / 투자 자문 아님"
                       [버튼] "페르소나 고르고 시작하기"

[3] 페르소나 선택   → 인라인 키보드
                       [Warren Buffett] [Ray Dalio] [Cathie Wood]
                       선택 → 사용자 프로필에 영속 저장 (Cosmos / SQLite)
                       (재선택은 /persona 또는 메뉴 버튼)

[4] 오늘의 리포트   → "오늘의 리포트가 준비되어 있습니다. 받아보시겠어요?"
                       [예, 보기] [건너뛰기]
                       "예" 선택 시 → INTEGRATED_MARKET_PROMPT 실행
                         • S&P 500 / NASDAQ 종합 / NDX 일일 변동
                         • 상승 Top 5 / 하락 Top 5 (NASDAQ-100 기준)
                         • 거시 이슈 1–2개
                         • 페르소나 시각의 한 줄 시황 해설

[5] 관심사 획득     → "주로 어떤 분야/종목에 투자하시나요?"
                       (자유 입력 또는 인라인 키보드 멀티 선택)
                       예: "AI 반도체", "배당주", "BTC 관련주", "ETF",
                            "TSLA · NVDA · AAPL"
                       파싱 후 사용자 프로필에 태그 + 티커 리스트로 저장

[6] 기억 기반 소통  → 이후 모든 대화에서 다음을 자동 적용:
                       • 매일 첫 인사 시 사용자 관심사 우선 언급
                         "오늘 NVDA가 +3.2% 올랐어요. AI 반도체 섹터가 …"
                       • 사용자가 "오늘 어때?" 같은 모호한 질의 시
                         관심 종목·태그 기준으로 응답 구성
                       • 페르소나 교체 명령 시 인사 + 관심사는 그대로 유지
                         "✓ Ray Dalio 로 페르소나가 변경됐습니다.
                          (관심 분야: AI 반도체, ETF — 그대로 유지)"
```

식별 키:
- **Telegram 사용자**: `update.effective_user.id` (Telegram 정수 id)
- **모바일/웹 (Phase 4)**: 클라이언트가 발급한 UUIDv4
- 두 식별자 모두 §13.4 의 SHA-256 salt rotation 으로 익명화하여 저장 (§5.4 참고)

### 6.2 단계 매핑 — 구현 위치

| 단계 | 현재 구현 | 1차 작업 변경/신규 |
|---|---|---|
| [1] 인사 | `_cmd_start` ([bot/telegram_handler.py:60](bot/telegram_handler.py#L60)) | 메시지 한국어화 + 인라인 키보드로 다음 단계 유도 |
| [2] 소개 | 없음 | 신규 — 자기소개 + 면책 + `/policy` 명령 (1회만 자동 노출, `users.intro_seen` 플래그로 트래킹) |
| [3] 페르소나 | `_cmd_persona` (텍스트 명령만) | `InlineKeyboardMarkup` + `CallbackQueryHandler` + 영속 저장 |
| [4] 리포트 | 없음 | 신규 — `services/market_report.py` 추가 |
| [5] 관심사 획득 | 없음 | 신규 — 자유 텍스트 파싱 + 키워드 정규화 + 티커 매칭 |
| [6] 기억 기반 소통 | `chat_data` 인메모리 (M1 — 재시작 시 소실) | 신규 — `services/user_profile.py` + 영속 저장소 |

### 6.3 영속 저장소 — `users` 컨테이너 / 테이블

1차 작업에서는 단순화를 위해 **로컬 SQLite** (`./data/aiinvestor.db`) 로 구현하고, 2차 작업의 Azure 이전 시 **동일 스키마를 Cosmos DB 컨테이너**로 이주합니다.

```sql
-- users
CREATE TABLE users (
  user_key            TEXT PRIMARY KEY,    -- 'tg:<telegram_id>' 또는 'uuid:<v4>'
  anon_user_id        TEXT NOT NULL,       -- §13.4 SHA-256(salt + user_key)[:16]
  persona_key         TEXT NOT NULL DEFAULT 'buffett',
  intro_seen          INTEGER NOT NULL DEFAULT 0,
  research_consent    INTEGER NOT NULL DEFAULT 0,
  interest_tags       TEXT,                -- JSON array, e.g. ["AI 반도체","ETF"]
  watchlist_tickers   TEXT,                -- JSON array, e.g. ["NVDA","TSLA"]
  language            TEXT NOT NULL DEFAULT 'ko',
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL
);
```

Cosmos DB 매핑 (2차 작업):

| SQLite | Cosmos DB |
|---|---|
| 테이블 `users` | 컨테이너 `users`, partition key `/anon_user_id` |
| `interest_tags`, `watchlist_tickers` JSON 문자열 | 네이티브 배열 필드 |
| `created_at` / `updated_at` ISO8601 | 동일 |

### 6.4 신규 모듈 — `services/user_profile.py` 설계 (1차 작업)

```python
@dataclass
class UserProfile:
    user_key: str
    anon_user_id: str
    persona_key: str
    intro_seen: bool
    research_consent: bool
    interest_tags: list[str]
    watchlist_tickers: list[str]
    language: str
    created_at: datetime
    updated_at: datetime

class UserProfileRepo:
    def get_or_create(self, user_key: str) -> UserProfile: ...
    def set_persona(self, user_key: str, persona_key: str) -> None: ...
    def mark_intro_seen(self, user_key: str) -> None: ...
    def add_interests(self, user_key: str, tags: list[str], tickers: list[str]) -> None: ...
    def update_consent(self, user_key: str, consent: bool) -> None: ...
```

구현은 **SQLite (1차) → Cosmos DB (2차)** 모두 동일 인터페이스(`UserProfileRepo`) 를 노출하도록 abstract base + 두 구현체로 분리. `config.py` 에 `STORAGE_BACKEND=sqlite|cosmos` 환경 변수로 스위치.

### 6.5 신규 모듈 — `services/market_report.py` 설계 (1차 작업)

```python
@dataclass
class MarketReport:
    date: str                      # "2026-05-05"
    sp500_close: float
    sp500_change_pct: float
    nasdaq_close: float
    nasdaq_change_pct: float
    ndx_close: float
    ndx_change_pct: float
    top_gainers: list[TickerMove]   # 5
    top_losers: list[TickerMove]    # 5
    macro_headlines: list[str]      # 1–2
    persona_commentary: str         # LLM 생성 (페르소나 + 사용자 관심사 반영)

class MarketReportService:
    def build(self, persona: Persona, profile: UserProfile) -> MarketReport: ...
```

데이터 소스:
- 인덱스 종가 — yfinance `^GSPC`, `^IXIC`, `^NDX`
- 종목 등락 — NASDAQ-100 100개 일괄 다운로드 ([QQQUpDownSignal/qqq_up_down_signal.py](../QQQUpDownSignal/qqq_up_down_signal.py) 재사용)
- 거시 헤드라인 — 1차에서는 LLM에 위탁, 2차에서 NewsAPI/RSS 도입

1차 작업에서의 캐싱: 단일 프로세스 인메모리 `dict[date, MarketReport]` (TTL 24h).
2차 작업에서의 캐싱: §7.6 의 **Timer Trigger 사전 생성 + Blob/CDN** 으로 승격.

### 6.6 인라인 키보드 예시

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def persona_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Warren Buffett (장기 가치)", callback_data="persona:buffett")],
        [InlineKeyboardButton("Ray Dalio (매크로/올웨더)",   callback_data="persona:dalio")],
        [InlineKeyboardButton("Cathie Wood (혁신 성장)",     callback_data="persona:wood")],
    ])

def report_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("예, 보기",   callback_data="report:show"),
         InlineKeyboardButton("건너뛰기",   callback_data="report:skip")],
    ])

INTEREST_PRESETS = ["AI 반도체", "빅테크", "배당주", "ETF",
                     "BTC 관련주", "원자재/에너지", "헬스케어", "직접 입력"]
```

콜백은 `CallbackQueryHandler` 가 처리하며, 영속 저장소(`UserProfileRepo`) 에 즉시 반영. 페르소나 교체 시 `interest_tags` / `watchlist_tickers` 는 그대로 유지하고 인사말만 갱신.

---

## 7. Azure 서버리스 + CDN 목표 아키텍처

### 7.1 v1 시스템 구성도

```
                    ┌──────────────────────────────────────────────┐
                    │  Azure                                       │
                    │                                              │
   Telegram         │  ┌──────────────┐    ┌──────────────────┐   │
   Bot Webhook  ───▶│ ─│ App Gateway  │───▶│ Azure Functions  │   │
   (HTTPS)          │  │ + WAF        │    │ (Flex Consumption)│  │
                    │  └──────────────┘    │  - bot_webhook    │  │
                    │                       │  - daily_report   │  │
                    │                       │  - timer_warmup   │  │
                    │                       └────────┬─────────┘   │
                    │                                │              │
                    │           ┌────────────────────┼────────┐    │
                    │           ▼                    ▼        ▼    │
                    │  ┌──────────────────────────────┐  ┌────┐ │
                    │  │ Blob Storage (단일 저장 계층) │  │ KV │ │
                    │  │  • users/<anon>.json          │  │    │ │
                    │  │  • reports/<date>/<persona>   │  │    │ │
                    │  │  • logs/yyyy/mm/dd/HH.ndjson  │  │    │ │
                    │  └──────────────┬───────────────┘  └────┘ │
                    │                 │                          │
                    │  Functions 인스턴스 메모리 캐시 (TTL 5분)   │
                    │                           │                  │
                    │                           ▼                  │
                    │                    ┌─────────────┐           │
                    │                    │ Azure CDN   │           │
                    │                    │ (Standard)  │           │
                    │                    └──────┬──────┘           │
                    └───────────────────────────┼──────────────────┘
                                                │
                                  외부 cache 레이어 (TTL 1h)
                                                │
                                                ▼
                                     모바일 앱 / 웹 (장래)
```

### 7.2 컴포넌트 매핑

| 책임 | Azure 서비스 | 비고 |
|---|---|---|
| HTTPS 엔드포인트 (Telegram Webhook 수신) | Azure Functions HTTP Trigger | `setWebhook` 으로 텔레그램이 호출 |
| 봇 비즈니스 로직 | Azure Functions (Python 3.11 isolated worker) | 현재 코드의 `bot/`, `services/` 그대로 이전 |
| 일일 리포트 사전 생성 | Azure Functions Timer Trigger (`0 30 6 * * *` KST = 21:30 UTC, 미국 시장 마감 30분 후) | 결과를 Blob에 JSON 업로드 |
| 사전 생성된 리포트 서빙 | Azure Blob → Azure CDN (Standard Microsoft tier) | TTL 1시간, 동일 KST 일자 동안 재사용 |
| **사용자 페르소나/관심사 상태** | **Azure Blob Storage** (`users/<anon_user_id>.json`) | Functions가 Blob을 직접 읽고 **인스턴스 메모리에 TTL 5분 캐싱**. Cosmos DB는 도입하지 않음 (§7.3) |
| **사용 로그 (분석용)** | Azure Blob Storage append-only logs | 시간대/페르소나/티커/지연/캐시적중 등 익명 텔레메트리. **배치 분석으로 LLM 호출 특이점·시간대별 군집성 추출** (§7.4) |
| 시크릿 관리 | Azure Key Vault | Functions가 Managed Identity로 참조 |
| 관측 | Application Insights | 자동 통합, 비용 최저 티어 |

### 7.3 사용자 데이터 저장 — Blob 직접 읽기 + 메모리 캐시 (TTL 5분)

**의도적 설계 결정**: 2차 작업에서는 **Cosmos DB를 도입하지 않습니다**. 사용자 페르소나·관심사·언어 같은 가벼운 키-값 데이터는 **Blob Storage 객체 한 개씩** 으로 충분하며, 비용 / 운영 복잡도 / 콜드 스타트 측면에서 우월합니다.

#### 저장 레이아웃

```
container "users" (private, RA-GRS)
└─ users/<anon_user_id>.json
   {
     "user_key_hash": "82ec62f2f6549864",
     "persona_key": "buffett",
     "language": "ko",
     "intro_seen": true,
     "interest_tags": ["AI 반도체", "ETF"],
     "watchlist_tickers": ["NVDA", "TSLA"],
     "created_at": "2026-05-05T22:21:18Z",
     "updated_at": "2026-05-06T07:14:02Z"
   }
```

- partition: `anon_user_id` 의 첫 2자로 prefix 분산 (`users/82/82ec62f2f6549864.json`) — 핫스팟 방지
- ETag 기반 optimistic concurrency — 메모리 캐시 stale 시 충돌 감지

#### 인스턴스 메모리 캐시 (TTL 5분)

```python
# services/user_profile_blob.py (2차 작업)
class BlobUserProfileRepo(UserProfileRepo):
    def __init__(self, blob_client, ttl_seconds: int = 300):
        self._client = blob_client
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, UserProfile, str]] = {}  # key -> (expires_at, profile, etag)
        self._lock = asyncio.Lock()

    async def get_or_create(self, user_key, default_language, default_persona):
        cached = self._cache.get(user_key)
        now = time.monotonic()
        if cached and cached[0] > now:
            return cached[1]                    # 캐시 적중

        # 캐시 미스 → Blob 직접 읽기
        blob_path = f"users/{anon[:2]}/{anon}.json"
        try:
            data = await self._client.download_blob(blob_path)
            profile, etag = parse(data)
        except ResourceNotFoundError:
            profile = create_default(...)
            etag = await self._client.upload_blob(blob_path, profile)

        self._cache[user_key] = (now + self._ttl, profile, etag)
        return profile
```

#### 캐시 동작 시나리오

| 상황 | 동작 |
|---|---|
| 사용자가 5분 내 재요청 (같은 인스턴스) | 메모리 적중, Blob 호출 없음 |
| 사용자가 5분 내 재요청 (다른 인스턴스) | Blob 1회 read (ETag 비교 후 본문 다운로드) |
| 사용자가 5분 후 재요청 | TTL 만료 → Blob 재읽기 |
| 사용자가 페르소나/관심사 변경 | Blob write + 캐시 즉시 갱신, ETag 새로고침 |
| Functions 콜드 스타트 | 캐시 dict 비어 있음 → 첫 요청 1회 Blob read |

#### 왜 Cosmos DB를 안 쓰는가

| 차원 | Blob Storage (선택) | Cosmos DB Serverless (탈락) |
|---|---|---|
| DAU 100 기준 월 비용 | < $0.10 (스토리지) + < $0.05 (트랜잭션) | $1–3 (RU 기반) |
| 엔티티 1건 read 지연 | ~30–80ms (Blob) | ~5–15ms (Cosmos) |
| **5분 메모리 캐시 적용 후 평균 read** | **~2–5ms** (대부분 적중) | ~5–15ms |
| 운영 복잡도 | 매우 낮음 (객체 한 개) | 컨테이너 / partition / RU 관리 |
| 백업 / 마이그레이션 | `azcopy` 한 줄 | 별도 도구 |
| 일관성 모델 | ETag optimistic | 다양함 |
| 쓰기 빈도 | 사용자당 분당 1회 미만 | — |

**핵심 trade-off**: 각 사용자의 쓰기 빈도가 매우 낮고(페르소나 선택·관심사 입력 정도) 읽기는 5분 캐시로 흡수되므로, Blob의 read 지연(~50ms) 이 인터랙티브 봇 응답(p50 3–6초) 대비 무시할 수준. Cosmos DB의 ms-단위 지연 이점이 사라집니다.

---

### 7.4 사용 로그 — Blob 적재 + 배치 분석

#### 적재 형식

Functions의 모든 사용자 요청에서 **익명 텔레메트리** 한 줄을 NDJSON 으로 Blob에 append:

```
container "logs" (private)
└─ logs/2026/05/05/22.ndjson      (시간대별 분리, UTC)
```

```json
{"ts":"2026-05-05T22:31:14Z","anon":"82ec62f2f6549864","lang":"ko",
 "channel":"telegram","persona":"buffett","action":"ticker_query",
 "ticker":"NVDA","query_len":4,"latency_ms":4123,
 "llm_in_tokens":820,"llm_out_tokens":580,"cache_hit":false,
 "kst_hour":7,"kst_weekday":"Tue"}
```

기록되지 않는 항목: 원시 텔레그램 ID, 사용자명, IP, 자유 질의 본문(연구 동의 시에만). §13.4의 익명화 원칙 준수.

#### 작성 패턴

- 단일 라이트는 비용·지연 증가 → **인스턴스 내부 버퍼**(`list[dict]`) 에 모아 60초 또는 100건마다 append-blob 쓰기
- Function 인스턴스 종료 시그널 (`shutdown`) 에서 잔여 버퍼 flush
- Append Blob 사용으로 동시 인스턴스의 동일 시간대 파일 동시 쓰기 안전

#### 배치 분석 — LLM 호출 특이점 + 시간대별 군집성

매일 KST 07:00 (UTC 22:00, US 마감 1시간 후) 실행되는 **`analyze_logs` Timer Trigger**:

```
1. 전일 24개 시간대 *.ndjson 다운로드 → pandas DataFrame
2. 시간대별 집계:
   - 시간대 × 페르소나 매트릭스
   - 시간대 × 티커 Top-20 매트릭스
   - 시간대 × 평균 지연 / LLM 토큰 사용량
3. 특이점 탐지:
   - 7일 이동 평균 대비 ±2σ 벗어난 시간대 (호출 급증/급감)
   - 평소 안 등장하던 티커가 Top-10 진입 (신규 모멘텀)
   - LLM 출력 토큰이 평균 대비 +50% (장문 응답 — 환각 의심)
4. 군집성 패턴 추출:
   - K-means(K=24) on (hour-of-day) feature → 군집 일치도
   - DBSCAN on (ticker, hour) → 시간대 + 종목의 핫존
   - "미국 시장 개장 22:30 KST 직후 NVDA 질의 30배 증가" 같은
     자연스러운 시간대×테마 군집 자동 라벨링
5. 결과 요약을 Blob `analysis/yyyy-mm-dd.json` 에 저장
6. 임계 초과 시 텔레그램으로 운영자에게 알림
```

이 분석 결과 자체가 §13 학술 동반 자료의 §7 (Predictive Cache Warming) 와 §11 (Cache Hit Rate) 의 **선행 검증 데이터**로 활용됩니다 — 즉 3차 작업에서 의미적 캐싱을 도입하기 전에, 2차 작업의 로그만으로도 Zipf 분포 / 시간 군집성 / 캐시 잠재 적중률을 추정할 수 있습니다.

#### 보존 정책

- `logs/` 컨테이너: lifecycle policy로 90일 후 자동 삭제 (개인정보 잔존 최소화)
- `analysis/` 컨테이너: 365일 보존 (집계 결과만)
- `users/` 컨테이너: 사용자가 `/forget` 명령 시 즉시 삭제, 비활성 사용자는 1년 후 정리 잡

---

### 7.5 Telegram Webhook 모드로 전환

현재 `app.run_polling()` ([main.py:40](main.py#L40)) 은 Functions에서 동작 불가. 전환 작업:

```python
# function_app.py (Azure Functions Python v2 model)
import azure.functions as func
from telegram import Update
from telegram.ext import Application

app_func = func.FunctionApp()
ptb_app: Application = build_application(token, deps)

@app_func.route(route="telegram/webhook", auth_level=func.AuthLevel.ANONYMOUS)
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    update = Update.de_json(body, ptb_app.bot)
    await ptb_app.process_update(update)
    return func.HttpResponse(status_code=200)
```

배포 후 1회 실행:

```bash
curl -F "url=https://<func-app>.azurewebsites.net/api/telegram/webhook" \
     -F "secret_token=<random32hex>" \
     "https://api.telegram.org/bot<TOKEN>/setWebhook"
```

`secret_token` 은 Telegram이 매 호출 헤더 `X-Telegram-Bot-Api-Secret-Token` 에 실어 보내며, Functions에서 검증 → 외부 위조 호출 차단.

### 7.6 일일 리포트 사전 생성 + CDN 캐시

```
KST 06:30 (UTC 21:30 — 미장 마감 직후)
┌──────────────────────────────┐
│ Timer Trigger Function        │
│  1. yfinance 인덱스/NDX-100   │
│  2. DeepSeek로 페르소나별 3개 │
│     리포트 생성               │
│  3. Blob 업로드:              │
│     reports/2026-05-05/       │
│       buffett.json            │
│       dalio.json              │
│       wood.json               │
│  4. CDN purge (해당 path)     │
└──────────────────────────────┘

사용자가 [예, 보기] 누르면:
  Functions가 Blob URL이 아닌 CDN URL을 사용자 메시지로 회신/렌더
  → 동일 일자 같은 페르소나 N명 사용자 → CDN edge에서 응답 (Functions 재실행 X)
```

**캐시 효과 정량 추정 (DAU 1,000, 페르소나 3, 일 1회 리포트 조회 가정):**
- 캐시 없음 시: 1,000회 LLM 호출 × $0.001 ≈ $1/일
- CDN 적중 시: **3회** 사전 생성 × $0.001 ≈ $0.003/일 (99.7% 절감)

이 캐싱 효과 자체가 §13 학술 동반 자료의 검증 대상.

### 7.7 Functions 콜드 스타트 대응

Flex Consumption은 콜드 스타트 1–3초. 봇 응답에 치명적이므로:

1. **Always Ready instances = 1** 설정 (월 추가 비용 ~$13)
2. 또는 5분마다 셀프-핑하는 Timer Trigger
3. 일일 리포트는 콜드 스타트 영향 없음 (timer 자체가 콜드)

### 7.8 환경 분리

| 환경 | Function App | Bot Token | DeepSeek Key |
|---|---|---|---|
| dev | `aiinvestor-dev` | `@AI_vibe_investor_dev_bot` (별도 발급) | 동일 키 (저비용) |
| prod | `aiinvestor-prod` | `@AI_vibe_investor_bot` (현재 실서비스) | 별도 키 |

GitHub Actions가 `main` 브랜치는 prod로, `dev` 브랜치는 dev로 배포.

---

## 8. Azure 리소스 목록 및 비용 가이드

### 8.1 리소스 목록 (1 RG 권장)

```
rg-aiinvestor-prod
├── func-aiinvestor-prod              Function App (Flex Consumption, Linux)
├── plan-aiinvestor-prod              App Service Plan (Flex)
├── st-aiinvestor-prod                Storage Account
│                                       containers:
│                                         users/   사용자 페르소나 JSON
│                                         reports/ 일일 리포트 (CDN origin)
│                                         logs/    NDJSON 사용 로그
│                                         analysis/ 배치 분석 결과
├── cdn-aiinvestor-prod               CDN Profile + endpoint (reports/ origin)
├── kv-aiinvestor-prod                Key Vault
└── appi-aiinvestor-prod              Application Insights
```

> **Cosmos DB 없음**. 모든 영속 데이터는 Blob Storage 단일 계층 (§7.3).

### 8.2 월간 비용 추정 (DAU 100 기준)

| 항목 | 사용량 추정 | 월 비용 |
|---|---|---|
| Functions Flex (always-ready 1) | | ~$13 |
| Functions per-execution | 100 DAU × 5건/일 × 30일 = 15,000 호출 | ~$0.50 |
| Blob Storage 용량 | users 100×2KB + reports 90일×3×50KB + logs 90일×NDJSON ≈ 200MB | ~$0.01 |
| Blob Storage 트랜잭션 | 5분 캐시 적용 후 사용자당 평균 read 0.2회/건 + write 0.05회/건 | ~$0.10 |
| Azure CDN Standard Microsoft | 5 GB egress | ~$0.40 |
| Application Insights | 1 GB ingestion | $0 (free tier) |
| Key Vault | 키 5개, 호출 1만회 | ~$0.30 |
| **Azure 합계** | | **~$14.30/월** |
| DeepSeek API | 사전 생성 일 3회 + 사용자 질의 100×5×30 | ~$2/월 |
| **총합** | | **~$16/월** |

Cosmos DB 제거로 월 ~$1 절감 + 운영 단순화. DAU 1,000 까지 확장 시 LLM 비용이 가장 빠르게 늘어나므로 §13의 의미적 캐싱이 비용 곡선 평탄화의 핵심.

---

## 9. 배포 파이프라인

### 9.1 GitHub Actions 워크플로 (개요)

```yaml
# .github/workflows/deploy.yml (요약)
name: deploy-aiinvestor
on:
  push:
    branches: [main, dev]
    paths: ['AIInvestor/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r AIInvestor/requirements.txt -t AIInvestor/.python_packages/lib/site-packages
      - uses: azure/login@v2
        with: { creds: ${{ secrets.AZURE_CREDENTIALS }} }
      - uses: azure/functions-action@v1
        with:
          app-name: ${{ github.ref_name == 'main' && 'func-aiinvestor-prod' || 'func-aiinvestor-dev' }}
          package: AIInvestor
          scm-do-build-during-deployment: true
```

### 9.2 인프라 코드 (Bicep 권장)

`infra/main.bicep` 에서 §8.1 리소스를 모두 선언. `azd up` 한 번으로 RG 전체 프로비저닝.

### 9.3 시크릿 흐름

```
.env (로컬 개발)
└── git에 절대 커밋 X (.gitignore)

Azure Key Vault
├── telegram-bot-token
├── deepseek-api-key
├── telegram-webhook-secret
└── user-id-salt              # SHA-256 익명화 솔트 (90일 rotation)

Function App
├── Managed Identity 활성화
├── Key Vault에 RBAC: Key Vault Secrets User
├── Storage Account에 RBAC: Storage Blob Data Contributor
└── App Settings에 Key Vault reference
    예: TELEGRAM_BOT_TOKEN=@Microsoft.KeyVault(SecretUri=https://kv-aiinvestor-prod.vault.azure.net/secrets/telegram-bot-token/)
```

### 9.4 Azure 계정 연결 방식 — 어떻게 알려주실지

Azure 배포를 진행하실 준비가 되면 다음 중 **하나** 만 알려주시면 됩니다 (보안상 권장 순):

#### 방법 A — Service Principal (가장 안전, 권장)

GitHub Actions 자동 배포에 가장 적합합니다.

```bash
# 본인의 로컬에서 1회 실행
az login
az account show --query id -o tsv          # subscription_id 확인

# 배포 권한만 갖는 SP 생성 (Owner 아님)
az ad sp create-for-rbac \
  --name "github-aiinvestor-deploy" \
  --role contributor \
  --scopes /subscriptions/<sub-id>/resourceGroups/rg-aiinvestor-prod \
  --sdk-auth
```

출력된 JSON 한 덩어리만 알려주시면 됩니다 (`clientId`, `clientSecret`, `subscriptionId`, `tenantId`). GitHub Secret `AZURE_CREDENTIALS` 로 등록 후 워크플로가 사용합니다.

#### 방법 B — OIDC Federated Credential (시크릿 없음, 더 안전)

비밀값 자체를 GitHub에 저장하지 않습니다. 본인이 Azure 포털에서 federated credential 등록 후, 다음 4개 값만 알려주시면 됩니다:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- 등록된 GitHub repo / branch / environment

#### 방법 C — 본인이 직접 `azd up` 실행

CI 자동 배포가 아직 부담스러우시면, 본인 로컬에서 `azd auth login` 후 `azd up` 한 번 실행하시면 됩니다. 이 경우 제게 알려주실 정보는 **없습니다** (시크릿이 본인 로컬을 떠나지 않음).

#### 어떤 정보든 알려주실 때 주의

- **API key 본문은 GitHub repo / Slack / 메일에 절대 평문으로 보내지 말 것** — 비밀번호 관리자, 1Password Secure Note, 또는 Azure Key Vault의 `Get Secret URI` 만 공유
- Service Principal credential 은 90일마다 회전 권장 (`az ad sp credential reset`)
- 배포 후에는 GitHub Actions 워크플로 로그에 시크릿이 마스킹되는지 1회 확인

---

## 10. 관측성·로깅·시크릿

### 10.1 로깅 정책

| 레벨 | 용도 | PII 포함 |
|---|---|---|
| ERROR | 예외, 외부 API 실패 | ❌ |
| WARNING | 재시도 발생, fallback 응답 | ❌ |
| INFO | 요청 1줄 (anon_user_id, channel, command, latency_ms, cache_hit) | ❌ |
| DEBUG | 페이로드 (개발 환경에서만) | ⚠ 최소화 |

### 10.2 핵심 메트릭 (Application Insights)

- `request.latency_ms` (p50/p95/p99)
- `llm.deepseek.tokens_in`, `llm.deepseek.tokens_out`, `llm.deepseek.cost_usd`
- `cache.hit_rate` (CDN + 의미적 캐시 분리)
- `yfinance.failure_total`
- `persona.distribution` (어느 페르소나가 자주 쓰이는지)
- `flow.dropoff` (사용자 플로우 5단계 중 어디서 이탈)

### 10.3 알람

- Functions error rate > 5% 5분간 → Slack
- DeepSeek 호출 실패 > 10건/5분 → Slack
- Cosmos DB RU 사용량 > 80% → Slack

---

## 11. 개발 로드맵

본 로드맵은 **1차 / 2차 / 후속(3·4차)** 의 3-tier 우선순위로 정리합니다. **1차 = 기능 완결 (로컬)**, **2차 = 클라우드 이전 (Azure 서버리스 + CDN)**, 후속 = 학술 데이터 수집 / 멀티 채널.

---

### 🥇 1차 작업 — 6단계 사용자 플로우 + 영속 메모리 (로컬에서 완성)

**목표**: 사용자가 봇과 처음 대화하기 시작해서 페르소나 교체까지 모든 인터랙션이 정상 동작하고, 사용자 관심사가 영구 기억되는 단일 프로세스 봇.
**환경**: 로컬 또는 단일 호스트, SQLite 기반 영속화. Azure 미사용.
**완료 기준**:
- §6.1 의 [1]–[6] 단계가 모두 텔레그램에서 동작
- 봇 재시작해도 페르소나·관심사가 유지됨
- 페르소나 교체 시 관심사 컨텍스트는 보존

#### 1차-A: 기술 부채 해소 (운영 적합성)

- [ ] **H5 — 비동기 LLM 전환**: `OpenAI` → `AsyncOpenAI`, `generate()` 를 `async def` 로 변경 후 `_on_message` 에서 `await` ([services/persona_engine.py:87](services/persona_engine.py#L87))
- [ ] **H3 — 의도 분류 분기**: `_on_message` 가 입력을 (a) 티커 후보 정규식 → yfinance, (b) 한글 회사명 → 매핑 테이블, (c) 그 외 자유 질의 → LLM Q&A 모드로 분기 ([bot/telegram_handler.py:111](bot/telegram_handler.py#L111))
- [ ] **H2 — `allowed_updates`** 좁히기: `["message", "callback_query"]` ([main.py:40](main.py#L40))
- [ ] **H1 — dead import 제거**: `DEFAULT_PERSONA_KEY` ([bot/telegram_handler.py:19](bot/telegram_handler.py#L19))
- [ ] **H4 — yfinance 예외 세분화**: 카운터 분리 ([services/stock_service.py:127](services/stock_service.py#L127))
- [ ] **M5 — `_on_error` 사용자 회신** ([bot/telegram_handler.py:147](bot/telegram_handler.py#L147))

#### 1차-B: 영속 저장소 — `UserProfileRepo` (SQLite)

- [ ] `services/user_profile.py` — `UserProfile` 데이터클래스 + `UserProfileRepo` 추상 인터페이스 (§6.4)
- [ ] `services/user_profile_sqlite.py` — SQLite 구현체 (`./data/aiinvestor.db`), 첫 실행 시 테이블 자동 생성 + `anon_user_id` 인덱스
- [ ] `anon_user_id` 생성 — SHA-256 with local salt (`.env` 의 `USER_ID_SALT`)
- [ ] DI 와이어링 — `BotDependencies` 에 `profile_repo: UserProfileRepo` 추가 ([bot/telegram_handler.py:32](bot/telegram_handler.py#L32))

#### 1차-C: 6단계 플로우 구현

- [ ] **[1] 인사** — `_cmd_start` 한국어화 + 다음 단계 인라인 키보드
- [ ] **[2] 소개** — `intro_seen=0` 사용자에게만 1회, 면책 + 데이터 출처 + `/policy` 명령
- [ ] **[3] 페르소나 선택** — `InlineKeyboardMarkup` + `CallbackQueryHandler("persona:*")` → `profile_repo.set_persona()`
- [ ] **[4] 오늘의 리포트** — `services/market_report.py` 신설 (§6.5), `[예/건너뛰기]` 버튼, 응답 끝에 [5]로 자연 전이
- [ ] **[5] 관심사 획득** — 자유 텍스트 입력 + 프리셋 버튼(`INTEREST_PRESETS`), 파싱 → `interest_tags` / `watchlist_tickers` 분리 저장
- [ ] **[6] 기억 기반 소통** — 모든 LLM 호출 시 user prompt 에 사용자 관심사 컨텍스트 주입; 모호 질의("오늘 어때?") 는 `watchlist_tickers` 우선 응답

#### 1차-D: 페르소나 교체 컨텍스트 보존

- [ ] `/persona <key>` 또는 인라인 키보드 재선택 시 `persona_key` 만 갱신, `interest_tags` / `watchlist_tickers` 보존
- [ ] 교체 직후 인사말 — "✓ {새 페르소나} 로 변경됐습니다. 관심 분야: {tags} — 그대로 유지"

#### 1차-E: 검증

- [ ] **L3 — pytest 추가**: `UserProfileRepo` (in-memory SQLite로 격리), `MarketReportService.build()` (mock yfinance), `intent_classifier`
- [ ] **L4 — `requirements.lock`** 생성 (`pip-compile`)
- [ ] **종단 시나리오**: 봇 재시작 후 동일 텔레그램 사용자가 (a) 페르소나 유지, (b) 관심사 회상, (c) 페르소나 교체 후에도 관심사 유지 — 수동 통과

---

### 🥈 2차 작업 — Azure Functions Flex Consumption + CDN 이전

**목표**: 1차 결과물을 **그대로** Azure 서버리스로 이전하고, 일일 리포트를 CDN 사전 캐싱하여 LLM 호출량 99%+ 절감.
**환경**: Azure (`rg-aiinvestor-prod`, §8.1). Telegram **Webhook 모드**.
**전제**: 1차 작업 완전 완료 — 코드 모듈은 그대로 두고 *runtime layer 만* 교체.
**완료 기준**:
- prod 환경에서 Functions 기반 봇이 24/7 응답 (always-ready 1)
- 일일 리포트가 KST 06:30 자동 생성되어 CDN edge에서 서빙
- 사용자 프로필이 Cosmos DB로 이전 완료, SQLite 백엔드는 dev 전용으로 잔존
- GitHub Actions가 main → prod, dev → dev 자동 배포

#### 2차-A: Functions 프로젝트 화

- [ ] `function_app.py` — Python v2 모델, `bot_webhook` (HTTP) + `daily_report` (Timer) + `keepalive` (Timer)
- [ ] Webhook 모드 — `app.run_polling()` 제거, `ptb_app.process_update(update)` 직접 호출 (§7.5)
- [ ] `setWebhook` 자동화 — 배포 직후 GitHub Actions가 `secret_token` 까지 함께 등록
- [ ] Webhook secret 검증 — `X-Telegram-Bot-Api-Secret-Token` 헤더 매칭 실패 시 401

#### 2차-B: 영속 저장소 SQLite → Blob Storage (TTL 5분 캐시)

> §7.3 의 결정에 따라 Cosmos DB는 도입하지 않습니다. Blob 한 객체 = 사용자 한 명.

- [ ] `services/user_profile_blob.py` — `BlobUserProfileRepo` (1차의 `UserProfileRepo` 인터페이스 그대로 구현)
- [ ] **인스턴스 메모리 캐시** (`dict`, TTL 5분, asyncio lock 보호)
- [ ] **ETag 기반 optimistic concurrency** — 다른 인스턴스가 먼저 쓴 변경 감지 시 재읽기 후 머지
- [ ] partition 분산 — `users/<anon[:2]>/<anon>.json`
- [ ] `STORAGE_BACKEND=blob` 환경변수로 자동 선택
- [ ] 일회성 마이그레이션 — dev SQLite → Blob (Python 한 줄 스크립트)
- [ ] **/forget 명령** — 사용자가 자기 Blob을 즉시 삭제할 수 있는 명령 (§7.4 보존 정책 충족)
- [ ] 통합 테스트 — 콜드 스타트 후에도 페르소나/관심사 정확 회상 + 5분 캐시 적중 확인

#### 2차-C: Timer Trigger + Blob + CDN

- [ ] **Timer**: `0 30 6 * * *` (KST 06:30 = UTC 21:30, US 마감 30분 후)
- [ ] 페르소나 3종 × 일자별로 LLM 호출 → JSON → Blob `reports/<date>/<persona>.json`
- [ ] **Azure CDN Standard Microsoft** profile + endpoint, origin = Blob 컨테이너
- [ ] CDN purge — Timer 끝에서 신규 path 우선 캐싱
- [ ] [예, 보기] 클릭 시 Functions가 **CDN URL 의 JSON 을 fetch** → 페르소나 답변 렌더링 → Telegram 회신
- [ ] `cdn.hit_rate` App Insights 커스텀 메트릭

#### 2차-D: 인프라 코드 + 시크릿

- [ ] `infra/main.bicep` — §8.1 의 7개 리소스 모두 선언
- [ ] **Key Vault** 시크릿 — `telegram-bot-token`, `deepseek-api-key`, `telegram-webhook-secret`, `user-id-salt`
- [ ] Function App **Managed Identity** + KV RBAC (`Key Vault Secrets User`)
- [ ] App Settings 가 Key Vault reference 로 시크릿 주입 (`@Microsoft.KeyVault(...)`)
- [ ] **GitHub Actions** `.github/workflows/deploy.yml` (§9.1), main→prod / dev→dev
- [ ] dev/prod 환경 분리 — 별도 봇 토큰(`@AI_vibe_investor_dev_bot`), 별도 DeepSeek 키

#### 2차-E: 관측성

- [ ] App Insights 자동 통합 + 커스텀 메트릭: `request.latency_ms`, `llm.deepseek.tokens_*`, `cdn.hit_rate`, `flow.dropoff[1..6]`, `persona.distribution`
- [ ] Azure Monitor 알람: error rate > 5% / DeepSeek 실패 > 10건/5분 / Cosmos RU > 80% (§10.3)
- [ ] 비용 알람 — 월 예산 $30 임계 시 메일

#### 2차-F: 콜드 스타트 + 부하 검증

- [ ] **Always Ready instances = 1**
- [ ] `keepalive` Timer (5분)
- [ ] k6 또는 locust 부하 테스트 — 동시 50 사용자, p95 < 4초

#### 2차-G: 사용 로그 적재 + 배치 분석 (§7.4)

- [ ] `services/usage_logger.py` — NDJSON append-blob, 인스턴스 내 60초/100건 버퍼링, shutdown flush
- [ ] `logs/<yyyy>/<mm>/<dd>/<HH>.ndjson` 시간대별 분리 적재
- [ ] **`analyze_logs` Timer Trigger** (`0 0 22 * * *` UTC = KST 07:00)
  - [ ] 전일 24시간 분 NDJSON → pandas DataFrame
  - [ ] 시간대 × 페르소나 / 시간대 × Top-20 티커 매트릭스
  - [ ] 7일 이동평균 ±2σ 특이점 탐지 (호출 급증, 신규 티커, 장문 응답)
  - [ ] K-means(K=24) on hour-of-day, DBSCAN on (ticker, hour) — 시간대 군집 자동 라벨
  - [ ] 결과 → `analysis/<date>.json` Blob 저장
  - [ ] 특이점 발생 시 운영자 텔레그램 푸시 알림
- [ ] Lifecycle policy — `logs/` 90일, `analysis/` 365일 자동 정리

---

### 🥉 후속 작업 (3·4차) — 학술 데이터 수집 / 모바일·멀티턴

> 1·2차 검수 후 별도 계획서로 분기. 본 항목은 §13 학술 동반 자료와 직접 연결됨.

**3차 — 의미적 캐싱 + 학술 데이터 수집**
- 4 컨테이너 (`research_query_embeddings`, `research_cache_events`, `research_latency`, `research_popularity_daily`) — §13.3
- Azure OpenAI `text-embedding-3-small` + DiskANN 벡터 인덱스
- 2-tier consent UI (operational / research-extended) — §13.5
- SHA-256 salt rotation 자동화 (Key Vault, 90일) — §13.4

**4차 — 모바일 + 멀티턴**
- React Native + Expo (iOS/Android) — 동일 백엔드 호출
- 멀티턴 컨텍스트 영속화 (`chat_history` 컨테이너, TTL 30일)
- 채널 비교 분석 (§13.7)

---

### 11.1 1차/2차 일정 가이드 (1인 풀타임 기준)

| 단계 | 예상 소요 | 비고 |
|---|---|---|
| 1차-A 기술 부채 | 2–3일 | H5 비동기 전환이 가장 큼 |
| 1차-B 영속 저장소 | 1–2일 | SQLite 단순 |
| 1차-C 6단계 플로우 | 3–5일 | InlineKeyboard + market_report 신규 |
| 1차-D 페르소나 보존 | 0.5일 | C와 함께 |
| 1차-E 검증 | 1–2일 | pytest + 수동 시나리오 |
| **1차 합계** | **약 8–13일** | |
| 2차-A Functions 화 | 2일 | |
| 2차-B Cosmos 이전 | 1–2일 | |
| 2차-C Timer + CDN | 2–3일 | |
| 2차-D 인프라 코드 | 2일 | Bicep 익숙도에 따라 변동 |
| 2차-E 관측성 | 1일 | |
| 2차-F 부하 검증 | 1일 | |
| **2차 합계** | **약 9–11일** | |

---

## 12. 리스크 및 미해결 항목

| 리스크 | 영향 | 완화 |
|---|---|---|
| yfinance가 비공식 API라 갑자기 차단/스로틀 | 데이터 공급 중단 | Polygon.io / Alpha Vantage / Finnhub 백업 supplier 준비 |
| DeepSeek API 가격 변동 / 서비스 정책 변경 | 비용 또는 가용성 | 환경 변수로 base_url + model 분리되어 있어 OpenAI / Anthropic 으로 즉시 스위치 가능 |
| 텔레그램 정책 변경 — 봇 metering | 운영 중단 | 모바일 앱 채널을 Phase 4에서 미리 구축 |
| LLM 환각으로 잘못된 수치 응답 | 사용자 손실 가능 | 시스템 프롬프트 + 데이터 블록 외 수치 사용 금지 + 면책 1줄 강제 (현행) |
| 한국 자본시장법 — 유사투자자문업 등록 의무 | 법적 리스크 | (1) "자문 아님" 면책 강조 (2) 매수/매도 추천 표현 금지 (이미 시스템 프롬프트에서 차단) (3) 변호사 검토 후 약관 작성 |
| Cosmos DB 비용 급증 (벡터 인덱스) | 월 비용 급등 | 90일 TTL + serverless tier로 상한 |

---

## 13. 연구 데이터 수집 계획 (학술 동반 자료)

> 이하 §13 은 IEEE Trans. Cloud Computing 투고 예정 논문 *"Semantic Edge Caching for Repetitive LLM Queries"* 의 동반 자료입니다. 본 챗봇 서비스 자체가 데이터 수집 플랫폼 역할을 합니다.

### 13.1 Abstract

This section specifies the data collection methodology for empirically validating the hypotheses presented in *"Semantic Edge Caching for Repetitive LLM Queries"*. Where the original paper relies primarily on simulation, this companion plan describes how the deployed AI Investor chatbot serves as a real-world data collection platform across two channels (Telegram and mobile native apps) under the low-cost serverless architecture defined in §7. The plan covers: (1) mapping of the paper's five core hypotheses to measurable signals, (2) anonymization and consent protocols satisfying Korean PIPA and GDPR, (3) Azure Cosmos DB schema with automatic TTL policies, (4) channel-stratified statistical analysis methods, and (5) ethics review preparation including IRB exemption justification.

**Keywords**: Semantic Caching, LLM Inference, CDN-inspired Architecture, Empirical Validation, Anonymized Telemetry, Multi-channel Data Collection

### 13.2 Hypothesis Mapping

| Paper Section | Claim | Measurement |
|---|---|---|
| §3 Query Repetition | Human queries follow repetitive statistical patterns | Repetition rate per command/ticker/hour |
| §4 Statistical Model | Query popularity follows Zipf distribution | Daily aggregation + MLE on Zipf exponent |
| §6 Semantic Cache Pipeline | Embedding ANN identifies semantically equivalent queries above threshold | Cosine similarity distribution + user feedback correlation |
| §7 Predictive Cache Warming | Trending signals enable proactive cache population | Pre-warming 30min before market open + A/B comparison |
| §11–14 Hit Rate / GPU / Cost / Energy | 60–90% hit rates → proportional savings | Direct measurement from `research_cache_events` + DeepSeek billing |

**Plan-introduced auxiliaries**:
- **H6 (Channel-clustered queries)**: Telegram vs. mobile distinguishable via KS test on length, command, time-of-day distributions.
- **H7 (Time-clustered queries)**: Same KST hour queries form semantic clusters in embedding space — silhouette score on K-means.

### 13.3 Cosmos DB 컨테이너 (4종)

`research_query_embeddings` (TTL 90d), `research_cache_events` (TTL 90d), `research_latency` (TTL 90d), `research_popularity_daily` (TTL 365d). 모든 컨테이너 partition key = `/date`, embedding 컨테이너만 DiskANN 벡터 인덱스.

스키마 상세는 (이전 v1.0 문서의 §4) 와 동일하며, 변경점은 다음 두 가지:
- 채널 enum에 `mobile_ios`, `mobile_android` 추가됨 (Phase 4)
- `model_used` 필드에 `cache | deepseek-v4-flash | deepseek-v4-pro` 외에 `cdn_warm` 추가 — §7.6 사전 생성 캐시 적중 케이스 구분용

### 13.4 익명화

```
anon_user_id = sha256(salt + ":" + raw_user_id)[0:16]
```

salt는 Azure Key Vault에 보관되어 로그에 절대 노출되지 않으며 90일 주기로 자동 rotation. PII 패턴(주민번호 / 카드번호 / 이메일) 정규식 redaction은 raw query text 저장 직전에 적용.

### 13.5 2-tier Consent

| Tier | 기본값 | 수집 |
|---|---|---|
| Operational | opt-out 만 가능 | anon_user_id, channel, command, embedding, cache event, latency, KST hour |
| Research-extended | opt-in | 위 + raw query text |

`/research_revoke` 명령으로 언제든 raw text 기록 일괄 삭제 가능 (anon_user_id 매칭).

### 13.6 첫 응답 시 1회 안내 (§6.4 / Phase 1과 결합)

```
"AI Investor를 사용해 주셔서 감사합니다.

• AI 응답에 오류가 있을 수 있습니다.
• 익명화된 사용 데이터가 서비스 개선과 학술 연구에 활용됩니다.
• 개인 정보는 식별 불가능한 형태로만 보관되며 90일 후 자동 삭제됩니다.
• 본 서비스는 투자 자문이 아닙니다.

[연구 데이터 수집에 추가 동의 — 가장 도움됩니다]
[운영 데이터만 — 기본]
[전체 정책 보기]"
```

### 13.7 채널 비교 분석 (H6)

| 차원 | 통계 검정 |
|---|---|
| 길이 분포 | Two-sample Kolmogorov–Smirnov |
| 시간대 분포 | Chi-square (24-bin histogram) |
| 캐시 적중률 | Two-proportion z-test |
| 지연시간 | Mann–Whitney U (heavy-tailed) |
| 페르소나 선호 | Chi-square independence |
| 후속 질의율 (60s 내) | Two-proportion z-test |

다중 검정 보정: Bonferroni (n=6).

### 13.8 통계 분석

- **Cache hit rate**: 7일 rolling, 95% Wilson score CI
- **Zipf fit**: MLE로 exponent s 추정, KS goodness-of-fit
- **Time clustering (H7)**: PCA 1536→50 + K-means K=24 + silhouette + UMAP 시각화
- **Pre-warming A/B**: day-level alternation, bootstrap CI
- **Cost / Energy**: DeepSeek billing 그대로, 에너지는 발표된 per-token 추정치

### 13.9 IRB / 컴플라이언스

| 관할 | 규정 | 적용 |
|---|---|---|
| 한국 | 개인정보보호법 (PIPA) | 1차 적용 |
| 한국 | 생명윤리법 (IRB) | 면제 신청 — 관찰적 telemetry, 익명화, 무중재 |
| EU | GDPR | EU 모바일 사용자 대비, 잊혀질 권리 §13.4 |
| US | Common Rule | 비적용, 단 substantive 요구사항 준수 |

**Exemption arguments**: (1) 무중재 관찰, (2) 식별 불가능한 정보, (3) Azure 표준 보호, (4) 최소 위험.

### 13.10 데이터 공개 계획

- 일일 집계 통계 (시간대별 hit rate, Zipf 파라미터) — IEEE Dataport CSV 부록
- De-identified 이벤트 데이터 — 별도 publication-specific salt로 재해시 후 controlled access
- Raw query text — **공개하지 않음**

### 13.11 Threats to Validity (Wohlin et al.)

- **Internal**: pre-warming은 user-level RCT가 아닌 day-level alternation
- **External**: 금융 도메인·한국어·텔레그램+모바일 mix 조건부 결과
- **Construct**: 캐시 임계값 0.93은 경험치 — 0.90/0.93/0.95 sensitivity 보고
- **Conclusion**: 다중 검정 — Bonferroni 또는 Benjamini–Hochberg

### 13.12 학술 일정

| 마일스톤 | 트리거 | 활동 |
|---|---|---|
| M1 텔레메트리 가동 | Phase 2 완료 | Cosmos 4 컨테이너 + 익명화 production |
| M2 텔레그램 30일 데이터 | M1 + 30일 | 사전 분석 |
| M3 모바일 출시 | Phase 4 완료 | 양 채널 동시 수집 |
| M4 충분한 모바일 표본 | M3 + 60일 | 채널 비교 가능 |
| M5 통계 분석 완료 | M4 + 30일 | §11–14 + H6/H7 |
| M6 논문 재투고 | M5 + 14일 | IEEE TCC 제출 |

M1 → M6 약 4개월, IRB 지연 시 +2–3개월.

---

## 14. 지역별 지연 분석 — 콜드 스타트·레이턴시 (참고)

> **상태**: 참고 자료 — 추후 결정 항목.
> **전제**: 사용자 페르소나 조회 로직이 §7.3 의 *Azure Functions 인메모리 캐싱(TTL 5분) + Blob Storage 직접 읽기* 구조라는 가정.
> **출처**: 실측 azping 데이터, Azure Storage 성능 메트릭, 오픈소스 CDN 테스트 결과 종합. 서울 리전(Korea Central) **단일 배포** 기준.

### 14.1 지역별 End-to-End 지연 시간 예측

#### 한국 내 사용자

| 단계 | 구간 | 예상 지연 | 비고 |
|---|---|---|---|
| ① 사용자 → Functions | 국내 ISP → 서울 리전 | 2–10 ms | azping 측정값 82.85 ms 대비 실 체감 더 낮음 |
| ② Functions 처리 (웜) | 인메모리 캐시 적중 | 5–20 ms | 페르소나 TTL 5분 이내 재요청 |
| **③ 총 E2E (캐시 적중)** | Blob 읽기 생략 | **≈ 7–30 ms** | 최상의 성능 |
| ②′ Functions 처리 (콜드) | 콜드 스타트 + Blob 읽기 | 1–10 s | 신규 인스턴스 할당 + Python 의존성 로딩 |
| ③′ Blob Storage 서버 지연 | 동일 리전 내 | < 50 ms | 표준 블롭 단일 요청 |
| **④′ 총 E2E (콜드 + Blob)** | | **≈ 2–11 s** | 최악의 성능 |

#### 일본 사용자

| 단계 | 구간 | 예상 지연 | 비고 |
|---|---|---|---|
| ① 사용자 → Functions | 일본 ISP → 서울 리전 | 30–80 ms | 한일 해저 케이블 경유 |
| ② Functions 처리 (웜) | 인메모리 캐시 적중 | 5–20 ms | |
| **③ 총 E2E (캐시 적중)** | Blob 읽기 생략 | **≈ 35–100 ms** | |
| ②′ Functions 처리 (콜드) | 콜드 스타트 + Blob 읽기 | 1–10 s | |
| **④′ 총 E2E (콜드 + Blob)** | | **≈ 2–11 s** | |

#### 동남아시아 사용자 (싱가포르 기준)

| 단계 | 구간 | 예상 지연 | 비고 |
|---|---|---|---|
| ① 사용자 → Functions | 동남아 ISP → 서울 리전 | 70–150 ms | 지리적 거리 |
| ② Functions 처리 (웜) | 인메모리 캐시 적중 | 5–20 ms | |
| **③ 총 E2E (캐시 적중)** | Blob 읽기 생략 | **≈ 75–170 ms** | |
| ②′ Functions 처리 (콜드) | 콜드 스타트 + Blob 읽기 | 1–10 s | |
| **④′ 총 E2E (콜드 + Blob)** | | **≈ 2–11 s** | |

### 14.2 Azure CDN 적용 시 지연 시간 변화

CDN은 **공개 데이터(시황 요약, 상승/하락 종목 리스트 등)** 에만 적용 가능. 개인화된 사용자 페르소나 데이터에는 적용할 수 없습니다. 단, 공개 데이터의 체감 성능은 지역별로 크게 개선됩니다.

#### 14.2.1 Azure CDN 엣지 노드 (아시아 지역)

| 지역 | CDN POP 위치 |
|---|---|
| 한국 | 서울 |
| 일본 | 도쿄(3), 오사카(2) |
| 동남아시아 | 싱가포르(6), 방콕, 자카르타, 호치민 등 |

Azure CDN은 109개 대도시에 192개 글로벌 엣지 노드 보유. 싱가포르에 6개 노드가 집중 배치되어 동남아시아 트래픽 처리에 유리합니다.

#### 14.2.2 CDN 적용 시 지연 개선 효과

| 사용자 지역 | CDN 미적용 (직접 Blob) | CDN 적용 시 | 개선 효과 |
|---|---|---|---|
| 한국 | 2–10 ms | 10–50 ms | Blob 원본 접근 대비 안정적 |
| 일본 | 30–80 ms | 40–55 ms | 백본 최적화로 150 ms → 50 ms 수준 개선 |
| 동남아시아 | 70–150 ms | 50–80 ms | 싱가포르 6개 POP 활용 |

> **핵심**: CDN은 공개 시황 데이터 조회 시에만 적용 가능하며, 사용자 페르소나 조회는 여전히 Functions → Blob Storage 경로를 따릅니다. 다만 Azure CDN의 아시아 커버리지가 우수해 공개 데이터는 전 지역에서 50–80 ms 이내 일관된 성능 기대 가능.

### 14.3 콜드 스타트 영향 최소화 전략

증권당 챗봇이 장 마감 시간(KST 06:00 부근)에 트래픽이 집중되는 패턴을 보일 경우, 다음 방안으로 콜드 스타트 영향 감소 가능:

| 전략 | 설명 | 효과 |
|---|---|---|
| **타이머 트리거 웜업** | 5분 간격 더미 호출로 인스턴스 유지 | 콜드 스타트 발생률 약 90% 감소 |
| **Flex Consumption Plan (Always Ready 1)** | 최소 1개 인스턴스 상시 준비 | 콜드 스타트 완전 제거, 비용은 약간 증가 (월 +$13 수준) |
| **패키지 경량화** | 불필요한 의존성 제거 | 콜드 스타트 시간 30–50% 단축 |

§7.7 의 콜드 스타트 대응과 §11 2차-F 부하 검증 항목과 연계됩니다. 본 §14 의 정량 추정치는 부하 테스트 시 검증·보정 대상이며, 결과에 따라 해당 전략 채택 여부를 최종 결정합니다.

---

## 15. 진행 현황 (2026-05-05 23:10 KST 기준)

### 15.1 작업 진행률 요약

| 영역 | 상태 | 비고 |
|---|---|---|
| **1차-A 기술 부채** | ✅ **완료** | H1/H2/H3/H4/H5/M2/M5 모두 반영 |
| **1차-B 영속 저장소** | ✅ **완료** | SQLite `UserProfileRepo` + `delete()` 추가 |
| **1차-C 6단계 플로우** | ✅ **완료** | `services/market_report.py` 신설, 라이브 yfinance + DeepSeek 페르소나 코멘트 + 4언어 렌더링 |
| **1차-D 페르소나 교체 컨텍스트 보존** | ✅ **완료** | `persona_changed` + `_format_interests` |
| **1차-E 검증** | ✅ **완료** | pytest **53건** 통과, `requirements.lock` 생성 |
| **신규: /forget 명령** | ✅ **완료** | 인라인 키보드 재확인 → SQLite row 삭제 (Azure Blob 이전 시 동일 인터페이스) |
| **신규: /policy 명령** | ✅ **완료** | 4개 언어 정책 본문 (`/forget` `/lang` `/persona` 안내 포함) |
| **종단 수동 시나리오** | ✅ **완료** | §15.6 12케이스 체크리스트 문서화 |
| **다국어 티커 매핑 확장** | ✅ **완료** | NASDAQ 200+ / S&P 500 mega-large + 한국인 인기 ETF 60+ — **931 alias / 252 unique ticker** (영/한/일/중 + 약칭). 21개 카테고리 100% 커버 |
| **2차-A Functions 화** | ✅ **scaffold 완료** | `function_app.py` (webhook + daily_report Timer + keepalive) + `host.json` + `.funcignore` |
| **2차-B Blob+TTL5분 캐시** | ✅ **scaffold 완료** | `BlobUserProfileRepo` (ETag concurrency) + `STORAGE_BACKEND` 자동 선택 factory + `aiosqlite` 호환 |
| **2차-C Timer + Blob + CDN** | ✅ **scaffold 완료** | `BlobReportWriter` 12개 (3 페르소나 × 4 언어) Blob 업로드 + CDN purge + 핸들러 cache-first fetch |
| **2차-D Bicep + Actions** | ✅ **scaffold 완료** | `infra/main.bicep` (Storage / KV / Functions Flex / CDN / App Insights / RBAC) + `setup-azure.sh` + `.github/workflows/deploy-aiinvestor.yml` |
| **2차-E 관측성** | 🟡 **부분** | App Insights instrumentation 활성화됨 (`requests` + `traces`). `dependencies` 자동 instrument는 후속 |
| **2차-F 부하 / G 로그+배치** | ⏳ **대기** | 응답 지연 안정화 후 |
| **2차-H 사전 캐싱 데몬 (§16)** | ⏳ **신규 작업 명세** | TOP_50 종목 응답시간 ~7s → ~1.5s 예상 |
| **응답 지연 진단·수정** | ✅ **완료** ([postmortem.md](postmortem.md)) | 8.3s → 4.5–5.5s (예상). bot.initialize 1회 + max_tokens=550 + yfinance cache |
| **사용자 액션** | ⏳ **대기** | `brew install azure-cli gh jq` → `./infra/setup-azure.sh prod` → app secret 4개 → push |
| **3·4차 (학술 / 모바일)** | ❌ **미착수** | 의도된 후순위 |

### 15.2 코드 모듈 현재 상태

| 파일 | 라인 | 상태 |
|---|---|---|
| [main.py](main.py) | 48 | ✅ DI 와이어링 + `allowed_updates` 좁힘 + UserProfileRepo 통합 |
| [config.py](config.py) | 51 | ✅ `USER_ID_SALT`, `SQLITE_PATH` 추가 |
| [bot/telegram_handler.py](bot/telegram_handler.py) | 430 | ✅ 6단계 플로우 + 인라인 키보드 + 콜백 라우팅 + i18n |
| [services/i18n.py](services/i18n.py) | 253 | ✅ 4개 언어 (ko/en/ja/zh), 강화된 면책, 페르소나 언어 지시 |
| [services/persona_engine.py](services/persona_engine.py) | 161 | ✅ `AsyncOpenAI`, `timeout=20s`, 다국어 페르소나, 관심사 컨텍스트 주입 |
| [services/user_profile.py](services/user_profile.py) | 140 | ✅ SQLite 기반 `UserProfileRepo` |
| [services/stock_service.py](services/stock_service.py) | 164 | 🟡 변경 없음. M2(회사명→티커) 미구현 |
| services/market_report.py | — | ❌ **미생성** (1차-C [4]단계 placeholder만 i18n에 존재) |
| tests/ | — | ❌ **미생성** (1차-E) |

### 15.3 검증 완료된 동작

- 4개 언어 라우팅: `ko` / `en-US` / `ja` / `zh-Hans` / 미지원→`en` ✅
- SQLite 영속화 라운드트립 (생성→갱신→재조회): persona, tags, tickers 정확 보존 ✅
- 봇 부팅 + 텔레그램 폴링 + DeepSeek API 호출 ✅
- 면책 강화 메시지 4개 언어 출력 ✅

### 15.4 봇 상태

- 마지막 가동 PID: 종료됨 (graceful)
- SQLite 파일: `data/aiinvestor.db` (사용자 2명, 마지막 갱신 2026-05-05 14:07 UTC)
- 재기동 명령: `cd AIInvestor && .venv/bin/python main.py` 또는 `nohup .venv/bin/python main.py > /tmp/ai_investor.log 2>&1 & disown`

---

### 15.5 향후 2시간 안에 마무리 가능한 작업 — 권장 체크리스트

다음 항목은 모두 **로컬에서 완결 가능**하며, 2차(Azure) 작업의 전제조건을 충족시켜 클라우드 이전 즉시 시작할 수 있는 상태로 만듭니다. 우선순위 순:

#### A. **1차-C [4] 일일 시황 리포트 본문** — 예상 50분 ⭐⭐⭐ (가장 사용자 가치 큼)

- [ ] `services/market_report.py` 신설
  - [ ] `MarketReport` dataclass (S&P/NASDAQ/NDX 종가·변동 + Top5 상승/하락 + 페르소나 코멘트)
  - [ ] `MarketReportService.build(persona, profile, language)` — yfinance `^GSPC`/`^IXIC`/`^NDX` + NASDAQ-100 100개 일괄 다운로드 ([QQQUpDownSignal/qqq_up_down_signal.py](../QQQUpDownSignal/qqq_up_down_signal.py) 재사용)
  - [ ] DeepSeek로 페르소나별 한 줄 코멘트 생성 (사용자 언어, 관심사 반영)
  - [ ] 단일 프로세스 인메모리 캐시 (`dict[date, MarketReport]`, TTL 24h)
- [ ] [bot/telegram_handler.py:227](bot/telegram_handler.py) `report:show` 콜백 분기에서 placeholder 제거하고 `MarketReportService` 호출로 교체
- [ ] 4개 언어 i18n 키 추가 — 리포트 헤더 ("📊 오늘의 시황" / "📊 Today's Market" / "📊 本日の市況" / "📊 今日的市场")

**완료 기준**: 텔레그램에서 [예, 보기] 누르면 페르소나 톤으로 실 시황 데이터 + 한 줄 코멘트가 사용자 언어로 회신됨.

#### B. **1차-A M2 회사명→티커 매핑** — 예상 25분 ⭐⭐ (UX 핵심)

- [ ] `services/ticker_lookup.py` 신설 — S&P 500 + NASDAQ-100 약 600 종목 매핑 (`{"애플": "AAPL", "테슬라": "TSLA", "アップル": "AAPL", "苹果": "AAPL", ...}` 다국어 별칭)
- [ ] [services/stock_service.py:79](services/stock_service.py#L79) `_normalize` 가 한글/일본어/중국어 회사명 입력 시 매핑 테이블 조회 후 `query.upper()` 로 fallback
- [ ] CSV로 외부 분리 (`data/ticker_aliases.csv`) → 코드와 데이터 분리

**완료 기준**: "테슬라", "엔비디아", "アップル", "苹果" 입력 시 정상적으로 yfinance 조회.

#### C. **1차-E pytest 최소 세트** — 예상 25분 ⭐⭐ (회귀 방지)

- [ ] `tests/__init__.py`, `tests/conftest.py`
- [ ] `tests/test_user_profile.py` — in-memory SQLite (`":memory:"`) 로 격리, 생성/갱신/JSON 직렬화/anon_user_id 결정성
- [ ] `tests/test_i18n.py` — `normalize_language` 4언어 + fallback, 모든 `_Bundle` 필드가 모든 언어에 존재
- [ ] `tests/test_intent_classifier.py` — `TICKER_RE` 매칭 케이스 (정상/한글/긴 문자열/특수문자)
- [ ] `pytest.ini` — `[pytest]` 기본 설정
- [ ] `pip install pytest` + `requirements-dev.txt` 분리

**완료 기준**: `.venv/bin/pytest` 가 녹색.

#### D. **`requirements.lock` 생성 (L4)** — 예상 5분 ⭐

- [ ] `pip install pip-tools` → `pip-compile requirements.txt --output-file requirements.lock`
- [ ] README에 잠금 파일 사용법 1줄 추가

#### E. **운영자 `/forget` 명령** — 예상 15분 ⭐ (GDPR/PIPA 대비)

- [ ] [bot/telegram_handler.py](bot/telegram_handler.py) 에 `/forget` 명령 추가 — 본인의 `users` row 삭제 (SQLite). 2차 Azure 이전 시 동일 인터페이스로 Blob 삭제로 전환.
- [ ] 재확인 콜백 (`forget:confirm` / `forget:cancel`) — 실수 방지

#### 권장 진행 순서 (2시간 = 120분)

```
00:00–00:50  A. market_report.py 본문 구현 (50분)
00:50–01:15  B. 회사명→티커 매핑 (25분)
01:15–01:40  C. pytest 최소 세트 (25분)
01:40–01:55  E. /forget 명령 (15분)
01:55–02:00  D. requirements.lock + 최종 부팅 검증 (5분)
```

총 5개 항목 완료 시 **1차 작업이 100% 마감**되며, 2차 Azure 이전은 §9.4 의 계정 연결 정보만 확보되면 즉시 착수 가능합니다.

#### 보류 항목 정리 — 모두 처리됨

- ✅ `/policy` 명령 — 4개 언어 정책 본문 + `_cmd_policy` 핸들러 등록 ([bot/telegram_handler.py](bot/telegram_handler.py))
- ✅ 종단 수동 시나리오 — §15.6 에 12개 케이스 통과 기준으로 문서화

### 15.6 종단 수동 시나리오 — 1차 작업 완료 검증 체크리스트

각 케이스는 [@AI_vibe_investor_bot](https://t.me/AI_vibe_investor_bot) 에서 실행 후 결과를 ✓ / ✗ 로 표시. 12 케이스 모두 ✓ 시 1차 작업 종단 검증 완료.

| # | 시나리오 | 기대 결과 |
|---|---|---|
| 1 | 새 사용자가 `/start` | 인사말 + 언어 전환 안내 + 자기소개(면책 강화 2줄) + 페르소나 키보드 |
| 2 | 페르소나 [Ray Dalio] 클릭 | "✓ Ray Dalio 로 설정" + 오늘의 리포트 제안 |
| 3 | [예, 보기] 클릭 | yfinance 라이브 + DeepSeek 한 줄 코멘트 + 4언어 면책 + 관심사 입력 안내 |
| 4 | [AI 반도체] [ETF] 클릭 | 토글 표시(✓), `interest_tags` 갱신 |
| 5 | 자유 입력 "NVDA TSLA" | watchlist_tickers 에 NVDA / TSLA 추가, 분야 vs 종목 분리 메시지 |
| 6 | [✅ 완료] | "관심 분야 저장" + 자유 질의 초대 |
| 7 | 입력 "테슬라" | yfinance 가 TSLA 로 정상 조회 (다국어 매핑 동작) |
| 8 | 봇 종료 후 재기동, 동일 사용자가 메시지 발신 | 페르소나 / 관심사 / 언어 SQLite 영속 보존 확인 |
| 9 | `/persona` → 다른 페르소나 선택 | 인사말 + "관심 분야: AI 반도체, ETF — 그대로 유지" |
| 10 | `/lang` → English | 모든 후속 응답이 영어 (페르소나·관심사 그대로) |
| 11 | `/policy` | 4개 언어 정책 본문 출력 (`/forget` `/lang` `/persona` 안내 포함) |
| 12 | `/forget` → [Yes, delete] | "deleted" 메시지 + DB row 제거 (다음 `/start` 는 신규 사용자 플로우) |

각 케이스의 자동화 테스트는 pytest 49건이 단위·로직 레이어를 커버하며, 12개 종단 케이스는 텔레그램 라이브 환경 의존성으로 인해 수동 검증입니다.

---

## 16. 사전 캐싱 데몬 — 인기 종목·ETF Blob/CDN 사전 적재

> **상태**: 작업 명세 (구현 미착수). 본 §16 은 [postmortem.md](postmortem.md) §7.3 에서 도출된 후속 작업으로, Functions 응답시간을 **인기 종목 한정 1초 이하**로 단축할 수 있는 가장 효과적인 단일 개입.

### 16.1 동기 — 왜 사전 캐싱이 필요한가

[postmortem.md §3](postmortem.md) 의 분해에 따르면 사용자 응답 8.3초 중 **DeepSeek body 스트리밍이 84%(7초)** 를 차지함. 코드 최적화로는 이 7초를 절반 이하로 줄이기 어렵다. 그러나 **한국 retail 트래픽의 약 70–80%는 상위 50개 종목/ETF 에 집중** — 이 부분만 미리 응답을 만들어 놓으면 LLM·yfinance 호출 없이 CDN edge에서 바로 회신 가능.

### 16.2 핵심 아이디어

```
Timer Trigger (4시간마다, US 시장 마감 후 + 4시간 간격)
  └─ for ticker in PRIORITY_300:                       # 약 600개 (NASDAQ 300 + S&P 500 + 인기 ETF — 중복 제거)
      └─ snapshot = StockService.get_snapshot(ticker)
      └─ Blob upload: prewarm/snapshots/<TICKER>.json  # 24h TTL
  └─ for ticker in TOP_50:                              # 사용자 트래픽 분포 상위
      └─ for persona × language (3 × 4 = 12):
          └─ rendered = PersonaEngine.generate(...)
          └─ Blob upload: prewarm/commentary/<TICKER>.<persona>.<lang>.json

사용자 요청 흐름 변경:
  1. 메시지 도착 → ticker 매핑
  2. Blob에서 prewarm/commentary/<TICKER>.<persona>.<lang>.json 시도 (CDN edge)
       HIT  → 바로 회신 (LLM/yfinance 모두 우회)
       MISS → 다음 단계
  3. Blob에서 prewarm/snapshots/<TICKER>.json 시도
       HIT  → snapshot 재사용, DeepSeek만 라이브 호출
       MISS → 기존 경로 (yfinance + DeepSeek 둘 다)
```

### 16.3 종목 리스트 정의

| 카테고리 | 출처 | 갯수 |
|---|---|---|
| NASDAQ-100 | yfinance ^NDX 구성 종목 (이미 [QQQUpDownSignal](../QQQUpDownSignal)에 있음) | 100 |
| NASDAQ Top 200 (Composite) | 시가총액 상위, 동적 fetch | 200 |
| S&P 500 mega/large caps | Wikipedia 또는 yfinance ^GSPC top by market cap | 200 (NASDAQ과 중복 제외) |
| 한국인 인기 ETF | [data/ticker_aliases.csv](data/ticker_aliases.csv) ETF 60종 | 60 |
| 한국인 인기 추가 종목 | 텔레그램 트래픽 분석 결과 (TOP_50 동적 갱신) | 50 |
| **합계 (중복 제거)** | | **~600** |

`data/priority_tickers.csv` 로 분리 관리. 매 timer 실행 시 이 CSV를 읽어 그 시점의 600개 종목을 처리.

### 16.4 TOP_50 의 동적 결정

처음에는 정적 리스트로 시작 (AAPL, NVDA, TSLA, MSFT, GOOGL, META, AMZN, AVGO, QQQ, SPY, SCHD, JEPI, ... 약 50개).

§13 학술 데이터 수집이 가동된 이후 (3차 작업 완료 후) `research_popularity_daily` 의 7일 누적 ticker frequency 상위 50개로 자동 갱신. 시드 트래픽이 쌓이기 전까지는 정적 리스트.

### 16.5 캐시 무효화 정책

| 데이터 | 갱신 주기 | 이유 |
|---|---|---|
| `prewarm/snapshots/<TICKER>.json` | 4시간 | 실시간 가격은 부정확하지만 페르소나 분석 용도로는 충분. yfinance rate limit 고려 |
| `prewarm/commentary/<TICKER>.<persona>.<lang>.json` | 24시간 | 페르소나 톤·로직은 빠르게 안 바뀜. 일중 시황은 별도 daily_report에서 처리 |
| 인덱스 종가 변동 ±2% 이상 | 즉시 invalidate | 큰 변동 시 사전 캐시는 오래된 정보 — 라이브 fallback 강제 |

### 16.6 Blob 레이아웃

```
container "prewarm" (private + CDN origin)
├── snapshots/
│   ├── AAPL.json
│   ├── NVDA.json
│   └── ...
├── commentary/
│   ├── AAPL.buffett.ko.json
│   ├── AAPL.buffett.en.json
│   ├── AAPL.buffett.ja.json
│   ├── AAPL.buffett.zh.json
│   ├── AAPL.dalio.ko.json
│   └── ... (50 × 3 × 4 = 600 blobs)
└── _index.json    # 마지막 갱신 timestamp + 다음 schedule
```

### 16.7 비용 추정 (4시간 주기)

| 항목 | 수량 | 단가 | 일 비용 | 월 비용 |
|---|---|---|---|---|
| yfinance 호출 (스냅샷 갱신) | 600 × 6/일 = 3,600 | $0 | $0 | $0 |
| DeepSeek 호출 (commentary 갱신) | 50 × 12 × 1/일 = 600 | $0.0028/1k 토큰 | ~$0.30 | **~$9/월** |
| Blob storage | 600 + 600 = 1,200 객체 × ~5KB = 6MB | — | $0.0001 | **<$0.01** |
| Blob read (캐시 hit per request) | DAU 100 × 5/일 = 500/일 | $0.0004/10K | <$0.01 | <$0.30 |
| Timer Trigger Function 실행 | 6/일 × 약 5분 | included | $0 | **~$1** |
| **추가 합계** | | | | **~$10/월** |

기존 ~$16/월 + 사전 캐싱 ~$10/월 = **~$26/월**. 응답시간 단축 효과 대비 매우 합리적.

### 16.8 응답시간 영향 (예상)

| 사용자 요청 분류 | 빈도 | Before | After |
|---|---|---|---|
| TOP_50 + 인기 페르소나/언어 (캐시 hit) | ~70% | 5.5–8s | **0.5–1.5s** (CDN edge fetch만) |
| TOP_300 (snapshot hit, commentary miss) | ~15% | 5.5–8s | **3–4s** (yfinance 절감) |
| 그 외 (cold ticker) | ~15% | 5.5–8s | 5.5–8s (변화 없음) |
| **가중 평균** | | **~7s** | **~2.0s** |

### 16.9 작업 분할 — 2차-H

본 §16 을 paper_plan §11 의 **2차-H** 로 추가 (2차-G 다음):

#### 2차-H 작업 항목

- [ ] `data/priority_tickers.csv` — 600개 종목 정적 리스트 작성 ([data/ticker_aliases.csv](data/ticker_aliases.csv) 활용)
- [ ] `services/prewarm_service.py` 신설
  - [ ] `PrewarmService.refresh_snapshots(tickers)` — yfinance 일괄 다운로드 → Blob upload
  - [ ] `PrewarmService.refresh_commentaries(top_50)` — DeepSeek 호출 → Blob upload
  - [ ] `PrewarmService.maybe_invalidate(reason)` — 큰 시장 변동 시 강제 갱신
- [ ] `function_app.py` 에 Timer trigger 추가
  - [ ] `prewarm_snapshots`: `0 0 */4 * * *` (4시간마다)
  - [ ] `prewarm_commentaries`: `0 30 */4 * * *` (스냅샷 갱신 30분 후)
- [ ] `bot/telegram_handler.py` `_handle_ticker_query` 분기 추가
  - [ ] 1차 시도: `prewarm/commentary/...` Blob fetch
  - [ ] 2차 시도: `prewarm/snapshots/...` Blob fetch + DeepSeek 호출
  - [ ] 3차 fallback: 기존 라이브 경로
- [ ] App Insights 커스텀 메트릭 — `prewarm.cache_hit_rate`
- [ ] CDN(Front Door) 도입은 별도 PR — 본 작업은 Blob HTTPS 직접 사용으로 시작
- [ ] 단위 테스트 — `PrewarmService` mock yfinance + DeepSeek
- [ ] `paper_plan.md §15` 진행 현황 표 갱신

#### 2차-H 일정 가이드

| 단계 | 예상 소요 |
|---|---|
| `priority_tickers.csv` + `prewarm_service.py` | 0.5–1일 |
| Timer triggers + Blob upload | 0.5일 |
| 핸들러 cache-first 분기 + 테스트 | 0.5일 |
| 라이브 검증 + 메트릭 | 0.5일 |
| **합계** | **2–2.5일** |

### 16.10 §13 학술 작업과의 시너지

- 본 §16 의 cache hit rate 가 §13.2 의 H6/H7 hypothesis 검증 데이터로 직접 활용됨
- TOP_50 동적 갱신은 §13.3 의 `research_popularity_daily` 컨테이너 데이터를 그대로 입력으로 사용
- 즉 §16 (운영 효율) 과 §13 (학술 검증) 이 동일 데이터 파이프라인을 공유 — 중복 작업 없음

### 16.11 위험 / 미해결

- yfinance rate limit: 600 ticker × 6회/일 = 3,600 호출. yfinance 비공식 한도 ~2,000/시간 — 4시간 주기로 분산하면 하한선 통과. 그래도 batch download (`yf.download(tickers=list)`) 로 압축 권장
- DeepSeek 응답 품질이 시간에 따라 미세하게 다를 수 있음 (temperature=0.4 라도 완전 deterministic 아님). 사용자가 같은 ticker 24시간 안에 두 번 보내면 동일 응답이 캐시에서 회신 — UX 측면 의도된 동작
- TOP_50 외 ticker 의 첫 호출은 여전히 5–8초. UI 측면 명시 필요 ("자주 조회되는 종목은 즉시 응답")

---

**End of Document**

*수정·제안·재현 요청은 GitHub Issue로 부탁드립니다.*
