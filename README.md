# vibe investing

> 인공지능을 도구로 활용한 바이브 투자(Vibe Investing) 큐레이션 · 전략 · 칼럼 · 논문 레포

AI를 엑셀과 같은 도구로 보고, 시장의 소음에서 신호를 가려내는 작업을 공개합니다. 
인공지능, LLM은 만능이 아니며, 모델을 읽는 인간의 통찰력이 가장 중요하다고 믿습니다. 
미국 나스닥·S&P500, 가상화폐, 명품 섹터, 크립토-주식 상관관계를 리서치하며 파과적 혁신 산업에서 알파 수익을 추구하고 있습니다.

이 레포는 Dennis 저의 산만한 성격처럼 일본의 만물상 돈키호테와 같이 산만한 가운데서 보석이 있습니다. 
readme 실시간 업데이트는 가능성이 낮으며 랜덤 주기로 업데이트됩니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Made with](https://img.shields.io/badge/Made%20with-Claude%20%2B%20Python-blue)](https://github.com/gameworkerkim/vibe-investing/blob/main)
[![Updates](https://img.shields.io/badge/Updates-Weekly-brightgreen)](https://github.com/gameworkerkim/vibe-investing/blob/main)
[![Awesome Lists](https://img.shields.io/badge/Awesome--Lists%20%C3%97%205-orange)](https://github.com/gameworkerkim/vibe-investing/blob/main)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-0962-2175)

[English README](https://github.com/gameworkerkim/vibe-investing/blob/main/Readme%20en.MD)

---

## NEW · 핫해핫해 콘텐츠 — Toss × AMQS 퀀트 대시보드

> 토스증권 **Open API** 로 한국인이 실제로 사고·검색하는 국내 주식·ETF에 **Adaptive Momentum Quant Strategy (AMQS)** 룰을 *기계적으로* 적용해 **매수 / 보유 / 매도** 를 한 화면에서 판정하는 풀스택 대시보드입니다. 미국 백테스트로 검증한 모멘텀 전략을 처음으로 **한국 시장에 이식**하고, 그 결과를 정직하게 공개합니다.

→ **[Toss 대시보드 열기](https://github.com/gameworkerkim/vibe-investing/tree/main/Toss)** · [사용 설명서(GUIDE)](https://github.com/gameworkerkim/vibe-investing/blob/main/Toss/GUIDE.md) · [국내 3년 백테스트 리포트](https://github.com/gameworkerkim/vibe-investing/blob/main/Toss/backtest/BACKTEST.md)

- **무엇을 하나** — 섹터 대표주 8섹터×10종목 + 인기 ETF 10종목 + 종목 검색(이름·6자리 코드, 공유 링크 `?q=삼성전자` 지원)에 동일한 룰을 즉시 적용. 각 종목에 모멘텀 점수(0~100)·12-1/6-1 모멘텀·60일 변동성·**−12% 손절선**·시그널 근거를 표시.
- **3대 메커니즘** — ① 4개 시간축 z-score 합성 모멘텀(노이즈 제거) ② 거시 레짐 필터(국내는 KODEX 200 200일선 + 20일 실현변동성으로 VIX 대체) ③ 주간 회전으로 리더십 로테이션 추적.
- **정직한 결과** — 국내 3년 백테스트에서 *폭락 없는 강세장* 구간은 KODEX 200 단순보유에 수익·낙폭·Sharpe 모두 뒤졌습니다. AMQS의 가치는 **급락·전환장의 낙폭 통제**에 있으며, 모멘텀 종목선택 자체는 동일가중 대비 초과수익을 냈습니다. (원본 미국 백테스트: CAGR 38.75% · MDD −16.9% · Sharpe 1.33)
- **즉시 실행** — `cd Toss && npm install && npm start` → 키 없으면 MOCK 모드(합성가격·로직 시연용)로 바로 뜹니다. 토스 Open API는 2026년 6월 기준 사전 신청 단계.

> *"방어가 공격보다 먼저 — 시장이 좋을 때 산책하고, 비가 오면 진창에 덜 빠진다."*

---

## NEW · 하락을 판단하는 퀀트 — ARDS-X 레짐 분류기 (소스 + 대시보드)

> *"하락에는 네 가지 얼굴이 있다 — 건강한 조정, 단기 과매도, 구조적 하락, 그리고 침체. 똑같이 빨갛게 보이지만, 처방은 정반대다."*

미국 빅테크 + AI/인프라 복합체와 S&P500·Nasdaq100 의 하락이 지금 **조정인지, 단기 과매도인지, 구조적 하락인지, 침체로 인한 자산 리밸런싱인지**를 **실데이터로 자동 분류**하는 퀀트 확장(ARDS-X)과 그 시각화 대시보드의 **전체 소스 코드**를 공개합니다. ARDS 원본이 LLM 프롬프트로 *추정*하던 5-Factor 침체 컴포지트를, 여기서는 **FRED 무료 CSV + yfinance 실데이터로 직접 계산**합니다 (API 키 불필요).

→ **[ARDS-X 소스·대시보드 열기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/ARDS%20%E2%80%94%20Adaptive%20Recession-Defensive%20Strategy%20for%20AI_QQQ)**

- **2-축 레짐 맵** — X축 거시 침체 Composite(5-Factor) × Y축 가격 스트레스(드로다운·추세붕괴) + 과매도 오버레이(RSI·%B·ATR)로 5개 상태(정상상승/조정/과매도/하락분배/침체리밸런싱)를 판정하고, 각 상태마다 **자매 전략(AMQS 모멘텀 / ARDS 방어)으로의 핸드오프**까지 제시. *단독 매매가 아니라 "지금 어떤 전략 책을 펼지"를 정하는 스위치.*
- **금리 스트레스 축(v1.1)** — "침체 Composite는 낮은데 왜 떨어지나(금리 쇼크)"를 **침체형/금리형/밸류형** 라벨로 분리. 백테스트에서 **금리형 하락의 향후 60일 수익률 −7.3%** 로, 침체 축이 놓치는 진짜 위험 구간을 정확히 분리해 TLT/IEF 헤지 작동 여부를 조건부로 안내.
- **히스테리시스(v1.1)** — 진입/이탈 밴드 + 2일 확인으로 레짐 핑퐁(휩쏘)을 **249 → 88회(−65%)** 로 감소.
- **백테스트 검증(2014–2026, ^NDX 2,914 거래일)** — 룩어헤드 없이 상태별 향후 수익률·레짐 스위치 vs Buy&Hold·신뢰도 캘리브레이션(Brier 0.281)을 공개. 강세장 방어 비용과 프록시 BEAR_TRAP 한계까지 정직하게 명기.
- **소스 구성** — `quant/`(config·datafeed·macro·rates·technical·classifier·run·backtest, 무료 데이터·캐시 폴백) + `dashboard/`(index.html·app.js·styles.css, 정적 시각화) + `prompts/`(LLM 교차검증용 한·영·중 프롬프트). 실행: `cd quant && python run.py` → `dashboard/data/latest.json`.

> *"가격만 봐서는 조정과 침체를 절대 구분할 수 없다. 그래서 ARDS-X 는 거시 축과 가격 축을 함께 본다."*

---

## 이 레포가 향하는 곳 — 멀티-LLM 투자위원회

Vibe Investing의 다음 단계는 단일 LLM 의존에서 벗어나, **서로 다른 개성을 가진 여러 LLM을 하나의 퀀트 헤지펀드 투자위원회처럼 운용하고 교차검증하는 것**입니다.

[ARDS — Adaptive Recession-Defensive Strategy](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/ARDS%3A%20Adaptive%20Recession-Defensive%20Strategy/readme.md) 연구에서, 동일한 프롬프트와 동일한 시장 데이터를 Claude · Gemini · ChatGPT · DeepSeek 4개 모델에 입력했을 때 다음이 관찰되었습니다.

- **거시 진단은 수렴** — 4개 모델 모두 경기 침체 경고 구간으로 합의 (Composite 표준편차 2.29%p, CV 3.7%)
- **실행은 분산** — "무엇을 얼마나 사야 하는가"의 비중 변동계수는 52%로, 진단 대비 약 14배 격차
- **각 모델이 고유한 PM 페르소나를 형성** — Claude(규율 기반 리스크 관리자), Gemini(현금 우선 매크로 리스크 오피서), ChatGPT(체계화·백테스트 중심 퀀트 전략가), DeepSeek(공격적 알파 헌터)

이 구조는 실제 멀티-매니저 헤지펀드의 투자위원회 의사결정과 유사합니다. 단일 초지능 모델이 아니라, **서로 다른 투자 철학을 가진 AI들의 committee**가 더 견고한 의사결정을 만든다는 가설을, 본 레포의 전략들로 단계적으로 실증·확장해 나갑니다. 기본 설계 철학과 5-Dimension 채점·4-Tier 유니버스·4-Phase 레짐 구조는 [ARDS readme](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/ARDS%3A%20Adaptive%20Recession-Defensive%20Strategy/readme.md)를 참조하세요.

---

## Vibe Investing이란?

Vibe Coding이 자연어로 LLM에 코드를 짜게 하는 패러다임이라면, Vibe Investing은 자연어 지시에서 출발해 LLM이 도구를 호출하고 시장 데이터·뉴스·온체인 신호를 수집·분석한 뒤 검증 가능한 투자 의사결정을 산출하는 agentic 파이프라인입니다. 핵심은 자연어 전략 정의, 능동적 도구 호출, 멀티 에이전트 합의(Bull/Bear/Risk/PM), 그리고 사람이 검증 가능한 reasoning trail입니다.
인공지능이 신호와 소음 사이에서 신호를 찾고 인간의 인사이트를 찾아줄 수 있는 투자 방식을 의미합니다.

---

## 내가 만든 Awesome 시리즈

이 레포의 중심은 직접 큐레이션·집필한 5종의 Awesome 시리즈입니다. 단순 링크 나열이 아니라, 각 항목을 강점·약점·적합 사용자로 평가하고 공통 함정을 명시한 점이 다릅니다. 각 시리즈는 독립된 서브 페이지에서 전체 내용을 볼 수 있습니다.

| 시리즈 | 장르 | 한 줄 정리 | 전체 보기 |
| --- | --- | --- | --- |
| Awesome Claude Quant Scripts | 퀀트 전략 + 프롬프트 | 8대 퀀트 전략을 학계 원전 → Python 골격 → Claude 프롬프트 3레이어로 묶은 핵심 자산 | [열기](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Awesome%20claude%20quant%20scripts.MD) |
| Awesome Vibe Invest — Stocks | 주식 도구 | NASDAQ/S&P500 AI 투자 도구 30+종 5축 평가 | [열기](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20vibe%20invest.MD) |
| Awesome Vibe Invest — Crypto | 크립토 도구 | 벤치마크(Alpha Arena) 중심 LLM 크립토 트레이딩 큐레이션 | [열기](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20vibe%20invest%20crypto.MD) |
| Awesome Vibe Trading Bot | 오픈소스 봇 | GitHub 오픈소스 코인 트레이딩 봇 분석 (AI 봇 확장판) | [열기](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20Vibe%20Trading%20Bot.MD) |
| Awesome AI Quant Prompt Repos | 프롬프트 레포 평가 | AI/LLM 기반 퀀트 프롬프트 GitHub 레포의 사용자 평가·신뢰성 분석 | [열기](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20AI%20Quant%20Prompt%20github%20repos%20evaluation%20kr.MD) |

### 다른 Awesome 시리즈와의 차이

기존 "awesome-quant" 류 리스트가 대체로 라이브러리·레포의 평면적 나열에 머무는 반면, 본 시리즈는 다음 차별화를 가진다.
(1) 항목별 강점·약점·적합 사용자 평가, 
(2) 활성도·성숙도·학습곡선·한국 시장·라이선스 5축 채점, 
(3) 공통 함정 섹션, 
(4) 한국·아시아 시장 자원 별도 정리를 포함합니다. 

특히 Awesome Claude Quant Scripts는 "어떤 도구를 쓰는가"가 아니라 "어떤 전략을 어떤 이론적 기반 위에서 돌리는가"를 다루는, 이 레포에서 가장 차별적인 결과물입니다.

---

## 장르별 큐레이션

### 전략 (Trading Strategy)

`01.Trading Strategy/` 폴더에 모여 있습니다. 멀티-LLM 교차검증 전략(ARDS, AMQS, AMQS-M7), **하락 판단 레짐 분류기(ARDS-X)**, Claude 스크립트 모음(Awesome Claude Quant Scripts), 단일 섹터 전략(명품), 상관관계 전략(BTC-Nasdaq 커플링)으로 구성됩니다. AMQS 모멘텀 엔진은 별도 [Toss 대시보드](https://github.com/gameworkerkim/vibe-investing/tree/main/Toss)로 국내 주식에 이식되었습니다.

→ 인덱스: [01.Trading Strategy README](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Readme.MD) ([EN](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Readme%20EN.md))

### 칼럼 (Investment Idea Column)

시장의 거시 흐름과 산업 변화를 실증 데이터로 분석한 7편. 위험 관리/시장 구조, 산업/섹터, 정량/데이터 기반으로 분류됩니다. 특정 주체를 지목하지 않는 통계적 논평 원칙을 따릅니다.

→ 인덱스: [02.Investment Idea Column README](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/Readme.MD)

### 논문 (SSRN Papers)

SSRN에 게재한 작업 논문 4편, 총 113페이지. 암호화폐 시장 미시구조 3편과 다국어 LLM 평가 1편으로, event study·variance decomposition·DCC-GARCH·Spearman 순위 상관 등 표준 계량 기법을 사용했습니다.

→ 인덱스: [Paper 논문 README](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/readme.md) · ORCID [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)

### 직접 개발 도구 (Tools)

| 도구 | 한 줄 정리 |
| --- | --- |
| [Toss × AMQS 대시보드](https://github.com/gameworkerkim/vibe-investing/tree/main/Toss) | 토스 Open API 국내 주식·ETF에 AMQS 룰 적용 → 매수/보유/매도 판정 풀스택 대시보드 (Node + MOCK 모드 + 국내 3년 백테스트) **NEW** |
| [ARDS-X 레짐 분류기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/ARDS%20%E2%80%94%20Adaptive%20Recession-Defensive%20Strategy%20for%20AI_QQQ) | 조정·과매도·하락·침체를 실데이터(FRED+yfinance)로 자동 분류 + 2-축 레짐 맵 대시보드 (2,914일 백테스트, API 키 불필요) **NEW** |
| [Harness Quant v2](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quant%20v2%20readme%20.MD) | 6개 시나리오 매트릭스 기반 LLM 트레이딩 플랫폼 (백테스트 + MCP + 멀티 에이전트 토론) (개발중)|
| [Earnings Momentum Agent](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quantv2/Earnings%20momentum%20agent%20readme%20.MD) | 저점 반등 + 어닝 서프라이즈 종합 Top 30 추천 파이프라인 (24개월 백테스트 30일 hit rate 83.3%) |
| [Nasdaq-BTC Coupling Bot](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) | BTC-QQQ 30일 rolling correlation 추적 + 6 regime 분류 + 신호 생성 (547줄 Python) |

### 기술 문서 (TechDoc)

레포 운영·재현에 필요한 기술 문서를 모았습니다.

→ [TechDoc 폴더](https://github.com/gameworkerkim/vibe-investing/tree/main/TechDoc)

---

## 최근 업데이트 (서브 폴더별 대표 항목)

### Toss · 신규 ⭐

- **Toss × AMQS 퀀트 대시보드** — 토스증권 Open API로 국내 주식·ETF에 AMQS 룰을 기계적으로 적용해 매수/보유/매도를 판정하는 풀스택 대시보드. AMQS 모멘텀 전략의 첫 한국 시장 이식 + 국내 3년 백테스트(KODEX 200·동일가중 대조) 정직 공개. MOCK 모드로 키 없이 즉시 실행.

### 01.Trading Strategy

- **ARDS-X — 하락 판단 레짐 분류기 (신규 ⭐)** — 조정·단기과매도·구조적하락·침체리밸런싱을 FRED+yfinance 실데이터로 자동 분류하는 2-축 레짐 맵. 금리 스트레스 축·히스테리시스(v1.1) + 2014–2026 백테스트(상태별 향후수익·캘리브레이션 Brier 0.281). 대시보드·퀀트 전체 소스 공개, API 키 불필요.
- **ARDS — Adaptive Recession-Defensive Strategy** — 4-LLM 교차검증으로 멀티에이전트 투자위원회 가설을 실증. 5-Factor 침체 컴포지트 + 4-Tier 25종목 유니버스 + 4-Phase 레짐.
- **Awesome Claude Quant Scripts** — 8대 퀀트 전략 큐레이션과 함께 AI 공급망 베이지안 분석, DAT 정량 전략, LLM 하락주 스크립트, 장기 배당 투자 등 4종 스크립트 + Sample 템플릿 수록.

### 02.Investment Idea Column

- **시장은 닫혔을 때 열리는가** — 나스닥100 기업 34건의 장 마감 후(AMC) 공시를 실증 분석. 91.2%가 AMC에 집중, AMC+Severe 조합 다음날 평균 -10.79%.
- **가상화폐와 나스닥은 얼마나 동기화되고 있을까** — 2020-2026 BTC-QQQ 상관관계 26분기 + 6 regime 분류 + 인트라데이 lag 측정.

### Paper 논문

- **Less Volume, More Variety** (SSRN 6705598) — 동일 프롬프트에서 LLM 출력 길이가 짧을수록 컨트라리안 종목 발굴률이 높아지는 역상관(Spearman ρ = -0.80) 보고.
- **Directional Decoupling** (SSRN 6750298) — BNB-ETH 페어의 상관관계 유지·변동성 비율 압축 메커니즘을 베타 분해로 규명 (28페이지).

### Harness quantv2

- **Earnings Momentum Agent** — 7단계 파이프라인(유니버스 스캔 → 펀더멘털·기술 필터 → 감성 → 컨센서스 → 4-에이전트 토론 → Top 30) 24개월 백테스트 768 의사결정 공개.

---

## 디렉토리 구조

```
vibe-investing/
├── README.md                          ← 본 문서 (한국어)
├── Readme en.MD                       ← English README
│
├── Toss/                              ← ⭐ NEW · Toss×AMQS 대시보드 (국내 매수/보유/매도 판정)
│   ├── README.md / GUIDE.md           ← 전략 철학 / 사용 설명서
│   ├── src/ (amqs.js·toss.js·universe.js) · server.js · public/
│   ├── backtest/BACKTEST.md           ← 국내 3년 백테스트 리포트
│   └── docs/                          ← 토스 Open API 기술 분석 + 스크린샷
│
├── 01.Trading Strategy/               ← 전략 인덱스
│   ├── Readme.MD / Readme EN.md
│   ├── ARDS — Adaptive Recession-Defensive Strategy for AI_QQQ/  ← ⭐ NEW · ARDS-X 하락 판단 레짐 분류기 (실데이터 퀀트 + 대시보드)
│   ├── ARDS: Adaptive Recession-Defensive Strategy/   ← 4-LLM 교차검증 방어 전략
│   ├── ARDS-Defense/                  ← 방어 심화 모듈
│   ├── Adaptive Momentum Quant Strategy (AMQS)/       ← 모멘텀 원본 (Toss 대시보드의 전략 엔진)
│   ├── Adaptive Momentum Quant Strategy (AMQS) for M7/← M7 모멘텀
│   ├── Awesome claude quant scripts/  ← 8대 전략 + 4종 스크립트 + Sample
│   ├── Luxury investment strategy/    ← 명품 섹터 전략 + 칼럼 + CSV 4종
│   └── Investment Strategy ... Coupling/ ← BTC-Nasdaq 봇 + 칼럼 + CSV 4종
│
├── 02.Investment Idea Column/         ← 칼럼 통합 인덱스 (7편)
│
├── Paper 논문/                        ← SSRN 작업 논문 4편 (113p) + 인용 스크립트
│
├── Harness quantv2/                   ← Earnings Momentum Agent
├── AfterMarketClose/                  ← AMC 공시 칼럼 + CSV
├── mNAV(Market-to-Net-Asset-Value) arbitrage/ ← DAT mNAV 칼럼 + CSV 3종
├── TechDoc/                           ← 기술 문서
├── TradingLog/                        ← 트레이딩 로그
│
├── Awesome vibe invest.MD             ← 주식 도구 큐레이션
├── Awesome vibe invest crypto.MD      ← 크립토 도구 큐레이션
├── Awesome Vibe Trading Bot.MD        ← 오픈소스 봇 분석
├── Awesome AI Quant Prompt ... kr.MD  ← 프롬프트 레포 평가
│
├── Harness quant v2 readme .MD        ← Harness Quant v2 문서
├── Vibe Investing Risk Management.MD  ← LTCM 칼럼
├── Microsoft fintool acquisition column.MD
└── Crypto perp manipulation column.MD
```

---

## 어디서 시작할까

- **국내 주식을 바로 판정해 보고 싶다면** → [Toss × AMQS 대시보드](https://github.com/gameworkerkim/vibe-investing/tree/main/Toss) (`npm start` → MOCK 모드로 즉시 실행)
- **지금 하락이 조정인지 침체인지 알고 싶다면** → [ARDS-X 레짐 분류기](https://github.com/gameworkerkim/vibe-investing/tree/main/01.Trading%20Strategy/ARDS%20%E2%80%94%20Adaptive%20Recession-Defensive%20Strategy%20for%20AI_QQQ) (`python run.py`, API 키 불필요)
- **퀀트 전략을 직접 짜보고 싶다면** → [Awesome Claude Quant Scripts](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/Awesome%20claude%20quant%20scripts.MD)의 프롬프트 템플릿 복사
- **멀티-LLM 위원회 개념을 보고 싶다면** → [ARDS readme](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/ARDS%3A%20Adaptive%20Recession-Defensive%20Strategy/readme.md)
- **도구 큐레이션이 필요하다면** → 관심 시장에 맞춰 [Stocks](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20vibe%20invest.MD) 또는 [Crypto](https://github.com/gameworkerkim/vibe-investing/blob/main/Awesome%20vibe%20invest%20crypto.MD)
- **시장 통찰을 얻고 싶다면** → [칼럼 인덱스](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/Readme.MD)에서 LTCM 칼럼부터
- **본인 자금으로 자동매매 전이라면** → 각 문서의 "알려진 한계 / 공통 함정 / 위험 고지" 섹션을 반드시 먼저 읽으세요

---

## 기여하기

별 누르기, 누락된 좋은 레포 제보, 평가에 대한 반박, 영문 번역, 한국 시장 자원 추천, 본인 백테스트 결과 공유, 칼럼 주제 제안, 퀀트 전략 추가 모두 환영합니다. 이슈 또는 PR로 알려주세요. "이 평가는 틀렸다"는 반대 의견이 가장 가치 있습니다.

---

## Disclaimer

이 레포의 모든 콘텐츠는 연구·교육 목적입니다.

- 어떤 도구도 수익을 보장하지 않습니다. 백테스트 hit rate는 이상적 시나리오 기반이며 slippage·수수료·세금·지연으로 실제 수익률은 낮아집니다.
- LLM이 생성한 코드에는 사실 오류·구조적 편향·보안 취약점이 포함될 수 있습니다. 직접 검증할 능력이 없다면 다른 LLM으로 교차검증해 환각을 필터링하세요. 4-LLM ensemble도 ground truth가 아니며 사람의 최종 검토가 필요합니다.
- 미국 SEC/CFTC, 한국 금감원, EU MiCA 모두 AI 기반 자동 트레이딩에 규제 적용 가능 — 본인 자산 운용은 가능하나 타인 자금 운용은 라이선스가 필요합니다.
- 시장 구조 분석 칼럼은 특정 주체를 지목하지 않는 통계적·학술적 논평이며, 개별 사건의 법적 성격 규명은 관할 기관의 몫입니다.
- 하락 베팅·공매도·곱버스 ETF·레버리지·방어형 인버스 상품은 개인에게 치명적일 수 있으며, 장기 보유 시 100% 손실에 수렴할 수 있습니다. 관련 위험 고지를 반드시 참조하고 포트폴리오 비중을 엄격히 제한하세요.
- 투자 결과와 법적 리스크에 대한 책임은 사용자에게 있습니다.

---

## About

김호광 (Dennis Kim / HoKwang Kim) — Betalabs Inc. CEO · Microsoft Azure ex-MVP · Former CEO, CyworldZ. Web3·블록체인·AI 트레이딩·멀티 에이전트 AI 시스템 영역에서 활동합니다.

- Email: gameworker@gmail.com
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)

이 레포는 긴 시간 금융, 보안, 게임 시장에서 일하면서 얻은 인사이트로 2017년 블록체인 스타트업 창업부터 싸이월드의 몰락까지 얻은 인사이트를 바탕으로 만들어졌습니다.

---

## 라이선스

MIT License — 자유롭게 사용·수정·배포 가능하며 출처 표기만 부탁드립니다. 칼럼·논문 인용 시 "김호광 (Dennis Kim) / vibe-investing 레포" 또는 해당 SSRN DOI를 명기해 주세요.

> "이론 없는 코드는 도박이고, 코드 없는 이론은 철학이다. Claude는 그 간극을 압축하지만, 결코 검증을 대체하지 않는다."

> "강세장에서 방어는 세금이지만, 약세장에서 방어는 산소다. 그러나 이 실험의 진짜 교훈은 — 당신을 위해 숨 쉬어 줄 단일 AI는 없다는 것이다. 서로 다른 폐를 가진 네 개의 AI가 함께 숨 쉴 때, 당신은 가장 잘 숨 쉴 수 있다."
