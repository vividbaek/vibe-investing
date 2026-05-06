# AI Investor

LLM 기반 텔레그램 챗봇 — 유명 투자자 페르소나로 미국 시황(NASDAQ / S&P 500)을 해설합니다.

- **상태**: MVP 가동 중 ([@AI_vibe_investor_bot](https://t.me/AI_vibe_investor_bot)), Azure 서버리스 이전 준비
- **백엔드 LLM**: DeepSeek (`deepseek-chat` / `deepseek-reasoner`) — OpenAI 호환 엔드포인트
- **데이터**: Yahoo Finance (yfinance)
- **저장소**: 1차는 로컬 SQLite, 2차에서 Azure Blob Storage 단일 계층 (사용자 프로필 / 일일 리포트 / 사용 로그) + 인스턴스 메모리 TTL 5분 캐시 + 일일 리포트 Azure CDN 사전 캐싱 + 로그 배치 분석 (시간대 군집·LLM 호출 특이점)

OpenAI에서 DeepSeek로 전환한 이유: ChatGPT는 실시간 데이터성 미반영 + 가격. DeepSeek는 API 호환성 + 금융 도메인 강점 + 1/35 비용.

> **Disclaimer**: 본 봇은 투자 자문 서비스가 아닙니다. AI가 생성한 응답은 부정확하거나 환각이 있을 수 있으며, 모든 응답 끝에 면책 한 줄이 강제됩니다. 투자 판단의 책임은 사용자에게 있습니다.

---

## 📑 단일 진실원본

본 프로젝트의 **아키텍처 / 사용자 플로우 / 코드 리뷰 / 개발 로드맵 / 학술 데이터 수집 계획** 은 모두 한 문서에 통합되어 있습니다:

→ **[paper_plan.md — 아키텍처 및 개발 계획 (v2.0)](paper_plan.md)**

함께 보는 자료:
- **[postmortem.md — 6초 응답 지연 진단·수정 기록](postmortem.md)** — Azure 배포 9회 실패→성공 + App Insights timeline 분해 + 두 핵심 병목(`async with` per-request, DeepSeek body 스트리밍) 식별. 같은 실수를 피하기 위한 체크리스트 포함.
- [LLM cost analysis.md](LLM%20cost%20analysis.md) — DeepSeek vs OpenAI/Anthropic/Qwen 비용 비교
- [.env.example](.env.example) — 환경 변수 템플릿

---

## 빠른 시작 (로컬 개발)

1. Telegram 봇 토큰 발급 ([@BotFather](https://t.me/BotFather)).
2. DeepSeek API 키 발급 ([platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)).
3. 환경 설정:

   ```bash
   cd AIInvestor
   cp .env.example .env
   # .env 열어서 TELEGRAM_BOT_TOKEN, DEEPSEEK_API_KEY 채우기
   chmod 600 .env
   ```

4. 가상환경 + 의존성:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate         # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. 실행:

   ```bash
   python main.py
   ```

추론 모델로 바꾸려면 `.env` 의 `DEEPSEEK_MODEL=deepseek-reasoner`.

---

## 텔레그램 명령

| 명령 | 동작 |
|---|---|
| `/start` | 6단계 온보딩 시작 (인사 → 소개 → 페르소나 → 오늘의 리포트 → 관심사 → 자유 질의) |
| `/persona` | 페르소나 인라인 키보드 (`buffett` / `dalio` / `wood`) — 관심사는 보존 |
| `/personas` | 사용 가능한 페르소나 목록 (현재 선택 표시) |
| `/lang` | 언어 전환 인라인 키보드 (`ko` / `en` / `ja` / `zh`) |
| `/policy` | 데이터 처리 정책 + 면책 (4개 언어) |
| `/forget` | 저장된 페르소나·관심사·언어 일괄 삭제 (재확인 키보드) |
| `/help` | 명령 목록 |
| 자유 입력 | 티커(`NVDA`) / 다국어 회사명(`테슬라`, `テスラ`, `特斯拉`) → yfinance 조회 → 페르소나 해설 (사용자 언어로) |

봇이 텔레그램 사용자 언어 코드(`language_code`)를 자동 감지하여 한국어 / 영어 / 일본어 / 중국어 중 선택하며, `/lang` 으로 언제든 전환 가능. 5단계 → 6단계 골든 패스 상세는 [paper_plan.md §6](paper_plan.md#6-사용자-플로우) 참조.

---

## 프로젝트 구조

```
AIInvestor/
├── main.py                       엔트리 포인트, DI 와이어링
├── config.py                     env 로딩 + 로깅
├── bot/
│   └── telegram_handler.py       6단계 온보딩 + 콜백 + i18n 라우팅
├── services/
│   ├── i18n.py                   4개 언어 번역 번들 (ko/en/ja/zh)
│   ├── persona_engine.py         AsyncOpenAI(DeepSeek) + 다국어 페르소나
│   ├── stock_service.py          yfinance 스냅샷 + 1년 변동률
│   ├── ticker_lookup.py          다국어 회사명 → 티커 (931 alias / 252 unique ticker)
│   ├── market_report.py          일일 시황 (S&P/NDX + Top 5) + 페르소나 코멘트
│   └── user_profile.py           SQLite UserProfileRepo (anon SHA-256)
├── data/
│   ├── ticker_aliases.csv        NASDAQ 200+ / S&P 500 mega-large + 인기 ETF — 영/한/일/중 + 약칭
│   └── aiinvestor.db             SQLite (자동 생성, .gitignore)
├── tests/                        pytest 49건 (user_profile / i18n / ticker)
├── requirements.txt
├── requirements.lock             pip-compile 잠금
├── pytest.ini
├── .env.example
├── README.md                     (이 파일)
├── paper_plan.md                 ★ 아키텍처 / 로드맵 / 코드 리뷰 / 학술 계획
└── LLM cost analysis.md          비용 비교
```

---

## 페르소나 추가 방법

[services/persona_engine.py:22](services/persona_engine.py#L22) 의 `PERSONAS` dict에 한 줄 추가하면 자동으로 `/personas`/`/persona` 에 노출됩니다.

```python
"munger": Persona(
    key="munger",
    display_name="Charlie Munger",
    system_prompt="You are Charlie Munger. Brief, blunt, mental-models...",
),
```

---

## 안전 장치 (현행)

- 시스템 프롬프트가 **데이터 블록 외 수치 환각을 금지** (현행 Buffett/Dalio/Wood 모두)
- **명시적 매수/매도 권고 금지** — 'I'd be inclined to wait' 같은 stance 표현으로 우회
- 모든 응답 끝에 `This is not financial advice.` 한 줄 강제
- 잘못된 티커 입력 시 친화적 에러 메시지

상세 위협 모델·점검 결과는 [paper_plan.md §5.4](paper_plan.md#54-보안--컴플라이언스-점검) 참조.

---

## 개발 로드맵 요약

| 우선순위 | 목표 | 환경 |
|---|---|---|
| **🥇 1차** | 6단계 사용자 플로우 + 영속 메모리 — 인사 → 소개 → 페르소나 → 오늘의 리포트 → 관심사 획득 → 기억 기반 소통 + 페르소나 교체. 봇 재시작 후에도 페르소나·관심사 유지 (`UserProfileRepo` SQLite) | 로컬 / 단일 호스트 |
| **🥈 2차** | Azure Functions Flex Consumption + Webhook + Timer 일일 리포트 사전 생성 + Blob → CDN 캐싱. 사용자 프로필 SQLite → **Blob Storage 단일 계층 (TTL 5분 메모리 캐시)** 이전. 사용 로그 NDJSON 적재 + 배치 분석(시간대 군집·LLM 특이점). GitHub Actions 자동 배포 | Azure |
| 🥉 후속 (3·4차) | 의미적 캐싱 + 텔레메트리(학술 데이터 수집), 모바일(iOS/Android) + 멀티턴 | Azure 확장 |

상세 작업 체크리스트는 [paper_plan.md §11](paper_plan.md#11-개발-로드맵) 에 1차/2차로 분리되어 정리되어 있습니다.

---

## 알려진 한계

- yfinance는 비공식 API — 일부 필드 누락 / 일시적 차단 가능 (백업 supplier 준비 중)
- 페르소나 상태가 인메모리 — 봇 재시작 시 소실 (Phase 2에서 Cosmos DB로 영속화)
- 동기 LLM 호출이 asyncio 이벤트 루프를 블록 — 동시 사용자 ≥ 2 시 지연 누적 (Phase 0에서 `AsyncOpenAI` 전환)
- 응답 스트리밍 미지원

---

## 주의

본 서비스는 Vibe Investing 프로젝트의 실증 테스트용이며, AI Quant 페르소나 연구의 개발 진행 결과물입니다. 따라서 AI의 환각 및 오류가 발생할 수 있습니다.
