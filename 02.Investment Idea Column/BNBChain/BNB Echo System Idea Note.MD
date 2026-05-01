# 아이디어 노트 — 거래소 에어드롭의 분배 비대칭

## Phase 5 연구 프로그램: Megadrop·HODLer Airdrop 의 매도 압력 정량화

**저자**: 김호광 (HoKwang Kim, Independent Researcher)
**상태**: 사전-연구 아이디어 정리 문서
**작성일**: 2026년 5월 1일
**소속 시리즈**: vibe-investing 연구 시리즈 (Phase 5 후보)

---

## 본 문서의 목적

본 문서는 vibe-investing 연구 프로그램의 **다섯 번째 후보 논문**을 위한 연구 설계를 담은 워킹 노트이다. 다음 내용을 정립한다:

1. **연구 질문과 가설** — 거래소 에어드롭이 신규 상장 토큰의 가격에 가하는 매도 압력을 정량화할 수 있는가
2. **방법론 프레임워크** — 어떤 데이터, 어떤 검정, 어떤 통제
3. **시장 사이클 통제 설계** — Q3 2025 강세장 데이터로 시장 효과를 분리하는 방법
4. **Phase 1-4와의 관계** — 동일 데이터 환경(Binance), 동일 방법론(BTC-relative), 다른 유닛(언락 vs 상장)
5. **법적·윤리적 안전장치** — 거래소·재단을 비난하지 않으면서 데이터 패턴을 보고하는 방법

본 문서는 **아이디어 단계 문서이며, 실행 약속이 아니다.** 실행 결정은 Phase 2 (N=200 72시간 쇼크 확장)이 완료되고, 자매 칼럼 *"바이낸스 Megadrop과 HODLer Airdrop의 두 얼굴"* (2026년 5월 게재)이 6-12개월의 시장 검증을 받은 후 내려질 것이다.

---

## 1. 연구 동기

### 1.1. 실무에서 관찰된 패턴

저자의 아시아 암호화폐 생태계 8년 실무 경험(2017-2026) 동안, Binance 의 거래소 에어드롭 프로그램(Launchpool, Megadrop, HODLer Airdrop)을 둘러싼 반복적 패턴이 관찰되었다:

1. **분배 비율 증가의 추세**: Megadrop은 총 발행량의 5-8%, HODLer는 1-3% 범위로 분배된다. 이는 2020년대 초반의 일반적 분배 비율(0.5-1%) 대비 의미 있게 큰 비중이다.

2. **상장일 즉시 매도 패턴**: 2025년 6월 Spark (SPK) 토큰의 경우, HODLer Airdrop 분배 후 24시간 이내에 -54% 하락, 수 시간 이내 최저점 -70% 도달하였다. 다수의 보도가 *"airdrop farmer selling"*을 직접적 원인으로 지목했다.

3. **시장 사이클과 독립적 약세**: 2025년 Q3 알트 시즌 (ETH +68.5% QoQ, BNB +57.3% QoQ)에도 불구하고, Binance Megadrop 카테고리 토큰들의 시가총액은 약 $46.4M (2026년 4월 기준)으로 붕괴 상태를 유지했다. 이는 *시장 환경 효과로 설명되지 않는* 특이 패턴을 시사한다.

4. **BNB 홀더 vs 신규 매수자 수익 비대칭**: BNB 홀더는 2024-01 ~ 2025-03 기간 +177% 수익(Binance 공식). 같은 기간 Binance 신규 상장 토큰의 88.9%(24/27)가 음성 수익(Dune Analytics).

### 1.2. 연구의 공백

이러한 관찰은 실무자들에게는 알려져 있으나 실증적으로 문서화되지 않은 상태로 남아 있다. 기존 문헌은 인접한 질문들을 다룬다:

- **Keyrock (2024)**: 토큰 언락의 집계적 가격 영향
- **Félez-Viñas, Johnson, Putniņš (2022)**: 상장 공지 전 내부자 거래
- **Allen, Antoniou, Gu (2024)**: 암호화폐 IEO/IDO 의 가격 패턴
- **김호광 (2026) — 72시간 쇼크 (Phase 1)**: 언락 가격 영향의 시간적 집중

이들 중 어떤 연구도 체계적으로 다음을 다루지 않는다: (a) 거래소 에어드롭 분배 비율과 상장 후 가격 추이의 관계, (b) Megadrop vs HODLer vs Non-Airdrop 의 짝지은 비교, (c) 시장 사이클 통제 후 분배 메커니즘 자체의 본질적 영향, (d) BNB 체인 자체의 성장과 신규 토큰 부진의 디커플링.

### 1.3. 연구 기회

이 공백은 특히 **Binance 데이터 환경**에서 두드러진다. 그 이유는 다음과 같다.

1. Binance는 2024년 거래소 에어드롭 시장의 94% 점유 ($2.6B 분배 — CoinMarketCap)
2. 누적 분배 $3.5B+ across 76 projects (2020년 이후 — CoinMarketCap)
3. 2025년 한 해에만 27개 신규 상장 데이터 공개 (Dune Analytics)
4. 분배 비율이 프로젝트별로 명시 공시 (1-8% 범위, 충분한 변이)
5. Lorentz·Maxwell 하드포크(2025 Q2-Q3)로 BNB 체인 자체의 성장이 신규 토큰 부진과 디커플링되는 자연 실험 환경

저자의 실무자 네트워크와 Phase 1 SSRN 6632838에서 구축한 데이터 파이프라인은 이 연구를 효율적으로 실행할 수 있는 인프라를 제공한다.

---

## 2. 연구 질문과 가설

### 2.1. 핵심 연구 질문

**RQ1 (기술적)**: 거래소 에어드롭 분배 비율이 신규 상장 토큰의 30/90/180일 BTC-relative abnormal return 에 통계적으로 유의한 영향을 미치는가?

**RQ2 (비교적)**: Megadrop (5-8% 분배), HODLer (1-3% 분배), Launchpool (가변), Non-Airdrop 의 평균 ROI 격차는 통계적으로 유의한가?

**RQ3 (시장 사이클 통제)**: 시장 환경(BTC regime, ETH regime, 알트 시즌 더미)을 통제한 후에도 분배 메커니즘 자체의 영향이 유의하게 남는가?

**RQ4 (디커플링)**: BNB 체인의 거시 활동 지표(거래량, 활성 지갑, TVL, BNB 가격)는 신규 상장 토큰의 부진과 시간적으로 디커플링되는가?

**RQ5 (실용적)**: 분배 비율 5%를 임계점으로 가설할 수 있는가? 즉, 5% 이상 분배 토큰의 부진이 5% 미만 분배 토큰 대비 통계적으로 유의하게 큰가?

### 2.2. 공식 가설 (4-Tier 구조)

Phase 1 (72시간 쇼크) 에서 검증된 접근을 따라, 가설은 증가하는 강도로 구조화되며, 각 tier는 법적·통계적으로 방어 가능하다.

#### Tier 1 (가장 보수적, 거의 확실히 방어 가능)

**H1**: Megadrop 토큰의 30일 BTC-relative abnormal return 의 평균은 0과 통계적으로 유의하게 다르며, 음의 부호를 갖는다.

- *예측*: 평균 30일 BTC-relative return ≈ -30% ~ -50% (예비 데이터 기반)
- *검정*: One-sample t-test, μ ≠ 0
- *효과 크기*: Cohen's d ≥ 0.8 (large)

#### Tier 2 (중도)

**H2**: Megadrop 토큰의 평균 BTC-relative return은 HODLer 토큰의 평균 BTC-relative return 보다 통계적으로 유의하게 낮다.

- *예측*: Megadrop μ - HODLer μ < 0 (Megadrop 분배 비율이 더 크므로 매도 압력도 더 큼)
- *검정*: Two-sample t-test 또는 Mann-Whitney U
- *효과 크기*: Cohen's d ≥ 0.5 (medium)

#### Tier 3 (가장 강한 주장)

**H3**: 시장 사이클(BTC 30일 수익률, ETH 30일 수익률, 알트 시즌 더미)을 통제한 후에도, 에어드롭 분배 비율은 30일 BTC-relative abnormal return 에 통계적으로 유의한 부의 효과를 미친다.

- *예측*: β(분배비율) < 0, p < 0.01
- *검정*: 다중회귀 (OLS, 로버스트 SE)
- *모델*: BTC_relative_return = α + β1·distribution_ratio + β2·BTC_30d_return + β3·ETH_30d_return + β4·alt_season_dummy + γ·controls + ε

#### Tier 4 (탐색적)

**H4**: BNB 체인 거시 활동 지표 (분기별 거래량 증가율, TVL 증가율, BNB 가격 변동률) 는 신규 상장 토큰의 평균 ROI 와 시간적으로 디커플링된다.

- *예측*: 두 시계열 간 Granger causality 또는 Vector Autoregression 에서 약한 또는 비유의한 인과
- *검정*: Granger causality test, VAR
- *해석*: 디커플링이 확인되면, BNB 체인의 자체 성장이 신규 토큰 부진과 독립적으로 진행됨을 시사 (자기잠식 루프 가설의 부분 부정)

### 2.3. 가설 구조의 학술적 의미

이 4-tier 구조는 SSRN 6632838 (72시간 쇼크) 와 동일한 *방어 가능성 사다리* 를 따른다:

- Tier 1 → 이미 데이터로 명백 (88.9% 손실, 평균 -44%)
- Tier 2 → 분배 비율 차이가 효과 크기 차이로 이어지는지 검증
- Tier 3 → 가장 학술적으로 강한 주장. 시장 사이클 통제 후의 본질적 영향
- Tier 4 → 가설 자체에 대한 *반증 가능성* 제공. BNB 체인 디커플링이 확인되면 *자기잠식 루프 가설은 부분 부정*되며, 이는 본 연구의 학술적 정직성을 보강한다.

---

## 3. 방법론 프레임워크

### 3.1. 데이터 환경

#### 3.1.1. 표본 정의

**대상**: 2024년 1월 ~ 2025년 12월 사이 Binance 신규 상장 토큰
**예상 표본 크기**: N ≥ 100 (예비 추정)
- 2024년: 약 50개 (CoinMarketCap 보고서 기반 추정)
- 2025년: 27개 (Dethective on X)
- 2026년 Q1: 추가 데이터 수집

**카테고리 분류**:
- *Megadrop* (분배 5-8%): BounceBit (BB), Lista DAO (LISTA), Solv Protocol (SOLV), KernelDAO (KERNEL) 등
- *HODLer Airdrop* (분배 1-3%): Bubblemaps (BMT), APRO (AT), Spark (SPK), Plasma (XPL) 등 (59+ 사례)
- *Launchpool*: 가변 분배 (역사적으로 1-5%) — Saga, Ethena, PIXEL 등 (21건 in 2024)
- *Wallet IDO*: 별도 카테고리 (Binance Web3 Wallet 통한 IDO)
- *Non-Airdrop*: 직접 상장, 인센티브 프로그램 없음 — *희소 카테고리, 매칭 어려움*

#### 3.1.2. 데이터 출처

| 데이터 | 출처 | 검증 상태 |
|--------|------|----------|
| 분배 비율 | Binance 공식 공시 | 1차 검증 |
| 상장일 가격 | CoinGecko, CoinMarketCap | 1차 검증 |
| 시간별 가격 (T-30 ~ T+180) | CoinGecko API | 1차 검증 |
| 유통량 | tokenomist.ai, 프로젝트 공식 | 1차 검증 |
| BTC/ETH 가격 | CoinGecko API | 1차 검증 |
| BNB 체인 거시 지표 | Messari quarterly reports | 1차 검증 |

#### 3.1.3. 데이터 한계

- **Survivorship bias**: 상장 폐지 토큰의 최종 가격 누락 가능. 단 Binance의 2023-2024년 0% delisting rate 주장에 의존.
- **Non-Airdrop 표본 부족**: Binance의 거의 모든 신규 상장이 어떤 형태의 인센티브 프로그램과 함께 진행됨. 순수 "Non-Airdrop" 통제군이 작음.
- **시장 사이클 표본**: 2024-2025년은 강세장. 약세장 데이터로의 일반화는 추가 검증 필요.

### 3.2. 핵심 방법론

#### 3.2.1. BTC-relative abnormal return 계산

Phase 1 (72시간 쇼크) 와 동일한 방법론:

```
AR_i,t = R_i,t - β_i × R_BTC,t

where:
  R_i,t = 토큰 i 의 t시점 일일 수익률
  R_BTC,t = BTC 의 t시점 일일 수익률
  β_i = 토큰 i 의 사전 추정 BTC 베타 (T-90 ~ T-30 윈도우)

CAR_i,T = Σ AR_i,t (t = 0 to T)
```

- 시간 창: T = 30일 (주 분석), T = 90일 (보조), T = 180일 (장기)
- 베타 추정: T-90 ~ T-30 일일 수익률의 OLS (시장 데이터 충분 시)
- 베타 추정 불가능 (신규 토큰) 시 β = 1 가정 (보수적)

#### 3.2.2. 분배 비율 변수 정의

```
distribution_ratio_i = airdrop_amount_i / total_supply_i

categories:
  high (≥5%): Megadrop 대부분
  medium (1-5%): HODLer 대부분, 일부 Launchpool
  low (<1%): 일부 Wallet IDO
  none (0%): Non-Airdrop
```

#### 3.2.3. 통제 변수

| 변수 | 정의 | 출처 |
|-----|------|------|
| BTC_30d_return | T-30 ~ T0 BTC 누적 수익률 | CoinGecko |
| ETH_30d_return | T-30 ~ T0 ETH 누적 수익률 | CoinGecko |
| alt_season_dummy | CoinGecko alt season indicator | CoinGecko |
| circulating_at_listing | 상장 시 유통량 비중 | tokenomist.ai |
| FDV_at_listing | 상장 시 fully diluted valuation | CoinGecko |
| token_category | DeFi / L1 / Meme / Infra / RWA | CoinGecko categories |
| listing_quarter | Q1/Q2/Q3/Q4 더미 | 자체 분류 |

#### 3.2.4. 회귀 모델 (Tier 3 검정)

```
CAR_i,30 = α 
         + β1·distribution_ratio_i
         + β2·BTC_30d_return_i
         + β3·ETH_30d_return_i
         + β4·alt_season_dummy_i
         + β5·log(circulating_at_listing_i)
         + β6·log(FDV_at_listing_i)
         + γ·token_category_i
         + δ·listing_quarter_i
         + ε_i
```

- 추정: OLS with robust SE (Eicker-Huber-White)
- 다중공선성 검정: VIF ≤ 10
- 이분산성 검정: Breusch-Pagan
- Bonferroni 교정 (다중 가설 검정)

#### 3.2.5. Matched-Pair Comparison (보조 분석)

Megadrop 토큰 vs HODLer 토큰을 다음 기준으로 매칭:
- 같은 분기 상장
- 같은 토큰 카테고리 (DeFi / L1 / Infra 등)
- 유사한 FDV (±50% 이내)

매칭된 쌍의 30일 BTC-relative return 차이의 평균 검정 (Wilcoxon signed-rank test).

### 3.3. 시장 사이클 통제 설계

본 연구의 *학술적 핵심*은 시장 환경 효과를 분리하는 것이다. 다음 3가지 접근을 병용한다:

#### 접근 A: BTC-relative abnormal return
- 모든 가격 변동을 BTC 대비 표현
- 시장 전체 효과를 자동 차감

#### 접근 B: 회귀 통제 변수
- BTC_30d_return, ETH_30d_return, alt_season_dummy
- 상장 시점의 시장 환경을 명시적 통제

#### 접근 C: 자연 실험 설계 (가장 강력)
- 2025 Q3 강세장 (ETH +68.5%, BNB +57.3%)에 상장된 Megadrop 토큰 vs 약세장 상장 토큰 비교
- 만약 Megadrop 토큰이 강세장에서도 BTC를 underperform 한다면, 이는 시장 사이클로 설명되지 않는 본질적 매도 압력의 증거

### 3.4. 검증된 예비 데이터 (Pilot Sample)

본 IdeaNote 작성 시점(2026-05-01)까지 1차 출처 검증을 통과한 사례:

| 토큰 | 카테고리 | 분배 비율 | 24h 수익 | 90일 수익 (잠정) | 출처 |
|------|--------|---------|---------|-------------|------|
| BounceBit (BB) | Megadrop | 8.00% | (확인 필요) | 큰 폭 하락 | tokenomist |
| Solv (SOLV) | Megadrop | 7.00% | (확인 필요) | -15.5% 주간 (2026-04) | Binance, CoinGecko |
| Lista (LISTA) | Megadrop | 5-8% | (확인 필요) | 변동 | Binance, CoinGecko |
| Bubblemaps (BMT) | HODLer | 3.00% | (확인 필요) | (확인 필요) | Binance |
| APRO (AT) | HODLer | 2.00% | (확인 필요) | (확인 필요) | Binance |
| Spark (SPK) | HODLer | 2.00% | **-54% (24h)**, **-70%+ 최종** | (확인 필요) | BeInCrypto, CryptoTimes, Coinspeaker |

**예비 관찰**:
- HODLer 2% 분배에서도 SPK 같이 -70% 가능 → 분배 비율만이 유일 변수가 아님
- Megadrop 카테고리 전체 시가총액 $46.4M (2026-04, CoinGecko) → 카테고리 차원 시그널

이 예비 사례는 N=6 으로 통계적 결론에 부족하다. 본격 연구는 *N≥100* 표본을 목표로 한다.

---

## 4. 시각적 가설 — 자기잠식 루프와 그 부분 수정

### 4.1. 원래 가설 (DeepSeek 다이어그램)

자매 칼럼(2026-05-01)에서 시각화된 가설:

```
1. BNB 홀더 혜택 강화 목표
   ↓
2. 에어드롭 물량 대량 배포 (전체 공급량 5% 이상)
   ↓
3. 상장 코인: 매도 압력 극대화
   ↓
4. 상장 코인 가격 하락
   ↓
5. 프로젝트 가치 하락
   ↓
6. BNB 체인 생태계 가치 감소
   ↓
7. BNB 홀더 실질적 혜택 감소
   ↓ (1로 복귀)
```

### 4.2. 데이터로 부분 수정된 가설

자매 칼럼의 7장에서 검증된 결과로 단계 6 이 수정됨:

**검증된 부분 (단계 1-5, 7)**:
- 단계 1-3: Megadrop 5-8% 분배 → 매도 압력
- 단계 4: 88.9% 손실, 평균 -44%, SPK -70%
- 단계 5: Megadrop 카테고리 시총 $46.4M
- 단계 7: 즉시 매도 시 +177% 확정 → Nash equilibrium

**부분 부정 부분 (단계 6)**:
- BNB 체인 자체는 *위축이 아닌 확장 단계*
- Q2 거래량 +101.9%, 활성 지갑 +33.2%, TVL +14.0%
- Q3 거래량 +35.3%, TVL +30.7%, BNB 가격 +53.5%
- 다른 동력(Binance Alpha, PancakeSwap, Aster) 이 BNB 체인 견인

**수정된 가설**: *부분 자기잠식 루프*. 신규 토큰 영역에서는 매도 압력 → 가격 하락 패턴이 작동하나, BNB 체인 거시는 신규 토큰 부진과 디커플링되어 다른 채널로 성장. 이는 H4 (Tier 4 가설) 의 검증 대상이 된다.

### 4.3. 학술적 정직성

이 부분 수정은 본 연구의 *반증 가능성* 을 보여준다:

- 만약 모든 가설이 무비판적으로 옹호된다면, 그것은 *옹호*이지 *연구*가 아니다
- 검증 데이터가 가설을 부분 부정하면 그것을 명시하는 것이 학술 연구의 본질
- 본 가설의 *부분 부정* 자체가 새로운 발견 (디커플링 가설)

---

## 5. Phase 1-4 와의 관계

### 5.1. 데이터 환경 일치성

| Phase | 주제 | 데이터 환경 | 유닛 | 시간 창 |
|-------|------|----------|------|--------|
| 1 (SSRN 6632838) | 72시간 쇼크 | Binance 토큰 | 언락 이벤트 | ±72시간 |
| 2 (계획) | N=200 확장 | Binance + 추가 거래소 | 언락 이벤트 | ±72시간 |
| 3 (계획) | 공시 타이밍 | Binance + 아시아 시장 | 공시 이벤트 | T-30 ~ T+14 |
| 4 (계획) | 체인 비교 | 다중 체인 | 언락 이벤트 | ±72시간 |
| **5 (본 IdeaNote)** | **분배 비대칭** | **Binance** | **상장 이벤트** | **T-30 ~ T+180** |

### 5.2. 방법론 일치성

본 연구는 Phase 1 의 *BTC-relative abnormal return* 방법론을 직접 계승한다:

- 동일 회귀 프레임워크
- 동일 베타 추정 방법
- 동일 Bonferroni 다중 검정 교정
- 동일 ±N 시간 창 분석 (Phase 1: 72시간, Phase 5: 30/90/180일)

이 방법론적 일치성은:
- 결과의 비교 가능성을 보장
- 연구 시리즈의 학술적 결합도를 강화
- 후속 연구자가 본 연구를 재현/확장하기 쉽게 함

### 5.3. SSRN 6632838 와의 보완성

| 차원 | 72시간 쇼크 (Phase 1) | 분배 비대칭 (Phase 5) |
|------|---------------------|---------------------|
| 유닛 | 언락 이벤트 | 상장 이벤트 |
| 시간 창 | ±72시간 (단기) | ±180일 (중장기) |
| 가격 충격 원인 | 토큰 공급 증가 | 0원 비용 보유자 매도 |
| 경제적 행위자 | 팀/투자자 (vesting cliff) | 에어드롭 수령자 (BNB 홀더) |
| 발견 가능 패턴 | 시간적 집중 (clustering) | 카테고리 차이 (Megadrop vs HODLer) |

두 연구는 *Binance 데이터 환경에서 토큰 공급의 두 가지 다른 충격을 다룬다*. 상호 보완적 증거.

---

## 6. 법적·윤리적 안전장치

### 6.1. 비난 회피 원칙

본 연구는 다음을 *주장하지 않는다*:

- Binance가 의도적으로 신규 토큰을 손해보게 한다는 주장
- BNB 홀더가 신규 토큰 매수자에게 *불공정* 이득을 본다는 주장
- 어떤 *법적*이거나 *규제*적 의견
- 특정 프로젝트 팀의 의도

본 연구는 다음을 *보고한다*:

- 공시된 분배 비율과 사후 가격의 상관관계
- 시장 사이클 통제 후의 잔여 효과
- 수령자의 합리적 매도 결정의 게임 이론적 균형

### 6.2. 데이터 출처의 공개성

- 모든 사용 데이터는 공개 (Binance 공식 공시, CoinGecko, CoinMarketCap, Messari)
- 비공개 정보, 내부 정보 일체 미사용
- 재현 가능한 데이터 파이프라인

### 6.3. 한국 법률 준수

- 외환거래법: 본 연구는 매매 권유 아님, 정보 제공
- 가상자산이용자보호법 (2024년 7월): 본 연구는 자문업 아님
- 자본시장법: 본 연구는 투자권유 아님

### 6.4. 사전 IRB 검토

- 인간 대상 연구 아님 (시장 데이터만 사용)
- 데이터 보호 GDPR 준수 (개인 식별 정보 무사용)
- 별도 IRB 불필요

---

## 7. 산출물

### 7.1. 학술 산출물

- **SSRN Working Paper**: *"Distribution Asymmetry: A Study of Centralized Exchange Airdrop Programs and Listed Token Returns"*
- 분량 목표: 25-30 페이지 (SSRN 6632838 와 유사)
- 언어: 영문 + 한국어 동시 게재

### 7.2. 공개 데이터

- N=100+ 표본 토큰 데이터셋 (CSV)
- 회귀 결과 테이블 (CSV)
- 시각화 (scatter plot, time-series)
- 재현 가능한 Python 스크립트

### 7.3. 자매 산출물

- **칼럼**: *"바이낸스 Megadrop과 HODLer Airdrop의 두 얼굴"* (2026-05-01 게재 예정)
- **GitHub**: vibe-investing 시리즈 통합 게재

### 7.4. 후속 연구 가능성

- Phase 6 후보: *Cross-Exchange Airdrop Comparison* (Bybit, Coinbase, OKX 의 유사 프로그램)
- Phase 7 후보: *Long-term Recovery Patterns* (T+1년, T+2년 가격 추이)
- Phase 8 후보: *KOL Network Amplification* (Phase 3 와 결합)

---

## 8. 실행 일정 (잠정)

2026년 5월 중 논문 완성.

---

## 9. 본 IdeaNote 의 한계

본 문서는 *완성된 연구 설계*가 아닌 *예비 연구 노트*이다. 다음 한계를 명시한다:

1. **표본 크기**: N=100+ 가능성을 전제했으나, 실제 데이터 가용성에 따라 변동 가능
2. **Non-Airdrop 통제군**: Binance 의 거의 모든 신규 상장이 어떤 형태의 인센티브 프로그램과 함께 진행되어, 순수 통제군 확보가 어려움. 짝지은 비교(matched-pair) 의존도가 높아짐
3. **시장 사이클 일반화**: 2024-2025년은 강세장. 약세장 데이터로의 외삽은 Phase 8 후보로 분리
4. **거래소 일반화**: 본 연구는 Binance 한정. Phase 6 후보로 다른 거래소로 확장 가능
5. **자기선택 편의 (self-selection bias)**: Megadrop 으로 선정된 프로젝트는 Binance 의 큐레이션을 통과한 것이며, 이는 무작위 표본이 아님. 결과 해석 시 주의 필요

---

## 10. 결론

본 IdeaNote 는 vibe-investing 연구 시리즈의 *Phase 5 후보* 를 정의한다. 핵심 기여는:

1. **새로운 유닛**: 거래소 에어드롭 프로그램의 분배 비율을 *정량적 변수*로 도입
2. **시장 사이클 통제**: BTC-relative abnormal return + 회귀 통제 + 자연 실험 설계로 시장 효과 분리
3. **Phase 1 와의 결합**: 동일 데이터 환경, 동일 방법론, 다른 유닛으로 토큰 공급 충격의 다차원 증거
4. **반증 가능성**: H4 가설 (BNB 체인 디커플링) 으로 자기잠식 루프 가설의 부분 부정 가능성 명시

본 연구의 *학술적 가치*는 — 거래소 에어드롭이라는 새로운 시장 메커니즘이 등장한 시기 (2020-2025) 에, 그 가격 영향을 *체계적으로 정량화한 첫 학술 연구* 가 될 가능성이다.

본 IdeaNote 는 실행 약속이 아니다. 실행 결정은 Phase 2 완료 후 Phase 1 (SSRN 6632838) 의 인용 데이터, 자매 칼럼의 시장 검증, 본 IdeaNote 의 외부 피드백을 종합하여 내린다.

---

## 작성 정보

**작성일**: 2026년 5월 1일
**저자**: 김호광 (Dennis Kim / HoKwang Kim) — Independent Researcher · Betalabs Inc. CEO
**시리즈**: vibe-investing 연구 시리즈 — Phase 5 후보
**ORCID**: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
**GitHub**: [vibe-investing](https://github.com/gameworkerkim/vibe-investing)
**SSRN Author**: [Author Page](https://ssrn.com/author=7497180)

**자매 산출물**:
- 칼럼: [Binance Megadrop·HODLer Airdrop 의 두 얼굴](https://github.com/gameworkerkim/vibe-investing) (2026-05-01)
- 학술 선행 연구: [SSRN 6632838 — The 72-Hour Shock](https://ssrn.com/abstract=6632838) (2026-04-25)
