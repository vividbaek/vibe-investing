---
title: "Korean Cryptocurrency Regulation, Kimchi Premium, and Capital Flight — SSRN Working Papers by HoKwang Kim"
title_ko: "한국 가상자산 규제 실패와 김치 프리미엄 국부 유출 — 사토시 김프 측정 도구와 정책 개혁 제언 (SSRN Working Papers, 김호광)"
description: "Five SSRN working papers by HoKwang Kim (Betalabs CEO). Lead paper: the Bithumb-Binance BTC-numéraire premium (Satoshi Kimp) identifies the kimchi premium as Korea-specific regulatory friction, with KRW 14.2 trillion in detected capital flight over 9 years. Policy: allow foreigners to open accounts at Korean exchanges while maintaining KYC/AML/CFT."
description_ko: "베타랩스 김호광 대표의 SSRN 작업 논문 5편. 대표 논문은 사토시 김프(빗썸-바이낸스 BTC 본위 김프) — 김치 프리미엄이 한국 특화 규제 마찰의 비용임을 식별하고 9년 누계 14.2조원 자본 유출을 정량화. 정책 권고: KYC/AML/CFT는 강화 유지하면서 외국인의 한국 거래소 계좌 개설을 허용하는 점진적 개방."
author: HoKwang Kim
author_ko: 김호광
orcid: 0009-0002-0962-2175
papers: 5
keywords:
  - kimchi premium
  - Satoshi Kimp
  - BTC numéraire
  - Korean cryptocurrency regulation
  - capital flight Korea
  - Bithumb Binance arbitrage
  - foreign account Korean exchange
  - DAXA
  - KoFIU
  - FATF
  - Travel Rule
  - BNB Chain
  - token unlock
  - CEX airdrop
  - LLM evaluation
  - cryptocurrency market microstructure
keywords_ko:
  - 김치 프리미엄
  - 사토시 김프
  - BTC 본위 김프
  - 한국 가상자산 규제
  - 국부 유출
  - 빗썸 바이낸스 차익거래
  - 외국인 거래소 계좌 개설
  - 외국인 가상자산 거래 허용
  - 외환거래법
  - 트래블룰
  - 김호광
  - 베타랩스
  - DAXA
  - KoFIU
  - BNB 체인
  - 토큰 언락
  - CEX 에어드롭
  - LLM 평가
license: CC BY 4.0 (preprints) / MIT (code)
last_updated: 2026-05-17
---

# 한국 가상자산 규제 실패와 김치 프리미엄 국부 유출 — 사토시 김프 측정 도구와 정책 개혁 제언

## Korean Cryptocurrency Regulation, Kimchi Premium, and Capital Flight: SSRN Working Papers by HoKwang Kim

[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-0962-2175)
[![SSRN Author](https://img.shields.io/badge/SSRN-Author%20Page-1A5F7A)](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088)
[![Papers](https://img.shields.io/badge/Papers-5-success)](#논문-목록--paper-list--论文列表)
[![Lead Paper](https://img.shields.io/badge/Lead_Paper-Satoshi_Kimp-blue)](#사토시-김프-satoshi-kimp--bithumb-binance-btc-num%C3%A9raire-premium-ssrn-6756158)
[![Capital Flight](https://img.shields.io/badge/Detected_Capital_Flight-KRW_14.2T_in_9yr-red)](#사토시-김프-satoshi-kimp--bithumb-binance-btc-num%C3%A9raire-premium-ssrn-6756158)
[![License](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

**Languages**: [한국어](#korean--한국어) · [English](#english) · [中文](#chinese--中文)

---

## 핵심 메시지 (Executive Summary)

본 저장소는 한국 가상자산(암호화폐) 시장의 핵심 현상인 **김치 프리미엄**이 *"한국인의 코인 사랑"* 같은 시장 비효율이 아니라 **한국 특화 규제 마찰이 부과한 가격 비용**임을 학술적으로 식별한 작업이다. 새로운 측정 도구 **사토시 김프(Satoshi Kimp, BTC 본위 김프)** 를 통해 환율·자본통제·USDT 프리미엄 노이즈를 수학적으로 제거하고, **빗썸이 포함된 거래소 쌍에서만 가격 격차가 자릿수 수준으로 비대칭**임을 입증했다.

이 규제 마찰의 비용은 한국 관세청 적발 통계로 정량화된다 — **9년간(2018~2025) 누계 약 14.18조원의 자본 유출이 적발**되었고, 이는 무역대금 위장 송금·환치기·페이퍼컴퍼니 등 **불법 채널**을 통한 것이다. 이는 *탐지된 거래만*의 통계이므로 실제 유출은 더 클 것으로 추정된다.

### 정책 권고: 개방을 통한 블록체인 시장 우위 확보

본 연구가 제시하는 정책 방향은 명료하다.

1. **외국인의 한국 거래소 계좌 개설·거래 허용** (점진적 자율화) — 현재 외국인 거래 금지는 차익거래자 진입을 봉쇄하여 김치 프리미엄을 *구조적으로 지속*시키는 핵심 메커니즘이다. 정상 KYC 채널을 통해 외국인 접근을 허용하면, 지금까지 *불법 환치기·위장 송금* 같은 어두운 채널로 흐르던 자금이 *추적 가능한 정상 채널*로 들어오게 되어 오히려 자금세탁 방지(AML)에 유리하다.
2. **KYC/AML/CFT는 강도 유지 또는 강화** — 자금세탁 방지·테러자금 차단·고객확인 체계는 FATF Recommendation 16 등 글로벌 표준에 부합하도록 *현재 강도 유지 또는 강화*. 외국인 시장 개방과는 *독립적*인 사안이다.
3. **원화 기반 스테이블코인 인프라 정비** — 트래블룰이 차익거래의 *시간 차원*을 차단한다면, 원화 스테이블코인은 같은 KYC 표준 안에서 *경로 차원*을 제공해 정상적인 차익거래 채널을 구축한다.

이 세 가지가 함께 작동하면, 시뮬레이션 모델 안에서 빗썸-해외 김프 표준편차가 *해외 거래소 쌍 수준(0.2~0.3%)으로 수렴*하고, 한국이 자본 유출의 구조적 동인을 제공하는 폭이 의미 있게 축소된다. 이는 한국이 **블록체인·Web3 시장에서의 위치를 회복하고 우위를 확보**하기 위한 가장 비용 효율적인 출발점이다.

---

## 저자 정보 (Author Information)

| 항목 / Field | 내용 / Value |
| --- | --- |
| 성명 / Name | HoKwang Kim, Dennis Kim |
| 소속 / Affiliation | Betalabs Inc. (CEO) · 전 Cyworld Z CEO · 전 Microsoft Azure MVP (2015–2023, 약 9년) |
| 학술 경력 / Background | 블록체인·Web3 산업 실무 9년 (2017~) · 사이버 위협 인텔리전스(CTI) 보고서 다수 · 다국어 학술 출판 |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN Author ID | [11276088](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088) |
| Email | <gameworker@gmail.com> |
| GitHub | [@gameworkerkim](https://github.com/gameworkerkim) |
| Companion Repo | [vibe-investing](https://github.com/gameworkerkim/vibe-investing) — 데이터·코드·백테스트·트레이딩 봇 |

---

## 논문 목록 / Paper List / 论文列表

대표 논문(사토시 김프)을 첫 번째로 배치하고, 나머지 4편은 시장 미시구조·LLM 평가 연구로서 본 시리즈를 뒷받침한다.

| 순서 | 제목 (한국어) | Title (English) | SSRN ID | 자료 레포 |
| --- | --- | --- | --- | --- |
| **대표** | **사토시 김프 — 빗썸-바이낸스 BTC 본위 김프 (BNB 체인 토큰 이론·시뮬레이션)** | The Bithumb-Binance BTC-Numéraire Premium: Theoretical Framework with Calibrated Simulation Evidence on BNB Chain Tokens | [6756158](https://ssrn.com/abstract=6756158) | [Satoshi kimp Paper](https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper) · [한글 PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/ko/paper.pdf) · [English PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/en/paper_en.pdf) · [보도자료(한국어)](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/Press%20Release%20KR.md) |
| 후속 1 | BNB-ETH 방향성 디커플링 — 거래소 네이티브 토큰의 베타 분해 | Directional Decoupling: BNB-ETH Volatility-Ratio Beta-Decomposition Framework | [6750298](https://ssrn.com/abstract=6750298) | [BNB_ETH Relationship](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNB_ETH%20Relationship/readme.md) |
| 후속 2 | CEX 에어드롭 분배 비대칭 — BNB Chain Megadrop | Distribution Asymmetry of CEX Airdrops & the BNB Chain Ecosystem | [6688740](https://ssrn.com/abstract=6688740) | [BNBChain](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNBChain/readme.md) |
| 후속 3 | LLM 출력 길이 × 컨트라리안 발굴 — 제약 섹터 종목 선별 | Less Volume, More Variety: LLM Output Length and Contrarian Discovery in Pharmaceutical Stock Selection | [6705598](https://ssrn.com/abstract=6705598) | [Harness Quant v2](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quant%20v2%20readme%20.MD) |
| 후속 4 | 토큰 언락 72시간 충격 — 바이낸스 52건 이벤트 분석 | The 72-Hour Shock: 52 Token Unlock Events on Binance | [6632838](https://ssrn.com/abstract=6632838) | [Token unlock 72h shock analysis](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/readme.MD) |

---

# Korean / 한국어

## 사토시 김프 (Satoshi Kimp) — Bithumb-Binance BTC-Numéraire Premium (SSRN 6756158)

> **대표 논문 · Lead Paper** — Working Paper Version 5.1 · 2026-05-13 · 한국어 19페이지 · 영문 21페이지 · 중문 18페이지 (Trilingual Edition)

**문서 직접 링크**:
[한글 논문 PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/ko/paper.pdf) · [English Paper PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/en/paper_en.pdf) · [보도자료(한국어)](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/Press%20Release%20KR.md) · [폴더 전체](https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper)

### 한 줄 요약

**김치 프리미엄은 시장 비효율이 아니라 한국 특화 규제가 부과한 가격 비용이며, 그 비용은 9년 누계 14.2조원의 자본 유출로 한국 경제가 떠안고 있다. 외국인의 한국 거래소 계좌 개설을 허용하면 구조적으로 축소된다.**

### 1. 새로운 측정 도구 — 사토시 김프 (BTC 본위 김프)

기존 김치 프리미엄은 원화/달러 환율을 거쳐 측정되었기 때문에, 그 안에는 (i) **환율 변동**, (ii) **자본 통제(외환거래법)**, (iii) **USDT/USDC 스테이블코인 프리미엄**, (iv) **송금 지연(트래블룰)** 등 *별개의 요인들이 한꺼번에 뒤섞여* 있었다. 이 측정의 모호함이 학술 문헌에서 김치 프리미엄을 *"한국 retail의 비합리성"* 같은 행동주의적 가설로 자주 환원시켜온 원인이다.

본 논문은 BTC를 거래소 *내부*의 기준 단위(numéraire)로 사용하는 새로운 측정식을 제안한다:

```
π^BTC_X(t) = [P_Bithumb(X, KRW)/P_Bithumb(BTC, KRW)] / [P_Binance(X, USDT)/P_Binance(BTC, USDT)] − 1
```

**명제 1 (FX Noise Cancellation, FX 노이즈 상쇄)** 으로 분자·분모의 환율 단위가 수학적으로 정확히 상쇄됨이 증명된다. 그 결과 남는 것은 **"토큰 X가 빗썸 내부에서 BTC 대비 얼마나 비싸게 거래되는가"** 라는 *순수한 토큰 수준 비대칭* 신호뿐이다. 폴더명 *"Satoshi kimp"* 는 *사토시(BTC 최소 단위)로 측정한 김치 프리미엄*을 뜻한다.

### 2. 결정적 식별 결과 — 자릿수 차이의 비대칭

새 측정식으로 측정한 거래소 쌍별 BTC 본위 김프의 변동성 표준편차는 다음과 같다 (시뮬레이션 결과).

| 거래소 쌍 | 한국 포함 여부 | std (ETH 기준) | std (BNB 기준) |
| --- | --- | --- | --- |
| Binance ↔ OKX | 해외 ↔ 해외 | **0.23%** | **0.22%** |
| Binance ↔ Bybit | 해외 ↔ 해외 | **0.25%** | **0.24%** |
| OKX ↔ Bybit | 해외 ↔ 해외 | **0.34%** | **0.32%** |
| **빗썸 ↔ Binance** | **한국 ↔ 해외** | **0.85%** | **1.59%** |
| **빗썸 ↔ OKX** | **한국 ↔ 해외** | **0.89%** | **1.61%** |
| **빗썸 ↔ Bybit** | **한국 ↔ 해외** | **0.90%** | **1.63%** |

**핵심 관찰**: 자릿수 차이의 비대칭(3~7배)이 **오직 한국 거래소가 포함된 쌍에서만** 나타난다. 해외 거래소끼리는 차익거래자가 분 단위로 가격 격차를 해소하지만, 한국 거래소에서는 **외환거래법, 트래블룰, 실명확인 가상계좌 제도, 외국인 거래 금지** 등 *차익거래 채널 자체를 막는 규제* 때문에 가격 괴리가 며칠에서 수 주간 지속된다.

이는 김치 프리미엄이 **"한국인이 코인에 열광해서"** 가 아니라 **"한국 시장이 봉쇄되어 있어서"** 발생한다는 점을 *통계적으로 분간 가능한 형태*로 입증한 첫 결과다.

### 3. 정량적 정책 비용 — 9년 누계 14.18조원 국부 유출

규제 마찰의 비용은 한국 관세청 적발 통계로 정량화된다 (국민의힘 최은석 의원실, 2025-10-21 공개).

| 연도 | 적발 건수 | 적발 금액 |
| --- | --- | --- |
| 2024년 | 26건 | **1조 1,579억원** |
| 2025년 1~8월 | 16건 | **8,813억원** |
| **2018~2025 9년 누계** | **264건** | **약 14.18조원** |

적발 유형은 **무역대금 위장 송금**, **무등록 외국환업무("환치기")**, **페이퍼컴퍼니 활용** 등이다. 대법원 2025-09-04 판결(2024도16540)은 "규제 회피 목적의 위계적 송금"을 무등록 외국환업무로 명시했다.

이 14.18조원은 *적발된 거래만의 통계*이므로 실제 자본 유출은 이보다 훨씬 클 것으로 추정된다. 또한 모든 적발이 김프 차익거래에 기인한 것은 아니므로, 본 논문은 이를 **김프 정책 비용의 간접 지표**로 신중히 사용한다 — 그럼에도 *규제가 차익거래를 봉쇄한 결과 자본이 어두운 채널로 유출되고 있다*는 메커니즘 자체는 명확하다.

### 4. 자연 실험적 사건 — 2024년 12월 비상계엄 −32%

표본 기간 중 한 차례의 자연 실험이 발생했다. **2024년 12월 3일 비상계엄 선포 당시 김치 프리미엄이 −32% 수준의 극단적 음의 값**까지 떨어진 것이다. 이는 정치적 충격이 BTC 본위 김프 채널에 어떻게 전이되는지 시뮬레이션으로 재현할 수 있게 한 사례다.

### 5. 방법론적 엄밀성

- **데이터**: 2020-01-01 ~ 2025-12-31 일별 합성 시계열 (T = 2,192). Makarov & Schoar (2020, JFE), Choi et al. (2022), Eom (2021), Tiger Research (2024) 등 선행 문헌의 *stylized facts*에 부합하도록 calibration. 부록 A에 모멘트 매칭 검증 포함 (예: BTC 김프 AR(1) 계수 0.911이 Choi et al. 2022 보고치 0.85~0.95 범위에 일치).
- **추정**: OLS 회귀에 **Newey–West HAC 표준오차** 적용. 비대칭 변동성은 **Student-t 혁신항 EGARCH(1,1)** 로 추정. **표준화 분산 비율 ρ_X** 로 토큰 자체 변동성 통제.
- **재현 가능성**: 랜덤 시드 고정(20260513), 전체 Python 빌드 스크립트 공개.
- **분석 대상**: BNB(2021-05-27 빗썸 상장), Venus(XVS, BSC DeFi), ETH(베이스라인) — BNB 체인 토큰 3종 패널.

### 6. 학술적 의의 — 세 가지 기여

1. **새로운 측정 도구**: BTC를 numéraire로 사용해 김치 프리미엄을 재정의한 *최초의 학술 논문*. 환율·자본통제·스테이블코인 노이즈를 *측정 단계에서* 분리한 점이 핵심 방법론적 진보다.
2. **새로운 식별 전략**: 비한국 거래소 간 vs 한국 포함 거래소 쌍의 BTC 본위 김프 변동성을 직접 비교하는 식별 전략을 통해, 김치 프리미엄이 *"시장 비효율"인지* *"규제 비용"인지* 를 통계적으로 분간 가능하게 했다. 이는 학술 문헌에서 처음 시도된 자연 비교 설계이다.
3. **방법론적 엄밀성**: Newey–West HAC 표준오차, Student-t 혁신항 EGARCH(1,1), 표준화 분산 비율 ρ_X 등 금융계량경제학의 *표준 도구를 모두 적용*하고, 랜덤 시드 고정과 빌드 스크립트 공개로 *재현 가능성*까지 확보했다.

### 7. 정책 함의 — 개방을 통한 블록체인 시장 우위 확보

본 논문이 제시하는 정책 권고는 *학술 권고*이며 실제 정책 결정은 실거래소 API 데이터를 활용한 후속 실증 연구를 토대로 이루어져야 함을 명시한다. 그러나 시뮬레이션 증거가 가리키는 방향은 명료하다.

**권고 1 — 외국인의 한국 거래소 계좌 개설 및 거래 점진적 자율화** (핵심 권고)

현행 외국인 거래 금지 규제는:

- 차익거래자의 진입을 봉쇄하여 김치 프리미엄을 *지속시키는 핵심 메커니즘*
- 한국 retail 투자자에게 비효율적 가격으로 인한 *후생 손실*을 부담시키는 구조
- 차익 자금이 **불법 환치기·위장 송금 같은 어두운 채널을 통해 유출**되도록 강제하는 압력
- 한국이 글로벌 블록체인·Web3 시장에서 *경쟁력 있는 거래 허브* 가 될 가능성을 차단

→ **외국인의 한국 거래소 계좌 개설·거래를 점진적으로 자율화**해야 한다. 이는 한국 시장을 글로벌 차익거래 네트워크에 *재연결*시키며, 정상 KYC 채널을 통해 외국인 접근을 허용하면 같은 자금이 *추적 가능한 정상 채널*로 들어오게 되어 오히려 자금세탁 방지(AML)에 유리하다.

**권고 2 — KYC/AML/CFT는 강도 유지 또는 강화**

자금세탁(AML)·테러자금조달 차단(CFT)·고객확인(KYC) 체계는 FATF Recommendation 16 등 글로벌 표준에 부합하도록 *현재 강도를 유지하거나 강화*하는 방향이 적절하다. 이는 외국인 시장 개방과는 **독립적인 사안**이며, 두 권고는 서로 모순되지 않는다.

**권고 3 — 원화 기반 스테이블코인 인프라 정비**

트래블룰이 차익거래의 *시간 차원*을 차단한다면, 원화 스테이블코인은 같은 KYC 표준 안에서 *경로 차원*을 제공함으로써 정상적인 차익 채널을 만들 수 있다. 이는 한국이 *원화 결제망과 블록체인 결제망을 통합*하는 차세대 금융 인프라의 출발점이 된다.

### 8. 한국 블록체인 시장 우위 확보 전략

이 세 가지 권고가 함께 작동하면, 시뮬레이션 모델 안에서 빗썸–해외 김프 표준편차가 *해외 거래소 쌍 수준(0.2~0.3%)으로 수렴*하고, 한국 시장이 자본 유출의 구조적 동인을 제공하는 폭이 의미 있게 축소된다.

더 중요한 것은 이를 통해 한국이 **블록체인·Web3 시장에서의 위치를 회복**할 수 있다는 점이다. 현행 규제는 한국을 *고립된 retail 시장*으로 만들지만, 점진적 개방은 한국을 *동아시아 블록체인 금융 허브*로 전환할 가능성을 연다. 한국에는 이미 글로벌 수준의 IT 인프라, 결제 시스템, 그리고 가장 활발한 개인 투자자층이 있다. 빠진 것은 *글로벌 자본과의 연결성* 뿐이다.

### 9. 후속 연구 7개 의제 (논문 §8)

논문은 다음 7개의 후속 연구 의제를 명시한다:

1. **BTCB vs WBTC 자연 실험** — 동일 자산의 두 체인 버전 비교
2. **다종 BSC 토큰 패널 분석** — CAKE, BAKE, ALPACA 등으로 확장
3. **트래블룰 효과의 명시적 분석** — 2022-03-25 단절점 모델
4. **DEX–CEX 가격 발견 미시구조 분석**
5. **패닉/유포리아 비대칭의 행동경제학적 해석**
6. **무차익 밴드 이탈 지속 시간(duration) 분석**
7. **비한국 거래소 spread의 실증 검증** — Binance·OKX·Bybit 동시 1분봉 BTC 데이터로 본 논문의 핵심 식별 가설 검증

### 10. 저자 코멘트 (보도자료 인용)

> "김치 프리미엄은 단순히 '한국 사람들이 코인에 열광해서' 생기는 현상이 아닙니다. 비한국 거래소들 사이의 BTC 본위 가격 격차가 사실상 영(0)에 수렴한다는 점은, 차익거래 채널만 살아있으면 시장이 가격 격차를 빠르게 해소한다는 명백한 증거입니다.
>
> 자릿수가 다른 빗썸–해외 격차는 한국 시장이 봉쇄됐기 때문에 생기는 것이며, 그 비용은 9년간 적발된 것만 14.2조원의 자본 유출로 한국 경제가 떠안고 있습니다. KYC/AML은 그대로 강하게 유지하면서 외국인 접근 규제만 자율화해도, 김치 프리미엄은 구조적으로 축소될 수 있습니다."
>
> — 김호광(HoKwang Kim), 베타랩스 대표 · 전 Cyworld Z CEO

---

## 후속 논문 4편 — 시장 미시구조 & LLM 평가 (한국어)

### 후속 1. BNB-ETH 방향성 디커플링 (SSRN 6750298)

**Working Paper v9.2 Final · 27페이지 · 9차례 개정**

**기여**: 표준 암호화폐 요인 모형은 β를 시스템 위험 노출의 *충분 통계량*으로 사용한다. 그러나 항등식 β = ρ × (σ_i / σ_m) 는 β가 두 가지 다른 이유로 변할 수 있음을 의미한다: *상관관계 채널* 또는 *변동성 비율 채널*. 본 논문은 두 채널을 분리하는 **분산 분해 프레임워크**를 제안하고 CoinMetrics 일별 데이터(2022.05~2026.04, n=1,460)로 BNB-ETH 사례에 적용. **BNB의 ETH 대비 정적 베타가 16.9% 하락(0.643→0.534)했음에도 Pearson 상관계수는 0.731→0.731로 사실상 불변** — 정적 베타 변화의 **100%가 변동성 비율 채널**, 0%가 상관관계 채널. 분자/분모 분해 결과 **BNB 측 57%, ETH 측 43%** 기여.

**특징**: 9차례 개정 중 두 전략적 터닝 포인트(v5.0 통제군 확장 → DeFi 재커플링 발견, v9.0 방법론 paper로 재포지셔닝). DCC-GARCH 동적 베타 0.575→0.541 (−5.84%, p<0.001). 합성대조군 sensitivity 검증, 이벤트 스터디 null 결과 정직 보고.

**시사점**: Liu & Tsyvinski(2021), Liu et al.(2024) 등 표준 암호화폐 요인 모형이 β만 보는 관행에 *방법론적 경고*. 프레임워크는 모든 자산-벤치마크 쌍에 적용 가능.

[자세한 내용 → BNB_ETH Relationship readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNB_ETH%20Relationship/readme.md)

### 후속 2. CEX 에어드롭 분배 비대칭 (SSRN 6688740)

**Preliminary Working Paper v1.2 · 2026-05-01**

**기여**: 바이낸스가 2024~2025년 사이 약 **26억 달러**를 76개 이상의 보상 프로그램(Megadrop · HODLer · Launchpool)을 통해 BNB 보유자에게 분배한 현상을 (i) BNB 보유자, (ii) 발행 재단, (iii) BNB Chain 생태계 세 행위자로 분리해 *차별적 영향*을 정량화. **7개 이론(Theorem)** 으로 foundation cost function을 형식화하고, Schelling(1960) coordination game과 Morris-Shin(1998) Global Games를 적용해 *즉시 매도가 Nash equilibrium dominant strategy*임을 증명.

**특징**: Foundation Disaster — Megadrop α = 7.3%에서 재단 손실 ≈ FDV의 30.5%, 비대칭 비율 R = 4.18. 임계 분배 비율 α* = 5.95% (Megadrop 통상 5~8% 범위가 *explosion zone* 내). 부트스트랩 95% CI (N=21): Megadrop 평균 −76.0%, Direct(with HYPE) 평균 +384.3%, Cohen's d = −1.52. Decoupling: Megadrop 시총 −75% 동안 BNB Chain TVL +47.2%, 거래량 +171.4%, 활성 지갑 +91.6%, BNB 가격 $629 → $1,030.

**시사점**: Allen-Berg-Lane(2023)의 *직접 에어드롭* 분석을 *CEX 매개 hybrid 에어드롭*으로 확장. Theorem 6 (Break-even impossibility)이 발행 후 *유동성 가뭄*의 구조적 원인 규명. DAXA·KoFIU 상장 심사 시 *재단 토큰 매각 일정 공시 의무화* 검토에 직접 근거.

[자세한 내용 → BNBChain readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNBChain/readme.md)

### 후속 3. LLM 출력 길이 × 컨트라리안 발굴 (SSRN 6705598)

**기여**: ChatGPT, Claude, DeepSeek, Gemini 4개 frontier LLM에 동일 프롬프트로 제약·바이오테크 종목 추천을 요청했을 때, *출력 길이*와 *컨트라리안 발굴률(다른 모델이 뽑지 않은 종목 비율)* 사이에 **Spearman ρ = −0.80**의 역상관 (ChatGPT 이상치 제외 시 ρ = −1.00). *정답이 정의되지 않는 도메인*에서 *다양성-as-output-property*라는 새로운 평가 차원 도입.

**특징**: **Compression-forces-selection 메커니즘** — 토큰 예산 자체가 *thought diversity hyperparameter*로 기능. 깔끔한 9페이지 empirical short paper. *Same LLM, Different Languages* v5 시리즈와 한 묶음.

**시사점**: LLM 앙상블 설계 시 *토큰 한도를 차등 부여*하면 ensemble diversity 증대. AI 헤지펀드 *기능적 동질화(functional homogenization)* 위험 — LTCM 1998년 사태와 같은 구조. Alpha Arena Season 1 결과 (GPT-5 −75% vs DeepSeek +46%)와 함께 *"모델 IQ ≠ 트레이딩 IQ"* 명제 강화.

[자세한 내용 → Harness Quant v2 readme](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quant%20v2%20readme%20.MD)

### 후속 4. 토큰 언락 72시간 충격 (SSRN 6632838)

**Working Paper v3.0 · 2026-04-23 · 22페이지**

**기여**: 2023~2025년 바이낸스 상장 자산에서 발생한 **52건의 주요 토큰 언락 이벤트**를 직접 수집해, 언락 직후 **72시간 윈도우**에서 abnormal return 측정. 52건 중 **46건(88.5%)** 음의 72시간 수익률, **평균 −16.97%** (binomial p = 2.2 × 10⁻⁹, Bonferroni 17개 형식 검정 후에도 유의). BTC 5개 regime ANOVA p = 0.24로 시장 환경에 무관하게 안정.

**특징**: Keyrock(2024)의 *30일·16,000건* 집계와 다른 **72시간 시간-한정 윈도우**로 분리. OLS 회귀로 언락 크기가 독립 음의 동인(β = −0.0089, p = 0.006). 10개 CSV + 8개 Python 스크립트로 **완전 재현** (`reproduce_all_tables.py` 한 번에 모든 표 재생성). 365일 anniversary 패턴은 *post-hoc*이라 명시적 한계 표명.

**시사점**: 단순 *언락 직전 short / 직후 covering* 전략의 통계적 유의성 확인. 거래소 측 *마진·차입 한도 일시 조정* 위험관리 정책 함의. DAXA의 *언락 캘린더 공시 의무화* 검토에 실증 근거.

[자세한 내용 → Token unlock 72h shock analysis readme](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/readme.MD)

---

# English

## Satoshi Kimp — Bithumb-Binance BTC-Numéraire Premium (SSRN 6756158)

> **Lead Paper** — Working Paper Version 5.1 · May 13, 2026 · Korean 19p · English 21p · Chinese 18p (Trilingual Edition)

**Direct document links**:
[Korean PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/ko/paper.pdf) · [English PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/en/paper_en.pdf) · [Press Release (Korean)](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/Press%20Release%20KR.md) · [Full Folder](https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper)

### One-Line Summary

**The kimchi premium is not a market inefficiency but the price of Korea-specific regulatory friction. Detected capital flight totals KRW 14.2 trillion over 9 years. The structural solution is to allow foreigners to open accounts at Korean exchanges while maintaining KYC/AML/CFT.**

### 1. A New Measurement Tool — Satoshi Kimp (BTC-Numéraire Premium)

The standard kimchi premium, measured through KRW/USD, bundles four distinct factors: (i) FX rate, (ii) capital controls (FX Trade Act), (iii) USDT/USDC stablecoin premium, and (iv) remittance latency (Travel Rule). This measurement ambiguity has historically caused the literature to attribute the kimchi premium to behavioral hypotheses such as *"Korean retail irrationality."*

This paper proposes a new measure using BTC as the within-exchange numéraire:

```
π^BTC_X(t) = [P_Bithumb(X, KRW)/P_Bithumb(BTC, KRW)] / [P_Binance(X, USDT)/P_Binance(BTC, USDT)] − 1
```

**Proposition 1 (FX Noise Cancellation)** proves that the FX units in numerator and denominator cancel exactly. What remains is a *pure token-level asymmetry signal*: how much token X trades richer (or cheaper) versus BTC inside Bithumb compared to Binance. The folder name *"Satoshi kimp"* refers to a kimchi premium measured in satoshis — Bitcoin's smallest unit.

### 2. The Decisive Identification Result — An Order-of-Magnitude Asymmetry

Cross-exchange BTC-numéraire premium volatility, measured via the new framework (simulation):

| Exchange Pair | Korea Included? | std (ETH) | std (BNB) |
| --- | --- | --- | --- |
| Binance ↔ OKX | offshore ↔ offshore | **0.23%** | **0.22%** |
| Binance ↔ Bybit | offshore ↔ offshore | **0.25%** | **0.24%** |
| OKX ↔ Bybit | offshore ↔ offshore | **0.34%** | **0.32%** |
| **Bithumb ↔ Binance** | **Korea ↔ offshore** | **0.85%** | **1.59%** |
| **Bithumb ↔ OKX** | **Korea ↔ offshore** | **0.89%** | **1.61%** |
| **Bithumb ↔ Bybit** | **Korea ↔ offshore** | **0.90%** | **1.63%** |

**Key observation**: An order-of-magnitude asymmetry (3–7×) appears *only* in pairs containing a Korean exchange. Offshore arbitrageurs close cross-exchange spreads within minutes. Korean exchanges are walled off by the *FX Trade Act, Travel Rule, real-name virtual-account regime, and the ban on foreign retail trading* — regulations that **shut the arbitrage channel itself** — so wedges persist for days to weeks.

This is the first statistically discriminable evidence that the kimchi premium arises *not because Koreans love crypto* but *because the Korean market is sealed off*.

### 3. Quantitative Policy Cost — KRW 14.18 Trillion in Capital Flight Detected Over 9 Years

The cost of this regulatory friction is quantified by Korea Customs Service data (released by lawmaker Choi Eun-seok's office on 2025-10-21):

| Year | Cases | Amount Detected |
| --- | --- | --- |
| 2024 | 26 | **KRW 1.16 trillion** |
| Jan–Aug 2025 | 16 | **KRW 0.88 trillion** |
| **2018–2025 (9-year cumulative)** | **264** | **~KRW 14.18 trillion** |

Detection categories include **trade-payment-disguised remittance**, **unregistered FX business ("hwanchigi")**, and **shell-company channels**. The Korean Supreme Court ruled on 2025-09-04 (2024도16540) that "regulation-evasion-motivated disguised remittance" constitutes unregistered FX business.

This KRW 14.18 trillion represents *detected transactions only* — actual capital flight is presumably larger. Not every detected case stems from kimchi-premium arbitrage, so the paper uses this figure cautiously as an *indirect indicator* of the policy cost. Even so, the mechanism is clear: **when regulation seals the arbitrage channel, capital escapes through dark channels.**

### 4. Natural-Experiment Episode — December 2024 Martial Law, −32%

A natural experiment occurred during the sample window. On **December 3, 2024**, Korea's emergency martial-law declaration drove the kimchi premium to an extreme **negative −32%**. The simulation reproduces how political shocks propagate through the BTC-numéraire channel.

### 5. Methodological Rigor

- **Data**: Daily synthetic series from 2020-01-01 to 2025-12-31 (T = 2,192). Calibrated to *stylized facts* from Makarov & Schoar (2020, JFE), Choi et al. (2022), Eom (2021), Tiger Research (2024). Appendix A documents moment-matching (e.g., BTC kimp AR(1) coefficient 0.911 vs Choi et al. 2022's reported 0.85–0.95).
- **Estimation**: OLS with **Newey–West HAC** standard errors; asymmetric volatility via **EGARCH(1,1) with Student-t innovations**; token-level idiosyncratic volatility controlled via standardized variance ratio **ρ_X**.
- **Reproducibility**: Fixed random seed (20260513); full Python build scripts open-sourced.
- **Asset panel**: BNB (Bithumb listing 2021-05-27), Venus (XVS, BSC DeFi), ETH (baseline).

### 6. Academic Significance — Three Contributions

1. **A new measurement tool**: The *first academic paper* to use BTC as numéraire to redefine the kimchi premium. Separating FX, capital-controls, and stablecoin noise *at the measurement stage* is the core methodological advance.
2. **A new identification strategy**: Directly comparing BTC-numéraire premium volatility between offshore-vs-offshore exchange pairs and Korea-containing pairs allows *statistical discrimination* between "market inefficiency" and "regulatory cost." This is a first-in-literature natural comparison design.
3. **Methodological rigor**: Full toolkit of financial econometrics — Newey–West HAC, Student-t EGARCH(1,1), standardized variance ratios — plus *reproducibility* via fixed seed and open build scripts.

### 7. Policy Implications — Openness for Korean Blockchain Market Leadership

The paper notes its recommendations are *academic* and real policy should follow empirical follow-ups using actual exchange API data. Still, the direction the simulation evidence points is unambiguous.

**Recommendation 1 — Gradual Liberalization of Foreign Access to Korean Exchanges (Core Recommendation)**

The current ban on foreign retail trading:

- *Seals off arbitrageurs*, the core mechanism sustaining the kimchi premium
- Imposes *welfare loss on Korean retail investors* through inefficient pricing
- *Forces arbitrage capital into illegal channels* (hwanchigi, disguised remittances) — the dark mirror of capital flight
- Blocks Korea from emerging as a *competitive trading hub* in global blockchain/Web3 markets

→ **Allow foreigners to open accounts and trade on Korean exchanges, on a gradual liberalization track.** This reconnects Korea to the global arbitrage network. Allowing foreign access via legitimate KYC channels actually *improves* AML outcomes — the same money that currently exits through hwanchigi would enter through traceable normal channels.

**Recommendation 2 — Maintain or Strengthen KYC/AML/CFT**

Anti-money-laundering (AML), counter-terrorist-financing (CFT), and customer-due-diligence (KYC) frameworks should remain at *current or higher intensity* per FATF Recommendation 16. This is *independent of* foreign market access — the two recommendations do not conflict.

**Recommendation 3 — Build Out KRW-Pegged Stablecoin Infrastructure**

If the Travel Rule cuts arbitrage along the *time* dimension, a KRW stablecoin within the same KYC standard provides a *path* dimension, creating a legitimate arbitrage channel. This is also the starting point for Korea's *integration of won payments with blockchain settlement* — a foundation for next-generation financial infrastructure.

### 8. Korean Blockchain Market Leadership Strategy

When these three recommendations operate together, the simulation model shows Bithumb–offshore standard deviations converging to *offshore-pair levels (0.2–0.3%)*, with Korea no longer providing structural fuel for capital flight.

More importantly, this path enables Korea to **recover its position in the blockchain/Web3 market**. Current regulation makes Korea an *isolated retail market*, but gradual openness can turn Korea into an *East Asian blockchain financial hub*. Korea already has world-class IT infrastructure, payments systems, and arguably the most active retail investor base in crypto. The missing piece is *connectivity to global capital* — which the proposed reforms restore.

### 9. Seven Follow-Up Research Agendas (Paper §8)

(1) BTCB vs WBTC natural experiment, (2) Multi-BSC-token panel (CAKE, BAKE, ALPACA, …), (3) Explicit analysis of the Travel Rule (2022-03-25 break point), (4) DEX–CEX price-discovery microstructure, (5) Behavioral interpretation of panic/euphoria asymmetry, (6) No-arbitrage band exit-duration analysis, (7) Empirical verification of offshore-exchange spreads using simultaneous 1-minute BTC data from Binance, OKX, and Bybit.

### 10. Author Comment (from Press Release)

> "The kimchi premium is not simply because 'Koreans love crypto.' The fact that BTC-numéraire price gaps among non-Korean exchanges converge essentially to zero is unambiguous evidence that markets close spreads quickly when the arbitrage channel is open.
>
> The order-of-magnitude Bithumb–offshore gap exists because the Korean market is walled off — and the cost has been borne by the Korean economy as roughly KRW 14.2 trillion in detected capital flight over nine years. Keeping KYC/AML strong while only liberalizing foreign access could structurally compress the kimchi premium."
>
> — HoKwang Kim, CEO of Betalabs Inc.; former CEO of Cyworld Z

---

## Supporting Papers (English) — Market Microstructure & LLM Evaluation

### Supporting Paper 1. Directional Decoupling — BNB-ETH (SSRN 6750298)

**Working Paper v9.2 Final · 27 pages · 9 major revisions**

**Contribution**: Standard cryptocurrency factor models treat β as a sufficient statistic for systematic risk. The identity β = ρ × (σ_i / σ_m) implies β can change for two distinct reasons: a *correlation channel* or a *volatility-ratio channel*. This paper proposes a **variance-decomposition framework** isolating the two and applies it to BNB-ETH via CoinMetrics daily data (May 2022–Apr 2026, n=1,460). BNB's static beta to ETH fell 16.9% (0.643 → 0.534) while Pearson correlation remained essentially unchanged (0.731 → 0.731) — **100% of static beta change is attributable to the volatility-ratio channel**, 0% to correlation. Further numerator/denominator decomposition: BNB-side 57%, ETH-side 43%.

**Characteristics**: 9 major revisions; two strategic turning points (v5.0 control-pool expansion revealed DeFi recoupling; v9.0 strategic repositioning from causal-effect to methodology paper). DCC-GARCH dynamic beta 0.575 → 0.541 (−5.84%, p<0.001). Synthetic-counterfactual sensitivity reported in both main (14-donor) and sensitivity (16-donor) specs. Spot ETH ETF event-study null result honestly reported.

**Implications**: A methodological warning against factor models à la Liu & Tsyvinski (2021), Liu et al. (2024) that rely on β alone. The decomposition framework generalizes to any asset-benchmark pair.

[Full details → BNB_ETH Relationship readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNB_ETH%20Relationship/readme.md)

### Supporting Paper 2. CEX Airdrop Distribution Asymmetry (SSRN 6688740)

**Preliminary Working Paper v1.2 · May 1, 2026**

**Contribution**: Binance distributed approximately **USD 2.6 billion** to BNB holders during 2024–2025 across 76+ reward programs (Megadrop, HODLer, Launchpool) — ~94% of global CEX distributions. This paper decomposes the differential impact across three actors: (i) BNB holders, (ii) issuing foundations, (iii) the BNB Chain ecosystem. Seven theorems formalize the foundation cost function; Schelling (1960) coordination games and Morris-Shin (1998) Global Games prove *immediate sell-off is the Nash-equilibrium dominant strategy*.

**Characteristics**: Foundation Disaster — at Megadrop's typical α = 7.3%, foundation cost ≈ 30.5% of FDV; asymmetry ratio R = 4.18. Critical distribution ratio α* = 5.95% (Megadrop's typical 5–8% range sits in the *explosion zone*). Bootstrap 95% CI (N=21): Megadrop −76.0%, Direct (with HYPE) +384.3%, Cohen's d = −1.52. Decoupling: Megadrop-category market cap −75% while BNB Chain TVL +47.2%, volume +171.4%, active wallets +91.6%, BNB price $629 → $1,030.

**Implications**: Extends Allen-Berg-Lane (2023) on *direct airdrops* to the new category of *CEX-mediated hybrid airdrops*. Theorem 6 (Break-even impossibility) explains the *structural post-listing liquidity drought*. Direct evidence for DAXA/KoFIU to require *foundation-side token release schedule disclosure*.

[Full details → BNBChain readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNBChain/readme.md)

### Supporting Paper 3. Less Volume, More Variety (SSRN 6705598)

**Contribution**: Identical prompts to four frontier LLMs (ChatGPT, Claude, DeepSeek, Gemini) for pharma/biotech stock selection produce a **Spearman ρ = −0.80** between *output length* and *contrarian discovery rate* (ρ = −1.00 excluding ChatGPT). Introduces *diversity-as-output-property* as an evaluation dimension for domains where ground truth is undefined.

**Characteristics**: Names the **compression-forces-selection mechanism** — token budget itself as a *thought-diversity hyperparameter*. A 9-page empirical short paper. Sits alongside the *Same LLM, Different Languages* v5 series.

**Implications**: For LLM ensemble design, *vary token budgets across constituent models* to increase diversity. For AI hedge funds, *functional homogenization* is the LTCM 1998 risk pattern. Anchored empirically by Alpha Arena Season 1 results (GPT-5 −75% vs DeepSeek +46%) reinforcing *"model IQ ≠ trading IQ."*

[Full details → Harness Quant v2 readme](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quant%20v2%20readme%20.MD)

### Supporting Paper 4. The 72-Hour Shock — Token Unlocks (SSRN 6632838)

**Working Paper v3.0 · Apr 23, 2026 · 22 pages**

**Contribution**: A hand-collected sample of **52 major token unlock events on Binance-listed assets between January 2023 and December 2025**, analyzed via event study within a tight **72-hour post-unlock window**. **46 of 52 events (88.5%)** exhibit negative 72-hour returns, mean −16.97% (binomial p = 2.2 × 10⁻⁹; robust to Bonferroni correction across 17 formal tests). The effect persists across five BTC regimes (ANOVA p = 0.24) and survives ETH and top-10 market-cap-weighted benchmarks.

**Characteristics**: Sharpens Keyrock's (2024) *30-day, 16,000-event* aggregate by isolating the **72-hour temporal concentration**. OLS regression confirms unlock size as an independent driver (β = −0.0089, p = 0.006, HC1 robust SE). **Fully reproducible**: 10 CSV datasets + 8 Python scripts; `reproduce_all_tables.py` regenerates every paper table. The 365-day anniversary pattern is transparently flagged as *post-hoc*.

**Implications**: Validates a simple *short-before-unlock / cover-after* strategy statistically. Motivates *margin/borrow-limit tightening* around unlocks. Provides DAXA an empirical case for *mandatory unlock-calendar disclosure*.

[Full details → Token unlock 72h shock analysis readme](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/readme.MD)

---

# Chinese / 中文

## Satoshi Kimp (聪本位泡菜溢价) — Bithumb-Binance BTC-Numéraire 溢价 (SSRN 6756158)

> **代表论文 · Lead Paper** — Working Paper Version 5.1 · 2026-05-13 · 韩文 19 页 · 英文 21 页 · 中文 18 页 (三语版)

**文档直接链接**:
[韩文 PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/ko/paper.pdf) · [英文 PDF](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/en/paper_en.pdf) · [韩文新闻稿](https://github.com/gameworkerkim/vibe-investing/blob/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper/Press%20Release%20KR.md) · [完整文件夹](https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper)

### 一句话总结

**泡菜溢价不是市场低效,而是韩国特有监管摩擦的价格成本。9 年累计 14.2 万亿韩元资本外流已被查获。结构性解决方案: 在维持 KYC/AML/CFT 的同时,允许外国人在韩国交易所开户。**

### 核心发现 (摘要)

传统泡菜溢价通过韩元/美元汇率测量,因此包含 (i) 汇率、(ii) 资本管制、(iii) USDT 稳定币溢价、(iv) 汇款延迟等多个因素的混合。本文提出使用 BTC 作为交易所内部计价单位 (numéraire) 的新测量公式 **π^BTC_X(t)**,并通过 **命题 1 (FX 噪声消除)** 证明: 分子-分母的汇率单位在数学上完全抵消。剩下的是仅识别 *纯代币级不对称* 的信号。

**决定性识别结果 (跨交易所对 BTC 本位泡菜溢价标准差,模拟):**

| 交易所对 | 含韩国? | std (ETH) | std (BNB) |
| --- | --- | --- | --- |
| Binance ↔ OKX (海外-海外) | 否 | **0.23%** | **0.22%** |
| Binance ↔ Bybit (海外-海外) | 否 | **0.25%** | **0.24%** |
| OKX ↔ Bybit (海外-海外) | 否 | **0.34%** | **0.32%** |
| **Bithumb ↔ Binance** | **是** | **0.85%** | **1.59%** |
| **Bithumb ↔ OKX** | **是** | **0.89%** | **1.61%** |
| **Bithumb ↔ Bybit** | **是** | **0.90%** | **1.63%** |

**数量级的不对称 (3-7 倍) 仅在包含韩国交易所的对中出现**。海外交易所之间套利者以分钟为单位消除价格差异,但韩国交易所因 *外汇交易法、Travel Rule、实名认证虚拟账户制度、外国人交易禁令* 等 **封闭套利渠道本身的监管** 导致价格背离持续数天至数周。

### 定量政策成本 — 韩国海关 9 年累计 14.18 万亿韩元

韩国关税厅数据 (韩国国民力量党崔殷錫议员办公室 2025-10-21 公开): 2018-2025 年 9 年间通过虚拟资产的非法外汇交易查获金额累计约 14.18 万亿韩元。查获类型包括贸易货款伪装汇款、无登记外汇业务 ("换钱者")、空壳公司利用等。韩国最高法院 2025-09-04 (2024도16540) 判决"以规避监管为目的的伪装汇款"构成无登记外汇业务。**仅为已侦测案件统计,实际资本外流估计更大。**

### 三项政策建议 — 开放促进韩国区块链市场领导地位

**建议 1 — 渐进放开外国人在韩国交易所开户和交易 (核心建议)**: 现行外国人交易禁令封锁套利者,是 *维持泡菜溢价的核心机制*,并强制套利资金 *通过伪装汇款、换钱者等非法渠道流出*。**允许外国人通过合法 KYC 渠道在韩国交易所开户并交易**,将韩国市场重新连接到全球套利网络。通过合法 KYC 渠道允许外国人接入实际上 *改善* AML 结果。

**建议 2 — KYC/AML/CFT 维持或加强**: 反洗钱、反恐融资、客户身份识别按 FATF Recommendation 16 等全球标准 *维持或加强当前强度*。与外国市场开放是 *独立* 问题。

**建议 3 — 韩元稳定币基础设施建设**: 如果 Travel Rule 阻断套利的"时间"维度,韩元稳定币在同一 KYC 标准内提供"路径"维度,创建合法套利渠道。

### 学术意义

1. **新测量工具**: 使用 BTC 作为 numéraire 重新定义泡菜溢价的 *第一篇学术论文*。
2. **新识别策略**: 通过直接比较海外-海外对 vs 含韩国对的 BTC 本位泡菜溢价波动率,可以 *统计上区分* 泡菜溢价是"市场低效"还是"监管成本"。
3. **方法论严谨性**: Newey–West HAC、Student-t EGARCH(1,1)、标准化方差比等金融计量经济学标准工具 + 完整可复制性。

### 韩国区块链市场领导地位战略

当这三项建议共同运作时,模拟模型显示 Bithumb-海外标准差收敛至 *海外对水平 (0.2-0.3%)*,韩国不再为资本外流提供结构性燃料。更重要的是,这条路径使韩国能够 **恢复在区块链/Web3 市场中的地位**。当前监管使韩国成为 *孤立的零售市场*,但渐进开放可以将韩国转变为 *东亚区块链金融枢纽*。韩国已经拥有世界级 IT 基础设施、支付系统、以及加密领域可能最活跃的零售投资者群体。缺失的部分是 *与全球资本的连接性* — 而本文提出的改革将恢复这一连接。

---

## 后续论文 4 篇 (中文) — 市场微观结构与 LLM 评估

### 后续 1. BNB-ETH 方向性脱钩 (SSRN 6750298)

**Working Paper v9.2 Final · 27 页 · 9 轮主要修订**

**贡献**: 通过 β = ρ × (σ_i / σ_m) 提出 **方差分解框架**,将 β 变化分为相关性渠道和波动率比率渠道。对 BNB-ETH 应用 (n=1,460): 静态 β 下降 16.9% (0.643→0.534) 而 Pearson 相关系数基本不变 (0.731→0.731) — **100% 归因于波动率比率渠道**,0% 相关性渠道。分子/分母分解: BNB 端 57%、ETH 端 43%。

**启示**: 对 Liu & Tsyvinski (2021) 等仅依赖 β 的因子模型的方法论警示。框架适用于任何资产-基准对。

[详细信息 → BNB_ETH Relationship readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNB_ETH%20Relationship/readme.md)

### 后续 2. CEX 空投分配不对称性 (SSRN 6688740)

**初步工作论文 v1.2 · 2026-05-01**

**贡献**: 币安 2024-2025 年通过 76+ 奖励计划向 BNB 持有者分配约 **26 亿美元**。本论文将影响分解到 BNB 持有者、发行基金会、BNB Chain 生态系统三个行为者,通过 7 个定理形式化基金会成本函数。Megadrop α = 7.3% 下,基金会成本 ≈ FDV 的 30.5%,不对称比 R = 4.18。

**启示**: 将 Allen-Berg-Lane (2023) 直接空投分析扩展到 CEX 中介混合空投。为 DAXA/KoFIU 要求基金会代币释放计划披露提供直接证据。

[详细信息 → BNBChain readme](https://github.com/gameworkerkim/vibe-investing/blob/main/02.Investment%20Idea%20Column/BNBChain/readme.md)

### 后续 3. Less Volume, More Variety (SSRN 6705598)

**贡献**: 向 ChatGPT、Claude、DeepSeek、Gemini 输入相同提示进行制药股票选择,产生输出长度与逆向发现率之间的 **Spearman ρ = −0.80**。引入 *diversity-as-output-property* 评估维度。

**启示**: LLM 集成设计应 *改变 token 预算*。AI 对冲基金面临 *functional homogenization* 风险 — LTCM 1998 同构。

[详细信息 → Harness Quant v2 readme](https://github.com/gameworkerkim/vibe-investing/blob/main/Harness%20quant%20v2%20readme%20.MD)

### 后续 4. 72 小时冲击 — 代币解锁 (SSRN 6632838)

**Working Paper v3.0 · 2026-04-23 · 22 页**

**贡献**: 手工收集 2023-2025 年币安上市资产中 **52 起主要代币解锁事件**,通过事件研究测量 72 小时后的 abnormal return。**46/52 (88.5%)** 显示负 72 小时收益率,平均 −16.97% (binomial p = 2.2 × 10⁻⁹,Bonferroni 校正后稳健)。

**启示**: 验证简单的 *解锁前做空 / 解锁后回补* 策略统计可行性。为 DAXA 考虑强制解锁日历披露提供实证基础。

[详细信息 → Token unlock 72h shock analysis readme](https://github.com/gameworkerkim/vibe-investing/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/readme.MD)

---

# 통합 의의 (Integrated Significance)

## 한국 가상자산 규제 실패의 학술적 진단과 정책 처방

본 5편의 작업 논문은 *한국 가상자산 시장 규제의 구조적 실패*를 학술적으로 진단하고, 그 해법으로서 **개방을 통한 블록체인 시장 우위 확보** 전략을 제시한다.

**대표 논문(사토시 김프)** 은 김치 프리미엄을 시장 비효율이 아닌 *규제 마찰의 가격 비용*으로 재정의하고, 9년간 14.2조원의 자본 유출이 *불법 채널을 통해* 발생했음을 정량화한다. 이는 한국 규제가 자국 retail 투자자에게 *비효율적 가격을 부담시키고*, 자본을 *불법 채널로 강제 유도*하며, 한국이 *글로벌 블록체인 시장에서 경쟁력을 잃게 만든다*는 세 가지 실패 패턴을 동시에 보여준다.

**후속 논문 4편**은 이 진단을 뒷받침하는 시장 미시구조 증거를 제공한다:

- **토큰 언락 72시간 충격** (#1, SSRN 6632838) — 시장이 *예측 가능한 공급 충격에도 비효율적으로 반응*하며, 한국 규제는 이를 회피할 수 있는 차익거래 도구를 retail에게 허용하지 않는다
- **BNB Megadrop 분배 비대칭** (#2, SSRN 6688740) — *BNB 보유자 + 재단 + 생태계* 세 행위자 간의 부의 비대칭이 한국에서도 동일하게 작동하지만, 외국인 차익거래자가 없어 *retail의 후생 손실을 더 크게 만든다*
- **LLM 출력 길이 × 컨트라리안 발굴** (#3, SSRN 6705598) — *AI 기반 트레이딩의 동질화 위험*에 대한 경고이며, 한국이 *AI 헤지펀드와 같은 차세대 금융 기술*을 흡수하려면 글로벌 시장과의 *연결성*이 필수다
- **BNB-ETH 방향성 디커플링** (#4, SSRN 6750298) — *exchange-native 토큰의 미시구조 분해 프레임워크*로, BNB 같은 거래소 토큰이 다른 토큰과 어떻게 다르게 움직이는지 보여준다. 한국 거래소도 자체 토큰을 고려한다면 이 프레임워크가 직접 적용된다

## 정책 권고의 통합 (Integrated Policy Recommendation)

다섯 편의 연구를 종합한 정책 권고는 다음 세 축으로 모인다.

1. **외국인의 한국 거래소 계좌 개설 및 거래 자율화** (대표 논문 권고) — 김치 프리미엄을 구조적으로 축소하고, 14조원 규모의 *불법 자본 유출을 정상 채널로 전환*하며, 한국을 동아시아 블록체인 금융 허브로 재포지셔닝한다.
2. **상장·언락·재단 공시 의무화** (후속 1, 2 권고) — 토큰 언락 캘린더와 재단 보유 토큰 매각 일정을 *DAXA 차원에서 의무 공시*함으로써 retail 후생 손실을 줄인다.
3. **KYC/AML/CFT는 강도 유지 또는 강화 + 원화 스테이블코인 인프라 정비** — 위 두 권고와 *독립적·병행적*으로 진행 가능하며, 글로벌 표준에 부합하면서도 정상 차익거래 채널을 구축한다.

이 3-축 정책은 *상호 모순되지 않는다*. 오히려 함께 작동할 때 한국이 글로벌 블록체인 시장에서 *경쟁력 있는 위치*를 회복하고, 동시에 자금세탁 방지 측면에서도 *현재보다 더 강한 통제력*을 갖게 된다.

---

# 인용 / Citation / 引用

## BibTeX

```bibtex
@techreport{kim2026_satoshi,
  author      = {Kim, HoKwang},
  title       = {The {Bithumb}--{Binance} {BTC}-Num{\'e}raire Premium:
                 A Theoretical Framework with Calibrated Simulation
                 Evidence on {BNB} Chain Tokens},
  institution = {Betalabs Inc.},
  type        = {Working Paper},
  year        = {2026},
  month       = {may},
  version     = {5.1},
  note        = {Trilingual Edition (Korean 19p, English 21p, Chinese 18p), 2026-05-13.
                 SSRN submission in progress. Lead paper of the SSRN Working Papers series.},
  doi         = {10.2139/ssrn.6756158},
  url         = {https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper}
}

@misc{kim2026_decoupling,
  author    = {Kim, HoKwang},
  title     = {Directional Decoupling and the Volatility-Ratio Channel:
               A Beta-Decomposition Framework for Exchange-Native Tokens ---
               Evidence from the {BNB}-{ETH} Relationship, 2022--2026},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6750298},
  url       = {https://ssrn.com/abstract=6750298},
  note      = {SSRN Working Paper No.~6750298}
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
```

---

# 폴더 구조 / Folder Structure / 文件夹结构

```
Paper 논문/
├── readme.md                                                  # This file (trilingual, SEO-optimized)
├── CITATION.cff                                               # GitHub-recognized citation metadata
├── BIBLIOGRAPHY.bib                                           # All 5 papers in BibTeX
├── BIBLIOGRAPHY.ris                                           # All 5 papers in RIS
├── Satoshi kimp Paper/                                        # LEAD PAPER (Version 5.1, 2026-05-13)
│   ├── Press Release KR.md                                    # Press Release (Korean)
│   ├── ko/
│   │   └── paper.pdf                                          # Korean paper (19p)
│   ├── en/
│   │   └── paper_en.pdf                                       # English paper (21p)
│   └── zh/
│       └── paper_zh.pdf                                       # Chinese paper (18p)
├── 02_SSRN-6750298_Directional-Decoupling.md                  # Supporting Paper 1
├── 03_SSRN-6688740_Distribution-Asymmetry-BNB.md              # Supporting Paper 2
├── 04_SSRN-6705598_Less-Volume-More-Variety.md                # Supporting Paper 3
└── 05_SSRN-6632838_72-Hour-Shock.md                           # Supporting Paper 4
```

Supporting Papers 1, 2, 4 also have full sub-folder READMEs at their original `vibe-investing` locations (see [Paper List](#논문-목록--paper-list--论文列表) for direct links).

---

# 라이선스 / License / 许可证

- **Preprint text & abstracts**: [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — share and adapt with attribution to HoKwang Kim and SSRN DOI
- **Associated code & scripts**: [MIT License](https://opensource.org/licenses/MIT)
- **Data**: see each paper's data availability statement and the [`vibe-investing`](https://github.com/gameworkerkim/vibe-investing) companion repository

---

# 연락처 / Contact / 联系方式

**HoKwang Kim (김호광 / Dennis Kim)** — CEO, Betalabs Inc., Seoul, South Korea

| Channel | Address |
| --- | --- |
| Email | <gameworker@gmail.com> |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN Author Page | <https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088> |
| GitHub | <https://github.com/gameworkerkim> |
| Companion Repository | <https://github.com/gameworkerkim/vibe-investing> |
| Lead Paper Folder | <https://github.com/gameworkerkim/vibe-investing/tree/main/Paper%20%EB%85%BC%EB%AC%B8/Satoshi%20kimp%20Paper> |

For media inquiries, academic collaboration, regulatory consultation, or speaking requests regarding the Satoshi Kimp paper or the broader research series, please contact via email above.

---

## 검색 키워드 / Search Keywords / 搜索关键词

**한국어**: 김치 프리미엄, 사토시 김프, BTC 본위 김프, 한국 가상자산 규제, 외국인 거래소 계좌 개설, 외국인 가상자산 거래 허용, 빗썸 바이낸스 차익거래, 외환거래법, 트래블룰, DAXA, KoFIU, 김호광, 베타랩스, BNB 체인, 토큰 언락, CEX 에어드롭, 국부 유출, 규제 실패, 한국 블록체인 시장, 자본 유출, 무등록 외국환업무, 환치기, Web3 정책

**English**: kimchi premium, Satoshi Kimp, BTC numéraire, Korean cryptocurrency regulation, foreign account Korean exchange, Bithumb Binance arbitrage, Korean FX Trade Act, Travel Rule, DAXA, KoFIU, HoKwang Kim, Betalabs, BNB Chain, token unlock, CEX airdrop, capital flight Korea, regulatory failure, Korean blockchain market, Korean Web3 policy

**中文**: 泡菜溢价, Satoshi Kimp, BTC 计价单位, 韩国加密货币监管, 韩国交易所外国人开户, Bithumb 币安套利, 韩国外汇交易法, Travel Rule, DAXA, KoFIU, HoKwang Kim, Betalabs, BNB 链, 代币解锁, CEX 空投, 韩国资本外流, 监管失败, 韩国区块链市场

---

*Last updated: 2026-05-17 · Trilingual (Korean · English · Chinese) · Maintained by HoKwang Kim*
*Lead Paper: The Bithumb-Binance BTC-Numéraire Premium (SSRN 6756158) · Series of 5 SSRN Working Papers*
