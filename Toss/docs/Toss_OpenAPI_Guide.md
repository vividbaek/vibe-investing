# 토스증권 Open API 기술 분석 문서

**활용 시나리오, 트레이딩 봇 설계 및 API 엔드포인트 정리**

> 작성일: 2026-06-05 | 기준 스펙: OpenAPI v1.0.3 (20 endpoints) | 서비스 상태: 사전 신청 단계 (정식 오픈일 미정)

---

## 1. 서비스 개요

토스증권 Open API는 국내주식과 해외주식(미국)을 단일 인터페이스로 다루는 통합 REST API 서비스다. 토스증권 계좌 보유 고객 대상으로 2026년 5월부터 사전 신청을 받기 시작했으며, 2026년 6월 2일 공식 개발자 문서와 OpenAPI 스펙이 공개됐다. 정식 오픈일은 아직 미정이며, 사전 신청자는 순차적으로 오픈 알림을 받은 뒤 토스증권 PC 웹사이트에서 API 키(client_id / client_secret)를 발급받아 사용하게 된다.

| 항목 | 내용 |
|---|---|
| 개발자 문서 | `https://developers.tossinvest.com/docs` (AI 에이전트용 `/llms.txt` 별도 제공) |
| OpenAPI 스펙 | `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json` (v1.0.3, 20개 엔드포인트) |
| Base URL | `https://openapi.tossinvest.com` (예제 코드 기준 `/v1` prefix) |
| 프로토콜 | REST (마케팅 페이지에는 WebSocket 언급이 있으나 현행 스펙에는 미포함) |
| 인증 | OAuth 2.0 Client Credentials Grant |
| 대상 시장 | 국내주식, 해외주식(미국) — 선물옵션·채권은 미지원 |
| 수수료 | 기존 토스증권 계좌 요율과 동일 (국내주식은 2026년 6월까지 면제, 이후 KRX 0.015% / NXT 0.014%) |
| 키 발급 | 토스증권 PC 웹사이트에서 발급 (사전 신청 후 순차 오픈) |

경쟁 구도 측면에서는 한국투자증권(KIS Developers)이 선점한 리테일 REST API 시장에 키움증권에 이어 토스증권이 진입하는 형태다. 토스증권의 차별점은 두 가지로 요약된다. 첫째, 국내·해외 주식을 하나의 API 표면으로 통합했다는 점. 둘째, ChatGPT·Claude 등 외부 LLM 환경에 API 키를 연동해 대화형 명령으로 계좌 분석을 수행하는 AI 친화적 설계를 전면에 내세웠다는 점이다.

---

## 2. 인증 구조 및 토큰 정책

인증은 OAuth 2.0 Client Credentials 방식이다. 트레이딩 봇 설계 시 토큰 수명 관리가 핵심 제약이므로 아래 정책을 정확히 반영해야 한다.

| 항목 | 정책 |
|---|---|
| 토큰 발급 | `POST /oauth2/token` 에 client_id + client_secret (form-urlencoded) 전송 |
| 토큰 형식 | Bearer access_token |
| 유효기간 | 86,400초 (24시간) |
| Refresh Token | 없음 — 만료 전 client_secret으로 재발급하는 로직을 직접 구현해야 함 |
| 동시 토큰 | client당 유효 토큰 1개 (재발급 시 기존 토큰 무효화 가능성에 유의) |
| 필수 헤더 | 계좌·자산·주문 API는 `Authorization: Bearer` 외에 `X-Tossinvest-Account` 헤더 필수 |

공식 페이지에 게시된 주문 예제 코드의 구조는 다음과 같다.

```python
BASE = "https://openapi.tossinvest.com/v1"
HEADERS = {
    "Authorization": f"Bearer {token}",
    "X-Tossinvest-Account": "{accountSeq}",
}

def buy(symbol, qty, price):
    return requests.post(f"{BASE}/orders", headers=HEADERS, json={
        "symbol": symbol,
        "side": "BUY",
        "orderType": "LIMIT",
        "quantity": qty,
        "price": price,
    }).json()
```

---

## 3. API 엔드포인트 전체 리스트

OpenAPI 스펙 v1.0.3 기준 20개 엔드포인트를 기능 카테고리별·호출 순서별로 정리했다. 실전 워크플로우에서 호출하게 되는 순서(인증 → 계좌 → 시세/종목 → 주문 보조 → 주문 실행 → 주문 조회)를 따른다.

### 3.1 인증

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 1 | `POST /oauth2/token` | 액세스 토큰 발급 (Client Credentials) |

### 3.2 계좌·자산 조회

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 2 | `GET /api/v1/accounts` | 보유 계좌 목록 조회 (X-Tossinvest-Account 값 확보) |
| 3 | `GET /api/v1/holdings` | 보유 종목(포지션) 조회 |

### 3.3 시세 조회

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 4 | `GET /api/v1/prices` | 현재가 조회 |
| 5 | `GET /api/v1/orderbook` | 호가 조회 |
| 6 | `GET /api/v1/trades` | 체결 내역(틱) 조회 |
| 7 | `GET /api/v1/candles` | 캔들(차트) 조회 — 1분봉·일봉만 지원 |

### 3.4 종목·시장 정보

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 8 | `GET /api/v1/stocks` | 종목 정보 조회 |
| 9 | `GET /api/v1/price-limits` | 가격 제한(상·하한가 등) 조회 |
| 10 | `GET /api/v1/market-calendar/KR` | 국내 시장 휴장일·개장 캘린더 |
| 11 | `GET /api/v1/market-calendar/US` | 미국 시장 휴장일·개장 캘린더 |
| 12 | `GET /api/v1/exchange-rate` | 환율 조회 (해외주식 KRW 환산) |

### 3.5 주문 보조 (사전 검증)

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 13 | `GET /api/v1/buying-power` | 매수 가능 금액 조회 |
| 14 | `GET /api/v1/sellable-quantity` | 매도 가능 수량 조회 |
| 15 | `GET /api/v1/commissions` | 수수료 조회 |

### 3.6 주문 실행 및 조회

| No. | 엔드포인트 | 기능 |
|---|---|---|
| 16 | `POST /api/v1/orders` | 주문 생성 (매수/매도, 지정가/시장가) |
| 17 | `POST /api/v1/orders/{orderId}/modify` | 주문 정정 |
| 18 | `POST /api/v1/orders/{orderId}/cancel` | 주문 취소 |
| 19 | `GET /api/v1/orders` | 주문 목록 조회 (미체결 포함) |
| 20 | `GET /api/v1/orders/{orderId}` | 개별 주문 상태 조회 |

---

## 4. 활용 시나리오 및 API 호출 순서

아래 6개 시나리오는 현행 스펙의 20개 엔드포인트만으로 구현 가능한 범위를 기준으로 설계했다. 각 시나리오마다 호출해야 하는 API를 실행 순서대로 명시한다.

### 시나리오 1 — 기본 지정가 트레이딩 봇 (매수 → 체결 추적)

가장 단순한 형태의 자동 주문 봇. 주문 전 검증 단계를 반드시 거치는 것이 안전 설계의 핵심이다.

| 순서 | API | 역할 |
|---|---|---|
| 1 | `POST /oauth2/token` | 토큰 발급 |
| 2 | `GET /api/v1/accounts` | 계좌 식별자 확보 (X-Tossinvest-Account) |
| 3 | `GET /api/v1/prices` | 현재가 확인 |
| 4 | `GET /api/v1/orderbook` | 호가 스프레드 확인 → 지정가 산출 |
| 5 | `GET /api/v1/buying-power` | 매수 가능 금액 사전 검증 |
| 6 | `GET /api/v1/price-limits` | 주문가가 가격 제한 범위 내인지 검증 |
| 7 | `POST /api/v1/orders` | 지정가 매수 주문 제출 |
| 8 | `GET /api/v1/orders/{orderId}` | 폴링으로 체결 상태 추적 |
| 9 | `POST /api/v1/orders/{orderId}/modify` 또는 `/cancel` | N분 미체결 시 정정 또는 취소 |

### 시나리오 2 — 미국주식 야간 분할매매 봇 (TWAP형)

토스증권이 공식적으로 내세운 핵심 사례. 시차로 모니터링이 어려운 미국 정규장 시간대(한국 새벽)에 대량 주문을 시간 분할로 자동 집행한다. 무인 운영이 전제이므로 토큰 24시간 만료에 대비한 자동 재발급 로직이 필수다.

| 순서 | API | 역할 |
|---|---|---|
| 1 | `GET /api/v1/market-calendar/US` | 당일 미국 휴장 여부 확인 (휴장 시 봇 중단) |
| 2 | `POST /oauth2/token` | 장 시작 전 토큰 신규 발급 (24h 커버) |
| 3 | `GET /api/v1/exchange-rate` | 환율 확인 → KRW 예산을 USD 수량으로 환산 |
| 4 | `GET /api/v1/buying-power` | 총 집행 가능 금액 확정 |
| 5 | `GET /api/v1/candles` (1분봉) | 직전 변동성 측정 → 슬라이스 크기 조정 |
| 6 | `GET /api/v1/prices` + `/orderbook` | 슬라이스마다 반복: 현재가·호가 기반 지정가 산출 |
| 7 | `POST /api/v1/orders` | 슬라이스 주문 제출 (예: 30분 간격 N분할) |
| 8 | `GET /api/v1/orders` | 미체결 잔량 확인 |
| 9 | `POST /api/v1/orders/{orderId}/cancel` | 타임아웃 슬라이스 취소 후 다음 슬라이스에 잔량 이월 |
| 10 | `GET /api/v1/holdings` | 장 마감 후 최종 포지션 검증 (reconciliation) |

### 시나리오 3 — LLM/AI 에이전트 연동 포트폴리오 분석 (Read-Only)

"내 포트폴리오 수익률 분석해줘" 한 문장으로 동작하는 공식 마케팅 시나리오. Claude·ChatGPT 등 LLM에 API 키를 연동하고, MCP 서버나 함수 호출로 조회 API를 노출한다. 주문 API를 도구에서 제외하면 읽기 전용 안전 모드가 되며, 개인 사용자에게는 이 구성을 기본값으로 권장한다. 개발자 문서가 `/llms.txt`를 제공한다는 점 자체가 이 시나리오를 1급 사용 사례로 설계했다는 신호다.

| 순서 | API | 역할 |
|---|---|---|
| 1 | `POST /oauth2/token` | 에이전트 기동 시 토큰 확보 |
| 2 | `GET /api/v1/accounts` | 계좌 컨텍스트 로드 |
| 3 | `GET /api/v1/holdings` | 보유 종목·수량·평단 로드 |
| 4 | `GET /api/v1/prices` | 보유 종목별 현재가 → 평가손익 계산 |
| 5 | `GET /api/v1/exchange-rate` | 해외주식 KRW 환산 수익률 계산 |
| 6 | `GET /api/v1/candles` (일봉) | 기간 수익률·MDD·변동성 등 시계열 분석 |
| 7 | `GET /api/v1/orders` | 최근 주문 이력 기반 매매 패턴 분석 |

### 시나리오 4 — 시세 수집·백테스트 데이터 파이프라인

멀티 LLM 교차검증형 퀀트 리서치의 입력 데이터를 만드는 수집 파이프라인. 단, 현행 스펙은 1분봉과 일봉만 제공하므로 3·5·15분봉 등 중간 주기는 1분봉을 직접 리샘플링해서 생성해야 한다.

| 순서 | API | 역할 |
|---|---|---|
| 1 | `GET /api/v1/stocks` | 유니버스 종목 메타데이터 수집 |
| 2 | `GET /api/v1/market-calendar/{KR,US}` | 거래일 캘린더 → 수집 스케줄 생성 |
| 3 | `GET /api/v1/candles` | 일봉(장기) + 1분봉(단기) 적재 |
| 4 | `GET /api/v1/trades` | 틱 데이터 적재 (체결강도·미시구조 분석용) |
| 5 | `GET /api/v1/commissions` | 수수료 실측값 → 백테스트 비용 모델 반영 |

### 시나리오 5 — 리스크 모니터링·손절 자동화 봇

보유 포지션을 주기적으로 감시하다가 손절·익절 조건 충족 시 자동 매도하는 방어형 봇. 계좌 조회 API에 초당 1회 수준의 rate limit이 존재하므로 폴링 주기를 1초 이상으로 설계해야 한다.

| 순서 | API | 역할 |
|---|---|---|
| 1 | `GET /api/v1/holdings` | 감시 대상 포지션 로드 (주기 폴링) |
| 2 | `GET /api/v1/prices` | 종목별 현재가 → 손익률 계산 |
| 3 | `GET /api/v1/sellable-quantity` | 트리거 발동 시 매도 가능 수량 확인 |
| 4 | `GET /api/v1/orderbook` | 매도 호가 확인 → 시장가/지정가 결정 |
| 5 | `POST /api/v1/orders` | 손절/익절 매도 주문 제출 |
| 6 | `GET /api/v1/orders/{orderId}` | 체결 확인 후 알림 발송 |

### 시나리오 6 — 무인 운영(서버/cron)을 위한 토큰 수명 관리

모든 무인 시나리오의 공통 기반. refresh token이 없으므로 만료 마진을 두고 client_secret으로 선제 재발급하는 패턴이 표준이다.

- 토큰 발급 시각 + 86,400초를 기록하고, 만료 60분 전 시점에 `POST /oauth2/token`으로 재발급한다.
- client당 유효 토큰이 1개이므로, 다중 프로세스 환경에서는 토큰을 중앙 캐시(파일·Redis 등)에 저장해 공유한다.
- 401 응답 수신 시 1회 즉시 재발급 후 재시도하는 폴백을 넣되, 재발급 루프 방지를 위해 백오프를 건다.

---

## 5. 설계 시 유의해야 할 제약사항

| 제약 | 내용 및 대응 |
|---|---|
| Rate Limit | 존재함 (계좌 API 초당 1회 수준으로 분석됨). 폴링 주기 1초 이상, 종목별 시세 조회는 배치·캐시 전략 필요. 정확한 한도는 문서·실측으로 확인 필요 |
| 캔들 주기 제한 | 1분봉·일봉만 제공. 3/5/15/30/60분봉은 1분봉 리샘플링으로 자체 생성 |
| WebSocket 미지원 | 마케팅 페이지에는 언급되나 현행 스펙(v1.0.3)에는 없음. 실시간성은 REST 폴링으로 구현하되 rate limit과 충돌하지 않게 설계 |
| 토큰 24h / refresh 없음 | 무인 환경에서는 자동 재발급 로직 필수 (시나리오 6 참조) |
| 표면 범위 | 거래내역 원장(ledger), 관심종목, 푸시 알림 API는 스펙에 없음. 시세·계좌·주문 중심의 좁은 표면 |
| 상품 범위 | 국내·미국 주식만. 선물옵션·채권 미지원 |
| 주문 정정 동작 | 비공식 분석 기준, 정정 시 신규 orderId가 발급되는 구조일 가능성이 있어 주문 추적 시 ID 계보(lineage) 관리 권장 |
| 서비스 상태 | 사전 신청 단계로 정식 오픈일 미정. 키 발급 콘솔 절차, 거래 권한 scope 모델은 아직 외부 검증 사례가 부족 |

---

## 6. 정보 검증 상태 구분

공식 문서 사이트(developers.tossinvest.com)는 JavaScript 렌더링 방식이라 본 분석 시점에 직접 파싱이 불가했다. 따라서 아래와 같이 출처 등급을 구분한다.

| 등급 | 해당 내용 |
|---|---|
| 공식 확인 | 사전 신청 진행 중, AI/LLM 연동 및 야간 자동매매 사용 사례, 수수료 정책, Base URL과 주문 예제 코드 구조, X-Tossinvest-Account 헤더 (토스증권 공식 페이지 및 언론 보도) |
| 스펙 기반 (2차 검증) | 20개 엔드포인트 목록, OAuth2 Client Credentials, 토큰 86,400초·refresh 없음, 캔들 1분봉·일봉 한정 — 공개된 OpenAPI 스펙(v1.0.3)을 분석한 오픈소스 프로젝트 문서 기준이며, 스펙 원문 직접 대조를 권장 |
| 미검증 | client_id/secret 발급 콘솔 절차, 거래 권한 scope 모델, rate limit 정확한 수치, WebSocket 제공 시점, 정식 오픈일 |

**실제 개발 착수 시에는 OpenAPI 스펙 원문(openapi.json)을 코드 생성의 single source of truth로 삼고, 본 문서는 아키텍처 설계 참고용으로 활용할 것을 권장한다.**

---

## 7. 참고 자료

- 토스증권 개발자센터: https://developers.tossinvest.com/docs
- OpenAPI 스펙: https://openapi.tossinvest.com/openapi-docs/latest/openapi.json
- 토스증권 Open API 소개 페이지: https://corp.tossinvest.com/ko/open-api
- 오픈 API 서비스 이용 약관: https://home.tossinvest.com/ko/terms/v2?id=752
- 연합인포맥스 보도 (2026-05-21): '새벽 자동매매·AI 계좌분석까지' 토스증권 오픈 API
- 커뮤니티 스펙 분석 (비공식): github.com/JungHoonGhae/tossinvest-cli — docs/migration/open-api.md
