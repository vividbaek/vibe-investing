---
title: "SSRN Working Papers — HoKwang Kim (Dennis Kim)"
title_ko: "SSRN 작업 논문 모음 — 김호광 (Dennis Kim)"
author:
  name: "HoKwang Kim"
  name_ko: "김호광"
  alias: "Dennis Kim"
  affiliation: "Betalabs Inc."
  email: "gameworker@gmail.com"
  orcid: "0009-0002-0962-2175"
  ssrn_author_id: "11276088"
  github: "gameworkerkim"
papers_count: 4
total_pages: 113
languages: ["en", "ko"]
last_updated: "2026-05-12"
license: "CC-BY-4.0 (preprint text); MIT (associated code)"
description: "Index of four SSRN working papers spanning cryptocurrency market microstructure, exchange airdrop economics, and multilingual LLM evaluation in equity selection."
description_ko: "암호화폐 시장 미시구조, 거래소 에어드롭 경제학, 다국어 LLM 주식 선별 평가 등 4편의 SSRN 작업 논문 인덱스"
keywords:
  - "cryptocurrency"
  - "market microstructure"
  - "token unlock"
  - "airdrop"
  - "BNB Chain"
  - "Binance"
  - "beta decomposition"
  - "volatility ratio"
  - "large language model"
  - "LLM evaluation"
  - "contrarian investing"
  - "pharmaceutical sector"
  - "event study"
keywords_ko:
  - "암호화폐"
  - "시장 미시구조"
  - "토큰 언락"
  - "에어드롭"
  - "BNB 체인"
  - "바이낸스"
  - "베타 분해"
  - "변동성 비율"
  - "거대언어모델"
  - "LLM 평가"
  - "역발상 투자"
  - "제약 섹터"
  - "이벤트 스터디"
---

# SSRN Working Papers — HoKwang Kim

> **English follows after the Korean section.**
> **한국어 다음에 영어 섹션이 이어집니다.**

[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-0962-2175)
[![SSRN Author](https://img.shields.io/badge/SSRN-Author%20Page-1A5F7A)](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088)
[![Papers](https://img.shields.io/badge/Papers-4-success)](#paper-list)
[![Total Pages](https://img.shields.io/badge/Total%20Pages-113-informational)](#paper-list)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

---

## 한국어 (Korean)

### 저자 정보

| 항목 | 내용 |
|---|---|
| 성명 | 김호광 (HoKwang Kim) |
| 영문 별칭 | Dennis Kim |
| 소속 | Betalabs Inc. (CEO) |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN 작성자 ID | [11276088](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088) |
| 이메일 | gameworker@gmail.com |
| GitHub | [@gameworkerkim](https://github.com/gameworkerkim) |

### 논문 4편 요약

본 폴더는 2026년 4월~5월에 SSRN에 게재된 4편의 작업 논문(working papers)을 통합 관리한다. 주제는 크게 두 갈래로 나뉜다:

1. **암호화폐 시장 미시구조 (3편)** — Binance 거래소 토큰 언락 이벤트, BNB Chain Megadrop 에어드롭 분배 비대칭, BNB-ETH 베타의 변동성 비율 채널 분해.
2. **다국어 LLM 평가 (1편)** — 동일 프롬프트 하에서 출력 길이와 컨트라리안 종목 발굴률 간 역상관 관계.

총 113 페이지에 걸쳐 *event study*, *variance decomposition*, *DCC-GARCH*, *Spearman 순위 상관* 등 표준 계량경제·통계 기법을 사용했으며, 모든 데이터·코드는 공개 저장소에서 재현 가능하다.

### 논문 목록 (게재 순서)

| # | 제목 | SSRN ID | 게재일 | 페이지 | 파일 |
|---|---|---|---|---|---|
| 1 | 72-Hour Shock — Binance 토큰 언락 52건 예비 증거 | [6632838](https://ssrn.com/abstract=6632838) | 2026-04-24 | 21 | [`01_SSRN-6632838_72-Hour-Shock.md`](./01_SSRN-6632838_72-Hour-Shock.md) |
| 2 | 중앙화 거래소 에어드롭 분배 비대칭 — BNB Chain 생태계 | [6688740](https://ssrn.com/abstract=6688740) | 2026-05-11 | 55 | [`02_SSRN-6688740_Distribution-Asymmetry-BNB.md`](./02_SSRN-6688740_Distribution-Asymmetry-BNB.md) |
| 3 | Less Volume, More Variety — LLM 출력 길이와 컨트라리안 발굴 | [6705598](https://ssrn.com/abstract=6705598) | 2026-05-11 | 9 | [`03_SSRN-6705598_Less-Volume-More-Variety.md`](./03_SSRN-6705598_Less-Volume-More-Variety.md) |
| 4 | Directional Decoupling — BNB-ETH 베타 변동성 비율 채널 분해 | [6750298](https://ssrn.com/abstract=6750298) | 2026-05-12 | 28 | [`04_SSRN-6750298_Directional-Decoupling.md`](./04_SSRN-6750298_Directional-Decoupling.md) |

### 원연구 자료 (Underlying Research Materials)

본 4편의 SSRN 논문은 `vibe-investing` 레포의 [`01.Trading Strategy/`](../01.Trading%20Strategy/) (정량 전략·데이터셋·실행 봇)와 [`02.Investment Idea Column/`](../02.Investment%20Idea%20Column/) (시장 구조 칼럼)에서 축적된 1차 자료를 *학술적으로 형식화·재현 가능 형태로 정제*한 결과물이다. 각 논문의 직접적 원자료는 다음과 같다.

#### 📄 Paper 1 — 72-Hour Shock (Binance 토큰 언락 이벤트 스터디)

**방법론적 원형**: 본 논문의 *단기 이벤트 윈도우 + 음(−)의 초과수익률 측정* 프레임워크는 [`AfterMarketClose/`](../AfterMarketClose/) 칼럼의 *AMC 공시 91.2% 집중 + 익일 평균 −6.45% 수익률* 실증 분석을 암호화폐 도메인으로 확장한 것이다.

| 자료 | 위치 | 본 논문에 기여 |
|---|---|---|
| AMC 공시 타이밍 칼럼 | [`AfterMarketClose/`](../AfterMarketClose/) | 이벤트 스터디 방법론 원형, 단기 윈도우 설계 |
| AMC 공시 데이터 | [`AfterMarketClose/disclosure_timing_cases.csv`](../AfterMarketClose/) | 34건 이벤트 → 익일 수익률 측정 템플릿 |
| Crypto perp 시장 칼럼 | [`Crypto perp manipulation column.MD`](../Crypto%20perp%20manipulation%20column.MD) | 암호화폐 단기 시장 미시구조 사전 문헌 |
| Awesome vibe invest crypto | [`Awesome vibe invest crypto.MD`](../Awesome%20vibe%20invest%20crypto.MD) | 크립토 도구·데이터 소스 큐레이션 |

#### 📄 Paper 2 — Distribution Asymmetry of CEX Airdrops (BNB Chain)

**방법론적 원형**: *집단 간 분배 비대칭 분석* 프레임은 [`mNAV(...)/`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) 칼럼의 *DAT 보유자 vs 외부 투자자 mNAV 사이클 분석* 에서 출발해, *3개 코호트(BNB 보유자 / 재단 / 소매 참여자) 분해* 로 확장됐다.

| 자료 | 위치 | 본 논문에 기여 |
|---|---|---|
| DAT mNAV 사이클 칼럼 | [`mNAV(...)/`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) | 보유자 그룹별 비대칭 손익 분석 방법론 |
| DAT 정량 검증 CSV | [`mNAV(...)/mnav_cycles_arbitrage_signals.csv`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) | 12 사이클 + 15개 기업 *집단별 P&L 측정* 템플릿 |
| Crypto perp 시장 칼럼 | [`Crypto perp manipulation column.MD`](../Crypto%20perp%20manipulation%20column.MD) | CEX 거래소 구조·재단 인센티브 사전 분석 |
| Awesome vibe invest crypto | [`Awesome vibe invest crypto.MD`](../Awesome%20vibe%20invest%20crypto.MD) | BNB Chain 생태계 분석 소스 |

#### 📄 Paper 3 — Less Volume, More Variety (LLM 출력 길이 × 컨트라리안 발굴)

**방법론적 원형**: *동일 프롬프트 + 다중 LLM 비교* 프레임은 [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) 폴더의 4종 LLM 기반 정량 전략에서 출발했다. 본 논문은 그중 *Declining Stock* 스크립트를 *제약 섹터로 적용 + 4개 frontier LLM 횡단 비교* 로 확장한 결과다.

같은 LLM이라도 한국어, 영어, 중국어로 프롬프트가 만들어지면 언어별로 학습된 데이터셋이 다르기 때문에 결과적인 차이가 발생할 수 있으며 금융 데이터의 축적 정도에서 한국어 데이터가 부족하여 더 불명확한 데이터가 나올 수 있다는 것을 증명했다.

| 자료 | 위치 | 본 논문에 기여 |
|---|---|---|
| Claude quant 스크립트 모음 | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) | LLM 기반 정량 전략 기준 프레임 |
| Declining Stock 스크립트 | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) (Declining Stock Quant Script Using LLM) | 제약 섹터 LONG/SHORT 프롬프트 원형 |
| Long-Term Dividend 스크립트 | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) (Long-Term Dividend Investing) | LLM 종목 선별 평가 베이스라인 |
| AI Quant Prompt 큐레이션 | [`Awesome AI Quant Prompt[KR].MD`](../) | 프롬프트 엔지니어링 큐레이션 |

#### 📄 Paper 4 — Directional Decoupling (BNB-ETH 베타 압축)

**방법론적 원형**: 본 논문은 [`01.Trading Strategy/Investment Strategy Based on Bitcoin and Nasdaq Coupling/`](../01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) 의 *BTC-QQQ 30일 rolling correlation + 6 regime 분류* 프레임을 *암호화폐 내부 페어(BNB-ETH)* 로 적용하고, 추가로 *β = ρ·σ_X/σ_Y 분산 분해* 를 더해 학술적으로 형식화한 것이다. **이 논문은 vibe-investing 레포의 트레이딩 자산을 가장 직접적으로 학술화한 사례다.**

| 자료 | 위치 | 본 논문에 기여 |
|---|---|---|
| BTC-Nasdaq 커플링 전략 | [`01.Trading Strategy/Investment Strategy Based on Bitcoin and Nasdaq Coupling/`](../01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) | 핵심 방법론(rolling correlation + regime) 원형 |
| 분기별 상관계수 CSV | `btc_qqq_correlation_2020_2026.csv` (위 폴더 내) | 26 분기 측정 템플릿 → BNB-ETH 표본 설계에 반영 |
| 6 Regime 분류 CSV | `correlation_regimes_signals.csv` (위 폴더 내) | regime 임계값 설계 기준 |
| 인트라데이 lag 샘플 | `intraday_coupling_samples.csv` (위 폴더 내) | 인트라데이 동조성 측정 사전 자료 |
| 547줄 Python 봇 | `nasdaq_btc_coupling_bot.py` (위 폴더 내) | DCC-GARCH 사전 검증 코드 베이스 |

> 📌 **연구 흐름**: `01.Trading Strategy/` (실전 봇·CSV) → `02.Investment Idea Column/` (시장 구조 칼럼) → **본 폴더 (SSRN 학술 논문)** 의 3단계 파이프라인을 따른다. 데이터·코드는 모두 [`gameworkerkim/vibe-investing`](https://github.com/gameworkerkim/vibe-investing) 에서 재현 가능하다.

### 연구의 의의 (Significance)

#### 1. 시장 미시구조 측면

세 편의 암호화폐 논문은 *공개 온체인 데이터*와 *CEX 거래소 데이터*만으로 측정 가능한 새로운 시장 비효율성 패턴을 정량화했다. 특히 (1) 토큰 언락 직후 72시간 내 가격 하락 패턴, (2) 에어드롭 분배 구조에서의 토큰 보유자/재단/소매 투자자 간 비대칭 손익, (3) BNB-ETH 페어에서의 *상관관계 일정 + 변동성 비율 압축* 메커니즘은 기존 학술 문헌에서 충분히 다뤄지지 않은 영역이다. 한국 *DAXA(디지털자산거래소공동협의체)* 및 *KoFIU(금융정보분석원)* 규제 논의에 직접 적용 가능한 실증 근거를 제공한다.

#### 2. LLM 평가 측면

3번 논문은 frontier LLM 4종(ChatGPT, Claude, DeepSeek, Gemini)을 *동일 프롬프트* 조건에서 비교했을 때, **출력 길이가 짧을수록 컨트라리안 종목 발굴률이 비례적으로 높아지는** 역상관 관계(Spearman ρ = −0.80, ChatGPT 이상치 제외 시 ρ = −1.00)를 보고한다. 이는 *토큰 예산 자체가 LLM 앙상블에서 사고 다양성을 유도하는 하이퍼파라미터로 기능할 수 있다*는 함의를 가지며, *compression-forces-selection* 메커니즘으로 해석한다.

#### 3. 방법론적 측면

4편 모두 **공개 데이터 + 공개 코드 + 공개 PDF** 의 *triple-open* 원칙을 따른다. 인용 시 SSRN DOI 가 우선이며, ORCID 와 함께 표기하면 *CrossRef* 및 *Google Scholar* 색인에 정확히 매핑된다. *Reproducible research* 표준을 준수하기 위해 GitHub 저장소에 데이터·스크립트·LaTeX 소스가 함께 공개되어 있다.

---

## English

### Author Information

| Field | Value |
|---|---|
| Name | HoKwang Kim (김호광) |
| Alias | Dennis Kim |
| Affiliation | Betalabs Inc. (CEO) |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN Author ID | [11276088](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088) |
| Email | gameworker@gmail.com |
| GitHub | [@gameworkerkim](https://github.com/gameworkerkim) |

### Overview

This folder consolidates four SSRN working papers posted between April and May 2026. Two thematic clusters are covered:

1. **Cryptocurrency market microstructure (3 papers)** — covering token unlock events on Binance, Megadrop airdrop distribution on BNB Chain, and the volatility-ratio channel of BNB-ETH beta decomposition.
2. **Multilingual LLM evaluation (1 paper)** — documenting an inverse relationship between LLM output length and contrarian discovery rate under identical prompts.

The four papers total **113 pages** and employ standard econometric/statistical techniques including event studies, variance decomposition, DCC-GARCH, and Spearman rank correlation. All data and code are publicly available for reproducibility.

### Paper List (in posting order)

| # | Title | SSRN ID | Posted | Pages | File |
|---|---|---|---|---|---|
| 1 | The 72-Hour Shock? Preliminary Evidence from 52 Token Unlock Events on Binance | [6632838](https://ssrn.com/abstract=6632838) | 2026-04-24 | 21 | [`01_SSRN-6632838_72-Hour-Shock.md`](./01_SSRN-6632838_72-Hour-Shock.md) |
| 2 | Distribution Asymmetry of Centralized Exchange Airdrops and the BNB Chain Ecosystem | [6688740](https://ssrn.com/abstract=6688740) | 2026-05-11 | 55 | [`02_SSRN-6688740_Distribution-Asymmetry-BNB.md`](./02_SSRN-6688740_Distribution-Asymmetry-BNB.md) |
| 3 | Less Volume, More Variety: LLM Output Length × Contrarian Discovery in Pharma | [6705598](https://ssrn.com/abstract=6705598) | 2026-05-11 | 9 | [`03_SSRN-6705598_Less-Volume-More-Variety.md`](./03_SSRN-6705598_Less-Volume-More-Variety.md) |
| 4 | Directional Decoupling: Volatility-Ratio-Driven Beta Compression in BNB-ETH | [6750298](https://ssrn.com/abstract=6750298) | 2026-05-12 | 28 | [`04_SSRN-6750298_Directional-Decoupling.md`](./04_SSRN-6750298_Directional-Decoupling.md) |

### Underlying Research Materials

The four SSRN papers are the *academic formalization of primary materials* accumulated under [`01.Trading Strategy/`](../01.Trading%20Strategy/) (quant strategies, datasets, live bots) and [`02.Investment Idea Column/`](../02.Investment%20Idea%20Column/) (market-structure columns) of the `vibe-investing` repository. Direct precursors per paper:

#### 📄 Paper 1 — 72-Hour Shock (Binance Token Unlock Event Study)

**Methodological precursor**: the *short-window event-study + negative abnormal-return measurement* framework extends the [`AfterMarketClose/`](../AfterMarketClose/) column's empirical finding (*91.2% of shock disclosures occur AMC; mean next-day return −6.45%*) into the cryptocurrency domain.

| Source | Location | Contribution to the paper |
|---|---|---|
| AMC disclosure timing column | [`AfterMarketClose/`](../AfterMarketClose/) | Event-study methodology, short-window design |
| AMC disclosure dataset | [`AfterMarketClose/disclosure_timing_cases.csv`](../AfterMarketClose/) | 34 events → next-day return measurement template |
| Crypto perp manipulation column | [`Crypto perp manipulation column.MD`](../Crypto%20perp%20manipulation%20column.MD) | Prior crypto market-microstructure literature |
| Awesome vibe invest crypto | [`Awesome vibe invest crypto.MD`](../Awesome%20vibe%20invest%20crypto.MD) | Crypto data sources & tool curation |

#### 📄 Paper 2 — Distribution Asymmetry of CEX Airdrops (BNB Chain)

**Methodological precursor**: the *inter-cohort distribution-asymmetry* frame originates in [`mNAV(...)/`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) — *holder vs. non-holder mNAV cycle analysis on DAT companies* — and is extended to a *three-cohort decomposition (BNB holders / foundation / retail participants)*.

| Source | Location | Contribution to the paper |
|---|---|---|
| DAT mNAV cycle column | [`mNAV(...)/`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) | Group-level asymmetric P&L analysis methodology |
| DAT quant validation CSV | [`mNAV(...)/mnav_cycles_arbitrage_signals.csv`](../mNAV(Market-to-Net-Asset-Value)%20arbitrage/) | 12 cycles + 15 firms — *per-cohort P&L measurement* template |
| Crypto perp manipulation column | [`Crypto perp manipulation column.MD`](../Crypto%20perp%20manipulation%20column.MD) | Prior analysis of CEX structure & foundation incentives |
| Awesome vibe invest crypto | [`Awesome vibe invest crypto.MD`](../Awesome%20vibe%20invest%20crypto.MD) | BNB Chain ecosystem source map |

#### 📄 Paper 3 — Less Volume, More Variety (LLM Output Length × Contrarian Discovery)

**Methodological precursor**: the *identical-prompt × multi-LLM cross-comparison* frame originates in the four LLM-based quant strategies under [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/). This paper extends the *Declining Stock* script to the *pharmaceutical sector with four frontier-LLM cross-evaluation*.

| Source | Location | Contribution to the paper |
|---|---|---|
| Claude quant scripts collection | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) | Reference framework for LLM-based quant strategy |
| Declining Stock LLM script | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) (Declining Stock Quant Script Using LLM) | Prototype for the pharma LONG/SHORT prompt |
| Long-Term Dividend Investing | [`01.Trading Strategy/Awesome claude quant scripts/`](../01.Trading%20Strategy/Awesome%20claude%20quant%20scripts/) (Long-Term Dividend Investing) | LLM stock-selection evaluation baseline |
| AI Quant Prompt curation | [`Awesome AI Quant Prompt[KR].MD`](../) | Prompt-engineering curation |

#### 📄 Paper 4 — Directional Decoupling (BNB-ETH Beta Compression)

**Methodological precursor**: this paper applies the *BTC-QQQ 30-day rolling correlation + 6-regime classification* framework from [`01.Trading Strategy/Investment Strategy Based on Bitcoin and Nasdaq Coupling/`](../01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) to an *intra-crypto pair (BNB-ETH)*, and adds *β = ρ·σ_X/σ_Y variance decomposition* on top for formal academic treatment. **This is the most direct academic formalization of vibe-investing's trading assets.**

| Source | Location | Contribution to the paper |
|---|---|---|
| BTC-Nasdaq coupling strategy | [`01.Trading Strategy/Investment Strategy Based on Bitcoin and Nasdaq Coupling/`](../01.Trading%20Strategy/Investment%20Strategy%20Based%20on%20Bitcoin%20and%20Nasdaq%20Coupling/) | Core methodology (rolling correlation + regime) precursor |
| Quarterly correlation CSV | `btc_qqq_correlation_2020_2026.csv` (in folder above) | 26-quarter measurement template → BNB-ETH sample design |
| 6-Regime classification CSV | `correlation_regimes_signals.csv` (in folder above) | Regime threshold design reference |
| Intraday lag samples | `intraday_coupling_samples.csv` (in folder above) | Prior intraday-comovement measurement |
| 547-line Python bot | `nasdaq_btc_coupling_bot.py` (in folder above) | DCC-GARCH pre-validation code base |

> 📌 **Research pipeline**: `01.Trading Strategy/` (live bots & CSVs) → `02.Investment Idea Column/` (market-structure columns) → **this folder (SSRN academic papers)** — a three-stage pipeline. All data and code are reproducible at [`gameworkerkim/vibe-investing`](https://github.com/gameworkerkim/vibe-investing).

### Significance

#### 1. Market Microstructure Contribution

The three cryptocurrency papers quantify novel market inefficiency patterns measurable from public on-chain and exchange data alone. Specifically, (1) the 72-hour post-unlock price decline pattern, (2) the asymmetric P&L between BNB holders, foundations, and retail participants in airdrop distributions, and (3) the *correlation-preserving, volatility-ratio-compressing* mechanism in the BNB-ETH pair — three phenomena underexplored in prior literature. The results offer empirical evidence directly applicable to Korean regulatory deliberations under DAXA (Digital Asset Exchange Joint Council) and KoFIU (Korea Financial Intelligence Unit).

#### 2. LLM Evaluation Contribution

Paper #3 reports an inverse relationship: under identical prompts to four frontier LLMs (ChatGPT, Claude, DeepSeek, Gemini), shorter-output models produce proportionally more contrarian (uniquely-discovered) picks. Spearman ρ = −0.80 across all four models, and ρ = −1.00 after excluding ChatGPT as a stale-data outlier. This implies **token budget itself may operate as a hyperparameter inducing thought-diversity in LLM ensembles**, a mechanism we label *compression-forces-selection*.

#### 3. Methodological Contribution

All four papers adhere to a *triple-open* principle: open data, open code, open PDF. Citations should use the SSRN DOI as primary identifier and include the ORCID for accurate mapping in CrossRef and Google Scholar. Reproducibility artifacts (datasets, scripts, LaTeX sources) are mirrored to the author's GitHub repositories.

---

## How to Cite / 인용 방법

### Quick BibTeX

```bibtex
@misc{kim2026_72hr,
  author    = {Kim, HoKwang},
  title     = {The 72-Hour Shock? Preliminary Evidence from 52 Token Unlock Events on Binance},
  year      = {2026},
  month     = {apr},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6632838},
  url       = {https://ssrn.com/abstract=6632838},
  note      = {SSRN Working Paper No.~6632838}
}

@misc{kim2026_airdrop,
  author    = {Kim, HoKwang},
  title     = {Distribution Asymmetry of Centralized Exchange Airdrops and the {BNB} Chain Ecosystem:
               {BNB} Holder Gain, Foundation Disaster, and the Decoupling Pattern of {BNB} Chain},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6688740},
  url       = {https://ssrn.com/abstract=6688740},
  note      = {SSRN Working Paper No.~6688740}
}

@misc{kim2026_llm,
  author    = {Kim, HoKwang},
  title     = {Less Volume, More Variety: An Inverse Relationship Between {LLM} Output Length and
               Contrarian Discovery in Pharmaceutical Stock Selection},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6705598},
  url       = {https://ssrn.com/abstract=6705598},
  note      = {SSRN Working Paper No.~6705598}
}

@misc{kim2026_decoupling,
  author    = {Kim, HoKwang},
  title     = {Directional Decoupling: Volatility-Ratio-Driven Beta Compression in the
               {BNB}-{ETH} Pair, May 2022 -- April 2026},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6750298},
  url       = {https://ssrn.com/abstract=6750298},
  note      = {SSRN Working Paper No.~6750298}
}
```

> Full bibliography in [`BIBLIOGRAPHY.bib`](./BIBLIOGRAPHY.bib) (BibTeX) and [`BIBLIOGRAPHY.ris`](./BIBLIOGRAPHY.ris) (RIS for Zotero/Mendeley/EndNote).

---

## Folder Structure / 폴더 구조

```
vibe-investing/                                      # Parent repository
├── 01.Trading Strategy/                             # ← Underlying research materials
│   ├── Awesome claude quant scripts/                #   (sources for Paper 3)
│   ├── Luxury investment strategy/
│   └── Investment Strategy Based on Bitcoin and Nasdaq Coupling/  # (sources for Paper 4)
├── 02.Investment Idea Column/                       # ← Market-structure columns
├── AfterMarketClose/                                #   (sources for Paper 1)
├── mNAV(Market-to-Net-Asset-Value) arbitrage/       #   (sources for Paper 2)
├── Crypto perp manipulation column.MD               #   (sources for Papers 1 & 2)
│
└── Paper 논문/                                       # ← THIS FOLDER (SSRN papers)
    ├── README.md                                    # This file — bilingual index
    ├── CITATION.cff                                 # Citation File Format (GitHub-recognized)
    ├── BIBLIOGRAPHY.bib                             # All 4 papers in BibTeX
    ├── BIBLIOGRAPHY.ris                             # All 4 papers in RIS
    ├── metadata.json                                # Machine-readable index (schema.org JSON-LD)
    ├── 01_SSRN-6632838_72-Hour-Shock.md
    ├── 02_SSRN-6688740_Distribution-Asymmetry-BNB.md
    ├── 03_SSRN-6705598_Less-Volume-More-Variety.md
    ├── 04_SSRN-6750298_Directional-Decoupling.md
    └── scripts/
        ├── generate_citations.py                    # Regenerates BibTeX/RIS/APA/CSL-JSON
        ├── validate_metadata.py                     # ICMJE/COPE/CrossRef metadata check
        └── search_papers.py                         # Local full-text search (no dependencies)
```

---

## Scripts (International Publishing Compliance) / 국제 게시 요건 스크립트

Three Python 3.10+ utilities live under [`scripts/`](./scripts) and have **no external dependencies** (stdlib only):

| Script | Purpose | Usage |
|---|---|---|
| [`generate_citations.py`](./scripts/generate_citations.py) | Regenerates BibTeX, RIS, APA, MLA, Chicago, and CSL-JSON citations from each paper's YAML front-matter. | `python scripts/generate_citations.py --format bibtex --out BIBLIOGRAPHY.bib` |
| [`validate_metadata.py`](./scripts/validate_metadata.py) | Validates every paper file against ICMJE/COPE/CrossRef minimum-metadata checklist (DOI, ORCID, title, abstract, keywords, JEL, posted date). | `python scripts/validate_metadata.py` |
| [`search_papers.py`](./scripts/search_papers.py) | Indexed full-text search over the four papers; supports KO/EN queries with token-overlap ranking. | `python scripts/search_papers.py "volatility ratio"` |

All scripts read the YAML front-matter and Markdown body of each `0X_SSRN-XXXXXXX_*.md` file as ground truth. After editing a paper file, rerun `validate_metadata.py` to confirm compliance before re-uploading to SSRN.

---

## License / 라이선스

- **Preprint text & abstracts**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — share and adapt with attribution to HoKwang Kim and SSRN DOI.
- **Associated code & scripts**: MIT License — see individual repository `LICENSE` files.
- **Data**: see each paper's data availability statement.

---

## Contact

- **Author**: HoKwang Kim (Dennis Kim) — Betalabs Inc.
- **Email**: gameworker@gmail.com
- **ORCID**: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- **SSRN Author Page**: <https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088>
- **GitHub**: <https://github.com/gameworkerkim>

---

*Last updated: 2026-05-12 · Maintained by HoKwang Kim · See `CITATION.cff` for the canonical citation entry.*
