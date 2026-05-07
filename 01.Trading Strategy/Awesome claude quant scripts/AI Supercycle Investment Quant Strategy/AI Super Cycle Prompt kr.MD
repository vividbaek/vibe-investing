# AI Super Cycle Quant Strategy Using LLM (한국어판)

> **인공지능 슈퍼 사이클에 올라타는 미국 주식 퀀트 전략**
> S&P 500 + NASDAQ-100 종목에서 *AI Value Chain 4-Layer* 노출도를 동시에 충족하는 Top 10 종목 발굴 + Layer별 분산 분석 + 동일가중 포트폴리오 시뮬레이션

---

## 사용 방법

1. 아래 프롬프트 블록을 *전체 복사* (코드 블록 우상단의 복사 버튼 클릭)
2. Claude / GPT-5 / Gemini / DeepSeek 등 LLM 에 *그대로 붙여넣기*
3. LLM 이 Top 10 종목 + Layer별 분산 + 포트폴리오 분석을 자동 생성

> **언어 선택 가이드**: 본 한국어판은 *한국어 결과* 를 받기 원하는 사용자용입니다. *토큰 소모량을 줄이고 싶다면* [영문판 (AI Super Cycle Prompt EN.MD)](./AI%20Super%20Cycle%20Prompt%20EN.MD) 사용을 권장합니다 — *영문 프롬프트가 한국어 대비 약 30-40% 토큰 절감* 효과가 있습니다. 중화권 시장 분석을 함께 보려면 [중문판 (AI Super Cycle Prompt CN.MD)](./AI%20Super%20Cycle%20Prompt%20CN.MD) 도 참고하세요.

---

## 프롬프트 (한국어판)

```
[역할]
당신은 글로벌 톱티어 퀀트 헤지펀드에서 12년간 테크 섹터 알파를 발굴해온 포트폴리오 매니저이자 AI 인프라 리서치 책임자입니다. 당신의 의사결정 체계는 'AI Value Chain Stack' 모델에 기반하며, AI 매출 노출도, 자본 효율성, GARP(Growth at Reasonable Price) 밸류에이션, 그리고 모멘텀 팩터를 통합해 향후 12개월 총 수익률을 산출합니다.

현재 날짜는 2026년 5월 2일입니다. (편의상 오늘 날짜 기준으로 가정)

[분석 요청 대상]
S&P 500 및 NASDAQ-100 구성 종목 중, AI 슈퍼사이클(2024-2030)의 4개 레이어에 직간접 노출된 기업을 발굴하십시오.

- Layer 1 (Foundation / 반도체·EDA·장비): 칩 설계, 파운드리, EUV/Etch 장비, HBM 메모리
- Layer 2 (Infrastructure / 하이퍼스케일러·데이터센터): 클라우드 인프라, GPU 클러스터, 자체 ASIC, Foundation Model 배포
- Layer 3 (Enablers / 전력·냉각·네트워크): 데이터센터 전력 시스템, 액침 냉각, 광 네트워크 스위치
- Layer 4 (Application / AI 활용 SW·서비스): 엔터프라이즈 AI 플랫폼, AI 기반 SaaS, 산업 특화 AI

각 레이어에서 균형 있게 총 10개 종목을 선별하되, 다음 분포를 유지하십시오:
- Layer 1: 4개 (반도체 가치사슬의 깊이 반영)
- Layer 2: 3개 (Hyperscaler 빅 3 또는 4 중 선별)
- Layer 3: 2개 (전력·네트워크 인프라)
- Layer 4: 1개 (애플리케이션 레이어 대표)

[스크리닝 조건]
- AI 매출 노출도: AI 직접/간접 매출 비중 ≥ 15%, 또는 AI 관련 백로그(RPO) ≥ 매출의 30%
- 매출 성장: 직전 4분기 평균 YoY 매출 성장률 ≥ 12%
- 잉여현금흐름: TTM FCF Margin ≥ 15% (단, 신규 Capex 사이클 진입 기업은 ≥ 8% 허용)
- 시가총액: ≥ $20B
- 거래량: 30일 평균 거래대금 ≥ $500M (유동성 확보)

[점수 체계 - 종목별 총 100점]

1. AI 매출 노출도 (35% 가중치)
   - AI 직접 매출 비중 (가속기, AI SW, AI 클라우드 서비스)
   - 데이터센터/클라우드 부문 매출 성장률 (YoY)
   - AI 관련 백로그(RPO 또는 Bookings) 가시성
   - Hyperscaler 4사(Microsoft/Google/AWS/Meta) 매출 노출도

2. 자본 효율성 & 모멘텀 (30%)
   - ROIC vs WACC 스프레드 (가치창출 폭)
   - FCF/Capex 비율 (자본투자 대비 현금창출 효율)
   - EPS 성장률 (3Y CAGR + Forward 12M)
   - 매출 가속도(Revenue Acceleration: QoQ 변화율의 추세)

3. 밸류에이션 적정성 - GARP (20%)
   - PEG 비율 (P/E ÷ EPS Growth, 1.5 이하 우대)
   - EV/Sales vs 매출 성장률 (Rule of 40 분석)
   - 5년 평균 대비 EV/EBITDA 멀티플 위치
   - DCF 내재가치 대비 할인율 (시나리오별 IRR 산출)

4. 모멘텀 & 수급 (15%)
   - 6M / 12M 가격 모멘텀 (52주 신고가 대비 위치)
   - 13F 기반 기관 보유 비중 변화 (헤지펀드 신규 매수)
   - EPS 추정치 상향 조정 빈도(Beat & Raise 트랙)
   - 옵션 시장 Skew (하방 헤지 비용 vs 상방 베팅)

[데이터 처리 원칙]
2025년 4월까지의 알려진 재무 데이터와 가격 이력 + 2026년 1분기 가이던스를 기반으로 합리적 시뮬레이션을 수행하십시오. 추정치에는 ±5% 오차 범위를 명시하십시오. 미국 외 ADR(예: TSM, ASML)은 본국 결산일 차이로 인한 시차를 명시하십시오.

[출력 요구사항]

파트 1: 상위 10개 종목 리포트 (표 형식 포함)

- 티커, 회사명, 섹터, AI Layer (1/2/3/4), 현재가(추정), 시가총액
- AI 매출 노출도, 매출 성장률, FCF Margin, ROIC
- 4개 항목별 점수 및 총점
- 핵심 투자 근거 3가지 (AI 슈퍼사이클 내러티브 + 정량 지표)
- 리스크 요인 2가지 (수출 규제, ASIC 경쟁, Capex 사이클 정점 등)
- 12개월 목표 수익률 및 손절 기준

파트 2: 4개 Layer별 노출 분석

- Layer 1/2/3/4 각각의 비중 및 대표 종목
- Layer 간 상관관계 및 분산 효과
- AI 사이클 단계별(Early Capex / Mid Build-out / Late Monetization) 최적 비중 제안

파트 3: 10개 종목 동일가중 포트폴리오

- 예상 매출 가중평균 성장률
- 추정 베타, 변동성, Sharpe Ratio (3Y)
- NASDAQ-100 대비 초과 성과 가능성에 대한 정성적 평가
- 사이클 전환점 시그널 (예: GPU ASP 하락, Hyperscaler Capex 가이던스 하향, 클라우드 매출 성장률 둔화)

[경고 문구]
이 분석은 교육 및 정보 제공 목적이며, AI 슈퍼사이클은 역사상 가장 큰 자본 사이클 중 하나이지만 동시에 닷컴버블(2000) 같은 변동성 위험을 내재합니다. 실제 투자 결정은 개인의 판단과 전문가 상담을 거쳐 이루어져야 합니다. 과거 매출 성장이 미래 성장을 보장하지 않습니다.
```

---

## 프롬프트 구조 설명

### AI Value Chain 4-Layer 모델

본 프롬프트는 *AI 가치사슬을 4개 레이어로 분해* 하여 LLM 이 *수직 통합 분산* 을 평가하도록 강제합니다:

| Layer | 역할 | 대표 기업 후보 | AI Capex 수혜 시점 |
| --- | --- | --- | --- |
| **Layer 1: Foundation** | 칩·장비·메모리 | NVDA, AVGO, TSM, ASML, MU, AMD | **Early Capex (2024-2026)** |
| **Layer 2: Infrastructure** | 하이퍼스케일러·클라우드 | MSFT, GOOGL, AMZN, META, ORCL | **Mid Build-out (2025-2028)** |
| **Layer 3: Enablers** | 전력·냉각·네트워크 | VRT, ANET, ETN, GEV, NVT | **Mid Build-out (2025-2028)** |
| **Layer 4: Application** | 엔터프라이즈 AI SW | PLTR, NOW, CRM, CRWD, ADBE | **Late Monetization (2027-2030)** |

### 점수 가중치 설계 철학

| 차원 | 가중치 | 핵심 질문 |
| --- | --- | --- |
| **AI 매출 노출도** | **35%** | "이 회사가 *AI 사이클의 직접 수혜자* 인가?" |
| **자본 효율성 & 모멘텀** | **30%** | "AI Capex가 *실제 현금흐름* 으로 전환되고 있는가?" |
| **밸류에이션 (GARP)** | **20%** | "성장 *대비* 가격이 합리적인가?" |
| **모멘텀 & 수급** | **15%** | "기관·옵션 시장이 *동의* 하는가?" |

> **배당 성장 프롬프트 대비 차이**: 배당 가중치(40%)가 사라지고 *AI 매출 노출도(35%) + 자본 효율성(30%)* 가 핵심으로 이동. *밸류에이션 비중도 25%→20% 축소* — 성장 사이클 후반부에는 멀티플 컨트랙션보다 *매출 성장 가속이 더 큰 알파* 를 만들기 때문입니다.

---

## 추천 포트폴리오 및 전망

본 프롬프트의 LLM 결과로 *권장* 되는 10종목 (시뮬레이션 기준):

### Layer 1: Foundation (4종)

| # | 티커 | 회사명 | 점수 | AI 노출도 | 12개월 목표 |
| --- | --- | --- | --- | --- | --- |
| 1 | **NVDA** | NVIDIA | **95** | 90%+ | +20~28% |
| 2 | **AVGO** | Broadcom | **90** | 60% | +15~22% |
| 3 | **TSM** | TSMC (ADR) | **92** | 50% | +18~24% |
| 4 | **ASML** | ASML Holding (ADR) | **87** | 45% | +12~18% |

### Layer 2: Infrastructure (3종)

| # | 티커 | 회사명 | 점수 | AI 노출도 | 12개월 목표 |
| --- | --- | --- | --- | --- | --- |
| 5 | **MSFT** | Microsoft | **91** | 35% (Azure AI) | +14~18% |
| 6 | **GOOGL** | Alphabet | **88** | 30% (GCP+TPU) | +13~17% |
| 7 | **META** | Meta Platforms | **89** | 40% (광고 AI) | +15~20% |

### Layer 3: Enablers (2종)

| # | 티커 | 회사명 | 점수 | AI 노출도 | 12개월 목표 |
| --- | --- | --- | --- | --- | --- |
| 8 | **VRT** | Vertiv Holdings | **86** | 70% (DC 전력) | +18~25% |
| 9 | **ANET** | Arista Networks | **84** | 65% (DC 네트워크) | +14~20% |

### Layer 4: Application (1종)

| # | 티커 | 회사명 | 점수 | AI 노출도 | 12개월 목표 |
| --- | --- | --- | --- | --- | --- |
| 10 | **PLTR** | Palantir | **78** | 80% (AIP) | +10~30% (변동성↑) |

### 포트폴리오 선택 근거 (Quant 관점)

1. **수직 통합 헤지 구조**: AI Capex가 둔화되면 Layer 1(반도체)이 가장 먼저 충격을 받지만, Layer 4(애플리케이션)는 *2-3년 시차* 로 매출 인식 → **Layer 분산이 사이클 변동성을 흡수**합니다.

2. **AI Capex의 "Picks & Shovels"**: 2026년 4대 Hyperscaler의 Capex가 약 $400B 수준으로 추정됩니다. 그 중 *60% 이상이 GPU + 데이터센터 인프라* 로 투입되며, 본 포트폴리오의 Layer 1 + Layer 3 비중(60%)은 이 자금 흐름의 직접 수혜선입니다.

3. **모멘텀 + GARP 결합**: NVDA, AVGO 같은 모멘텀 리더와 GOOGL(상대적 GARP), META(광고 AI 매출 가속) 같은 *상대적 디스카운트 종목* 을 혼합 → **Pure Momentum의 사이클 리스크 완화**.

### 12개월 시장 전망 시나리오

| 시나리오 | 확률 | NASDAQ-100 수익률 | 본 포트폴리오 |
| --- | --- | --- | --- |
| 🟢 **AI Capex 가속** (Hyperscaler 가이던스 상향) | 30% | +25% | **+32%** |
| 🟡 **기본** (현행 Capex 유지 + 매출 가속) | 45% | +14% | **+18%** |
| 🟠 **Capex 둔화** (1H'27 가이던스 하향) | 20% | -3% | **-1%** |
| 🔴 **AI 거품 붕괴** (수요 가시성 균열) | 5% | -28% | **-22%** |

> **기대수익률 가중평균**: NASDAQ-100 +13.6% vs 본 포트폴리오 **+18.4%** → **초과 알파 약 +4.8%p**

### AI 사이클 전환점 시그널 (모니터링 체크리스트)

- ⚠️ **GPU ASP 하락**: NVDA의 Blackwell/Rubin 세대 ASP가 분기 -5% 이상 하락 시 사이클 정점 신호
- ⚠️ **Hyperscaler Capex 가이던스**: MSFT, GOOGL, META, AMZN 4사 합계 Capex YoY 성장률이 +10% 이하로 둔화
- ⚠️ **데이터센터 가동률**: Cushman & Wakefield 기준 북미 데이터센터 공실률 ≥ 5%로 반등
- ⚠️ **AI 애플리케이션 매출**: ChatGPT/Copilot/Gemini 등 ARR 성장률 둔화 (현재 +100% YoY 수준)

---

## 출력 결과 활용 가이드

### Part 1 (Top 10 종목)

* **점수 85점 이상**: *Core 포지션* 후보 — 비중 12-15% 가능 (NVDA, MSFT, TSM)
* **점수 75-85점**: *Satellite 포지션* — 비중 8-10%, 분기별 재평가
* **점수 75점 미만**: *Tactical 포지션* — 비중 5% 이하, 모멘텀 시그널 활용

### Part 2 (Layer별 노출)

* **Early Capex 단계 (2026년 현재)**: Layer 1 비중 ↑ (40-50%)
* **Mid Build-out 단계 (2027-2028)**: Layer 2+3 비중 ↑ (50-60%)
* **Late Monetization 단계 (2029+)**: Layer 4 비중 ↑ (30%+)

### Part 3 (동일가중 포트폴리오)

* 예상 매출 성장률 가중평균: *18-25%* 범위
* 추정 베타: *1.25-1.40* (시장 베타 1.0 대비 고변동성)
* 한국 거주자 *원천징수 15% + 양도소득세 22%* 별도 고려
* NASDAQ-100 대비 *outperform 가능성* 은 *Hyperscaler Capex 사이클* 이 지속되는 동안 우호적

---

## 토큰 효율성 비교

| 언어 | 입력 토큰 | 출력 토큰 | 총 비용 (Claude Opus 4.7 기준) |
| --- | --- | --- | --- |
| 한국어 | 약 1,650 tokens | 약 4,200 tokens | 약 $0.092 |
| 영어 | 약 1,100 tokens | 약 3,000 tokens | 약 $0.064 |
| 중국어 (간체) | 약 1,200 tokens | 약 3,300 tokens | 약 $0.071 |

> **권장**: *반복 사용 (월 1회 리밸런싱 등)* 시 영문판 사용으로 *연간 약 $5-10 절감* 가능. 결과 *해석* 만 한국어로 받으려면 프롬프트 끝에 *"답변은 한국어로 작성"* 추가.

---

## 한국 거주자 추가 고려 사항

### 세금

* **배당 원천징수**: 미국 15% + 한국 종합과세 (배당소득 2,000만원 초과 시 누진세율) — *AI 종목은 배당이 거의 없으므로 사실상 양도소득세가 핵심*
* **양도소득세**: 미국 주식 매매차익 22% (250만원 공제 후) — *NVDA, PLTR 같은 고변동성 종목은 분할매도로 250만원 공제 활용 권장*
* **외환차손익**: 매매시 환율 차이 별도 과세

### 절세 계좌 활용

* **ISA (개인종합자산관리계좌)**: 국내 ETF 한정. *KODEX 미국나스닥100, TIGER 미국필라델피아반도체나스닥, ACE 미국빅테크TOP7 Plus* 등으로 간접 노출
* **연금저축**: 국내 운용사 운용 ETF 한정. *KODEX 미국S&P500, KODEX 미국나스닥100* 활용
* **퇴직연금 (DC/IRP)**: 70% 위험자산 규제 내에서 미국 ETF 활용

### 환헤지 여부 의사결정

* **환노출형** (직접 보유 NVDA, MSFT 등): 달러 강세 시 추가 수익. *AI 사이클이 우호적인 국면에서는 달러 강세 동조 가능성 높음*
* **환헤지형** (예: KODEX 미국나스닥100선물(H)): 환율 변동 위험 차단. *원/달러 1,400원대 진입 시 환헤지 비중 확대 검토*

### 한국 상장 AI 관련 ETF 대안

| 한국 ETF | 추종 지수 | 특징 |
| --- | --- | --- |
| KODEX 미국나스닥100 | NASDAQ-100 | NVDA, MSFT, GOOGL 등 톱티어 노출 |
| TIGER 미국필라델피아반도체나스닥 | PHLX Semi (SOX) | NVDA, AVGO, TSM, ASML 집중 |
| ACE 미국빅테크TOP7 Plus | M7 (NVDA, MSFT, AAPL, GOOGL, AMZN, META, TSLA) | Magnificent 7 집중 |
| TIGER 글로벌AI인프라 | 자체 지수 | VRT, ANET, ETN 등 Layer 3 노출 |

> 위 ETF들은 *한국 ISA 계좌* 에서 활용 가능 (절세 효과). 단, *해외주식형 ETF는 분배금에서 15.4% 원천징수* 후 추가 종합과세 가능.

---

## 위험 고지

* 본 프롬프트의 결과는 *교육·연구 목적의 가상 시뮬레이션* 이며, 실제 투자 권유가 아닙니다
* LLM 의 데이터는 *2025년 4월까지의 알려진 정보* 기반이며, *실시간 가격/매출 데이터가 아닙니다*
* 추정치는 *±5% 오차 범위* 가 있으며, *실제 시장 데이터로 재검증* 필수
* **AI 슈퍼사이클은 닷컴버블(2000) 대비 펀더멘털이 강하지만, *Capex 정점 후 -50% drawdown* 가능** — 2000년 SOX 지수 -82% 폭락 사례 인지 필수
* **2026-2027년 GPU ASP 하락 + Hyperscaler Capex 둔화 시그널** 모니터링 필수
* 한국 거주자는 *외환거래법 + 양도소득세 + 종합과세* 별도 검토
* LLM 이 생성한 코드/추천을 실거래에 사용하기 전 반드시 *독립 데이터 소스* (예: SeekingAlpha, Morningstar, Bloomberg) 로 *교차 검증*
* **PLTR, SMCI 같은 변동성 극심 종목은 *옵션 IV 80%+* 인 점을 인식하고 포지션 사이즈 보수적으로** 관리 필요

---

## 작성 정보

**시리즈**: vibe-investing — Awesome Claude Quant Scripts
**연관 sub-strategy**:

* [Dividend Growth Prompt kr.MD](../Dividend%20growth%20prompt/Dividend%20Growth%20Prompt%20kr.MD) — 본 프롬프트의 *반대 팩터* (배당 성장 + 가치)
* [Long-Term Dividend Investing](../Long-Term%20Dividend%20Investing) — 장기 보유 전략 코드 구현
* [DAT Quant Strategy](../DAT%20quant%20strategy) — 디지털 자산 보유 기업 전략

**저자**: 김호광 (Dennis Kim / HoKwang Kim)

* Independent Researcher, Betalabs Inc. CEO, Cyworld Z 전 CEO
* ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
* GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
* Email: [gameworker@gmail.com](mailto:gameworker@gmail.com)

**작성일**: 2026년 5월 2일 v1.0
**라이선스**: MIT (자유 사용, 출처 표기 권장)

---

> *"In the AI super cycle, the picks and shovels matter more than the gold."*
> *"AI 슈퍼사이클에서는 곡괭이와 삽이 금보다 중요하다."*
