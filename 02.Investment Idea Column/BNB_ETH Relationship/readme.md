# Directional Decoupling and the Volatility-Ratio Channel
## A Beta-Decomposition Framework for Exchange-Native Tokens

> Evidence from the BNB–ETH Relationship, 2022–2026

[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-0962-2175)
[![Working Paper](https://img.shields.io/badge/Status-Working_Paper_v9.2_(Final)-blue)](paper.pdf)
[![JEL](https://img.shields.io/badge/JEL-G12_G14_G15_C58-orange)](#)
[![Data](https://img.shields.io/badge/Data-CoinMetrics-green)](https://coinmetrics.io/)

🌐 **Languages**: [🇬🇧 English](#-english) · [🇰🇷 한국어](#-한국어) · [🇨🇳 中文](#-中文)

📌 **Quick links**: [Repository contents →](#-repository-contents) · [Citation →](#-citation) · [Author →](#-author) · [Contact →](#-contact)

---

## 🇬🇧 English

### Abstract

Standard cryptocurrency factor models treat $\beta$ as a sufficient statistic for systematic exposure. The identity $\beta = \rho \cdot (\sigma_i / \sigma_m)$ implies, however, that beta can change for two distinct reasons: a change in directional co-movement (correlation channel), or a change in relative volatility (volatility-ratio channel). The economic interpretations differ sharply, but the existing literature does not systematically separate them.

This paper proposes a **variance-decomposition framework** that isolates the two channels and applies it to a striking empirical pattern in BNB-ETH that we term *directional decoupling*: a beta decline accompanied by an unchanged correlation. Using daily price data from CoinMetrics covering May 2022 to April 2026 (n = 1,460 trading days), BNB's static beta to Ethereum (ETH) falls by 16.9% (from 0.643 to 0.534) while the Pearson correlation remains essentially unchanged ($0.731 \to 0.731$). **The decomposition reveals that 100% of the static beta change is attributable to a decline in the volatility ratio $\sigma_{BNB}/\sigma_{ETH}$, with no contribution from correlation change.** A further numerator/denominator decomposition shows that BNB-side volatility compression accounts for approximately 57% of the ratio decline, while ETH-side volatility expansion accounts for approximately 43%.

The April 2024 launch of the Binance HODLer Airdrops program serves as a natural **timing benchmark** partitioning our sample but is **not** the object of any causal claim.

### What We Studied: BNB and the Ethereum Relationship

BNB-ETH is a particularly informative case for studying beta-decomposition phenomena:

1. **Statistical power**: BNB and ETH have high contemporaneous correlation ($\rho \approx 0.73$ throughout the sample), providing the statistical power needed for fine-grained decomposition.
2. **Economic linkage**: BNB Chain (formerly BNB Smart Chain) competes directly with Ethereum, creating natural economic linkages that make beta-based factor exposure a meaningful object of study.
3. **Exchange-native scale**: BNB is the largest exchange-native token (Binance's utility/reward token), and ETH is the largest non-Bitcoin cryptocurrency, so the pair captures a substantial cross-section of the altcoin universe.
4. **Natural reference partition**: In April 2024, Binance launched its HODLer Airdrops program, which provides a natural pre/post boundary for the decomposition exercise (without serving as an object of causal-effect estimation).

### What We Found

| Result | Value | Interpretation |
|---|---|---|
| Static beta change | $0.643 \to 0.534$ ($-16.9\%$) | Substantial decline |
| Pearson correlation change | $0.731 \to 0.731$ | Essentially unchanged |
| Volatility ratio change | $0.879 \to 0.730$ | Sharp compression |
| **Correlation channel contribution** | **0.0%** of $\Delta\beta$ | No directional weakening |
| **Volatility-ratio channel contribution** | **100.0%** of $\Delta\beta$ | All beta change here |
| **BNB-side share of ratio change** | **57%** | BNB-specific compression |
| **ETH-side share of ratio change** | **43%** | ETH-side expansion |
| DCC-GARCH dynamic beta | $0.575 \to 0.541$ ($-5.84\%$, $p<0.001$) | Direction confirmed |
| Cross-sectional rank (16-pool) | 6 of 17 (35th pctile) | Moderate, not extreme |
| One-sample $t$-test vs.\ control mean | $t=-2.22$, $p=0.043$ | Cross-sectionally above-mean |
| Synthetic-counterfactual rank (main, 14-donor) | 4 of 15 ($p \approx 0.27$) | Moderate-to-strong |

**Key takeaway**: The directional decoupling pattern in BNB is real and somewhat stronger than the typical altcoin response, but is best understood as one instance of a broader altcoin volatility-ratio compression coinciding with ETH's volatility expansion in 2024 — *not* an asset-specific regime change. The HODLer Airdrops launch coincides with but did not appear to cause this pattern (Figure 1 shows the BNB beta trough occurred *before* the April 2024 launch).

**A direct test of one channel**: An event study of the spot Ethereum ETF approval (May 23, 2024) and trading launch (July 23, 2024) shows that ETF events do *not* drive the 43% ETH-side share — ETH volatility *fell* 42% in the 60 days after approval, then *rose* 70% in the 60 days after trading launch, with the net effect approximately zero (Appendix B). The ETH-side expansion must therefore reflect other channels (macroeconomic factors, post-Shanghai staking dynamics) over the full post-partition window.

### Why It Matters

1. **Beta is not a sufficient statistic for systematic exposure.** Cryptocurrency factor models (Liu & Tsyvinski 2021, Liu et al. 2024) routinely use beta as their primary measure. Our results show that for exchange-native and altcoin assets, beta movements may misrepresent the underlying co-movement structure: an apparent "decoupling" can reflect volatility compression rather than weakening factor exposure.
2. **The framework is general.** The decomposition $\beta = \rho \cdot (\sigma_i/\sigma_m)$ and the further numerator/denominator split apply to any asset-benchmark pair. Researchers studying any beta change in any asset class can apply this decomposition.
3. **Methodological caution for cross-sectional inference.** Our results illustrate that synthetic-counterfactual conclusions can reverse depending on donor-pool composition (Section 4.8 and Appendix C); we provide a worked example of how economic comparability of donors should take precedence over statistical fit when the treated unit is unique within the cross-section.

### Future Research

This paper is **deliberately scoped as documentation and decomposition, not causal inference**. The follow-up agenda — a planned subsequent paper — comprises:

1. **On-chain stablecoin flow analysis**: Glassnode/Nansen data on USDT/USDC/FDUSD movements into BNB-paired liquidity pools during ETH stress events, to discriminate active-intervention vs. passive-supply hypotheses.
2. **Staggered-treatment design**: OKX (OKB), Crypto.com (CRO), KuCoin (KCS), Bitget (BGB) holder-reward launch dates with Callaway & Sant'Anna (2021) staggered-treatment DiD to identify program-specific channel effects.
3. **Dose-response analysis**: HODLer airdrop monthly intensity (count + notional) as time-varying treatment intensity, regressed on rolling-window beta and volatility-ratio components.
4. **ETH-side decomposition with broader event set**: Beyond the spot ETH ETF events tested in Appendix B (which yielded a null result), event-study designs around FOMC decisions, dollar-strength inflection points, post-Shanghai staking-ratio regimes, and macroeconomic factors to attribute the 43% ETH-side share to specific channels.
5. **Category-level beta heterogeneity**: Investigation of why DeFi/oracle tokens (UNI, LINK) on average exhibited beta *increase* rather than decline — potentially reflecting cash-flow linkage to ETH ecosystem activity (gas fees, staking yields, DeFi TVL).
6. **Volatility-channel-aware factor models**: Augmenting standard one- and three-factor crypto factor models with explicit volatility-ratio components.

### Version History (newest first)

The paper went through nine major revision rounds. Each row summarizes the headline change and the reviewer concern that motivated it. Two of these rounds were *strategic turning points* that fundamentally restructured the paper; they are flagged with ⭐ and discussed in the **Research Trajectory** subsection that follows.

| Version | Major change | Motivation |
|---|---|---|
| **v9.2 (Final)** | Added ETH ETF event-study Appendix B (null result, transparently reported); removed trend-transition Appendix; updated author bio | Direct test of whether ETF events drive the 43% ETH-side share; paper focus and selective-reporting concerns |
| v9.1 | Synthetic-counterfactual main spec switched to 14-donor (TRX/XRP excluded); 16-donor demoted to sensitivity. Three-test reconciliation (Chow / $t$-test / synthetic) added in Section 5.2 with explicit power and assumption discussion. DCC vs.\ static beta divergence discussed in Section 4.5 | Donor-pool economic comparability is a precondition for synthetic-control validity; reviewer-style honest treatment of conflicting test results |
| **v9.0** ⭐ | **STRATEGIC REPOSITIONING from causal-effect paper to methodology paper.** New title ("Directional Decoupling and the Volatility-Ratio Channel: A Beta-Decomposition Framework"); HODLer Airdrops removed from title and demoted to "timing benchmark"; Section 4.1 made Variance Decomposition (was 4.8); "Identification" → "Cross-sectional specificity"; "treatment date" → "reference partition date" throughout | Sidestep the unwinnable identification debate by reframing contribution as methodological framework + empirical decomposition; matches the actual strength of the analytical contribution |
| v8.0 | Numerator/denominator decomposition added (Table 6: BNB-side 57% / ETH-side 43%); trend transition demoted to Appendix only; Future Work strengthened as "planned follow-up paper" | Quick-win analytical extension on existing data; mathematical decomposition that separates BNB-specific from ETH-side mechanisms |
| v7.0 | $t$-statistic sign corrected ($+2.21 \to -2.22$) with explicit framing; TRX/XRP synthetic-counterfactual sensitivity check added in Appendix C; HT-inclusion robustness expanded; DeFi within-category heterogeneity strengthened in Section 4.7 | Reviewer caught the sign convention; donor pool concerns formalized as robustness; honest reporting of within-category variance |
| v6.0 | HT (Huobi Token) excluded from main control pool due to HTX exchange-standing decline; statistical inference added (one-sample $t$-test, Wilcoxon, empirical-rank); Figure 1 (rolling beta visualization) added | Contaminated control issue; reviewers wanted formal inference, not just rank statistics; visual evidence requested |
| **v5.0** ⭐ | **EMPIRICAL EXPANSION**: control pool expanded from 7 exchange-token-only to 17 diverse altcoins across four categories (exchange tokens, L1 platforms, DeFi/oracle, other altcoins). Reveals DeFi *recoupling* ($+0.025$) — opposite direction from exchange tokens | Reviewer concern that 7-token exchange-only pool was too narrow; broader pool revealed cross-category heterogeneity that reframed the entire interpretation |
| v4.0 | Variance decomposition added (Table 5: 100% volatility-ratio channel, 0% correlation channel); concept of "directional decoupling" introduced | Reviewer asked why beta declined while correlation was unchanged; mathematical decomposition isolated the channel exactly |
| v1.0–v3.0 | Initial causal-effect study: BNB beta to ETH falls 16.9% post-April-2024; Chow test rejects structural stability; HODLer Airdrops as treatment | Initial framing as a treatment-effect study of the HODLer Airdrops program |

### Research Trajectory: Two Turning Points

The paper's research trajectory was reshaped by two strategic turning points that fundamentally changed what the paper claims:

**⭐ Turning Point 1 — v5.0 (Empirical expansion of the control pool):** The control pool was expanded from 7 exchange-token-only to 17 diverse altcoins spanning four categories. This expansion revealed a result that the original 7-token pool could not show: while exchange tokens, Layer-1 platforms, and other altcoins decoupled from ETH on average, **DeFi and oracle tokens *recoupled*** (mean $\Delta\beta = +0.025$, driven primarily by UNI and LINK). BNB's rank in the broader pool was 6 of 17 — moderate, not extreme. This finding made the original "HODLer Airdrops caused BNB-specific decoupling" story untenable: the data instead pointed to a market-wide reordering with substantial cross-category heterogeneity. The paper had to start narrating a more honest interpretation, leading directly to v6–v8 refinements.

**⭐ Turning Point 2 — v9.0 (Methodology repositioning):** By v8, the paper had accumulated strong empirical content (variance decomposition with 100% volatility-ratio attribution, 57/43 numerator/denominator split, full cross-sectional analysis), but its identification strategy for any HODLer-program-specific causal effect remained weak. Reviewer attacks on identification were essentially unwinnable with available data. The strategic decision in v9.0 was to **stop claiming causation altogether and reposition the paper around its actual strongest contribution — the variance-decomposition framework**. The title was changed to lead with the methodological idea, the Variance Decomposition section was moved to 4.1 as the first empirical result, all causal language ("treatment", "identification") was replaced with neutral terminology ("reference partition", "cross-sectional specificity"), and the introduction began with the gap in cryptocurrency factor models (Liu & Tsyvinski 2021, 2024) rather than with HODLer Airdrops. This pivot took the paper from a vulnerable causal-effect study to a defensible methodology paper with applicability beyond BNB.

### Research Question Evolution

| Phase | Versions | Central question | Status |
|---|---|---|---|
| Causal-effect study | v1–v3 | Did the HODLer Airdrops program cause BNB to decouple from ETH? | Identification proved untenable |
| Decomposition study | v4–v5 | If beta fell while correlation was unchanged, *where* in the joint distribution did the change occur? | Framework crystallized; cross-sectional context revealed broader pattern |
| Refinement | v6–v8 | How robust is the empirical pattern, and how does BNB compare cross-sectionally? | All robustness checks survived; numerator/denominator decomposition added |
| Methodology paper | v9.0–v9.2 | What does the variance-decomposition framework reveal about beta dynamics in cryptocurrency markets, with BNB-ETH as the illustrative case? | **Current scope** — defensible, generalizable, reviewer-friendly |

[Continue to repository contents →](#-repository-contents) · [Citation →](#-citation) · [Author →](#-author)

---

## 🇰🇷 한국어

### 초록

표준 암호화폐 요인 모형은 $\beta$를 시스템적 위험 노출의 충분 통계량(sufficient statistic)으로 사용한다. 그러나 항등식 $\beta = \rho \cdot (\sigma_i / \sigma_m)$은 베타가 두 가지 다른 이유로 변할 수 있음을 의미한다: 방향적 동조성 변화(상관관계 채널), 또는 상대 변동성 변화(변동성 비율 채널). 두 경제적 해석은 매우 다르지만, 기존 문헌은 이를 체계적으로 분리하지 않는다.

본 논문은 두 채널을 분리하는 **분산 분해 프레임워크**를 제안하고, 이를 BNB-ETH의 흥미로운 실증 패턴에 적용한다. 이 패턴을 우리는 *directional decoupling* (방향성 디커플링)으로 명명한다: 상관관계는 변하지 않으면서 베타만 하락하는 현상. CoinMetrics의 2022년 5월~2026년 4월 일별 데이터(n=1,460)를 사용하여, BNB의 ETH 대비 정적 베타가 16.9% 하락(0.643→0.534)했음에도 Pearson 상관계수는 사실상 변화 없음(0.731→0.731)을 문서화한다. **분해 결과 정적 베타 변화의 100%가 변동성 비율 $\sigma_{BNB}/\sigma_{ETH}$ 하락에서 비롯되며, 상관관계 변화의 기여는 0%이다.** 추가 분자/분모 분해 결과 BNB 측 변동성 압축이 비율 하락의 약 57%, ETH 측 변동성 확대가 약 43%를 차지한다.

2024년 4월 Binance HODLer Airdrops 프로그램 출시는 표본을 분할하는 자연스러운 **시점 기준점(timing benchmark)**으로 사용되지만, **인과적 효과 주장의 대상은 아니다**.

### 무엇을 연구했나: BNB와 이더리움의 관계

BNB-ETH는 베타 분해 현상 연구에 특히 유익한 사례이다:

1. **통계적 검정력**: BNB와 ETH의 동시점 상관계수가 표본 전체에서 $\rho \approx 0.73$로 높아, 정밀한 분해에 필요한 통계적 검정력 확보.
2. **경제적 연계성**: BNB Chain(구 BNB Smart Chain)이 이더리움과 직접 경쟁하므로, 베타 기반 요인 노출이 의미 있는 연구 대상.
3. **거래소 토큰 대표성**: BNB는 최대 거래소 네이티브 토큰(Binance의 유틸리티/보상 토큰), ETH는 비트코인 외 최대 암호화폐로, 알트코인 우주의 상당 부분을 포착.
4. **자연스러운 분할 시점**: 2024년 4월 Binance HODLer Airdrops 출시가 분해 분석을 위한 자연스러운 사전/사후 경계 제공 (인과 효과 추정의 대상은 아님).

### 어떤 결과를 얻었나

| 결과 | 값 | 해석 |
|---|---|---|
| 정적 베타 변화 | $0.643 \to 0.534$ ($-16.9\%$) | 상당한 하락 |
| Pearson 상관계수 변화 | $0.731 \to 0.731$ | 사실상 변화 없음 |
| 변동성 비율 변화 | $0.879 \to 0.730$ | 큰 압축 |
| **상관관계 채널 기여** | **0.0%** of $\Delta\beta$ | 방향적 약화 없음 |
| **변동성 비율 채널 기여** | **100.0%** of $\Delta\beta$ | 모든 베타 변화가 여기서 |
| **BNB 측 비율 변화 기여** | **57%** | BNB 고유 압축 |
| **ETH 측 비율 변화 기여** | **43%** | ETH 측 확대 |
| DCC-GARCH 동적 베타 | $0.575 \to 0.541$ ($-5.84\%$, $p<0.001$) | 방향 일치 |
| 16개 풀 내 횡단면 순위 | 6/17 (35분위) | 중간, 극단 아님 |
| One-sample $t$-test vs. 평균 | $t=-2.22$, $p=0.043$ | 횡단면 평균 대비 의미 있게 큼 |
| 합성대조군 순위 (main, 14-donor) | 4/15 ($p \approx 0.27$) | 중간-강한 수준 |

**핵심 시사점**: BNB의 directional decoupling 패턴은 실재하며 평균적 알트코인 반응보다 약간 강하지만, **자산 고유 체제 변화가 아니라** 2024년 ETH 변동성 확대와 맞물린 광범위한 알트코인 변동성 비율 압축의 한 사례로 가장 잘 이해된다. HODLer Airdrops 출시는 시점이 일치할 뿐 인과 원인은 아닌 것으로 보인다 (Figure 1: BNB 베타 저점은 2024년 4월 출시 *이전* 발생).

**한 채널의 직접 검증**: spot Ethereum ETF 승인일(2024-05-23)과 거래 개시일(2024-07-23)에 대한 이벤트 스터디(Appendix B)는 ETF 사건이 ETH 측 43% 기여를 *주도하지 않음*을 보인다. 승인 후 60일 동안 ETH 변동성은 *42% 하락*, 거래 개시 후 60일 동안 *70% 상승*, 순효과는 거의 영(zero). ETH 측 확대는 다른 채널(매크로 요인, post-Shanghai 스테이킹 동학)에 기인.

### 왜 중요한가

1. **베타는 시스템적 위험 노출의 충분 통계량이 아니다.** 암호화폐 요인 모형(Liu & Tsyvinski 2021, Liu et al. 2024)은 베타를 주요 측정치로 사용한다. 본 연구는 거래소 토큰과 알트코인의 경우 베타 변화가 기저 동조성 구조를 잘못 표현할 수 있음을 보인다: 외견상 "디커플링"이 요인 노출 약화가 아니라 변동성 압축을 반영할 수 있다.
2. **프레임워크의 일반성.** 분해 $\beta = \rho \cdot (\sigma_i/\sigma_m)$와 추가 분자/분모 분해는 모든 자산-벤치마크 쌍에 적용된다. 다른 자산 클래스에서 베타 변화를 연구하는 모든 연구자가 이 분해를 적용할 수 있다.
3. **횡단면 추론의 방법론적 주의.** 합성대조군 결론이 donor pool 구성에 따라 뒤집힐 수 있음을 보인다 (Section 4.8 및 부록 C). 처치 단위가 횡단면에서 unique할 때 통계적 적합도보다 donor의 경제적 유사성이 우선되어야 함을 작업 예시로 제공.

### 향후 연구 방향

본 논문은 **의도적으로 문서화 및 분해로 범위를 제한**하며 인과 추론은 시도하지 않는다. 후속 연구 의제 — 계획된 다음 논문 — 는 다음과 같다:

1. **온체인 스테이블코인 흐름 분석**: ETH 스트레스 이벤트 동안 BNB 페어 유동성 풀로의 USDT/USDC/FDUSD 이동에 대한 Glassnode/Nansen 데이터를 활용하여 능동적 개입 가설 vs. 수동적 공급 가설 판별.
2. **Staggered-treatment 설계**: OKX(OKB), Crypto.com(CRO), KuCoin(KCS), Bitget(BGB)의 holder reward 출시일을 활용한 Callaway & Sant'Anna(2021)의 staggered DiD로 프로그램 특정 채널 효과 식별.
3. **Dose-response 분석**: HODLer airdrop의 월별 강도(횟수 + notional)를 시변 처치 강도로 사용하여 rolling 베타 및 변동성 비율 성분에 회귀.
4. **확장된 이벤트 셋 ETH 측 분해**: 부록 B에서 검증한 ETH ETF 사건(null 결과)을 넘어, FOMC 결정, 달러 강세 변곡점, post-Shanghai 스테이킹 비율 체제, 매크로경제 요인 등의 이벤트 스터디로 ETH 측 43% 기여를 특정 채널에 귀속.
5. **카테고리별 베타 이질성**: DeFi/오라클 토큰(UNI, LINK)이 평균적으로 베타 *증가*를 보인 이유 — ETH 생태계 활동(가스비, 스테이킹 수익, DeFi TVL)과의 현금흐름 연계 가능성 — 조사.
6. **변동성 채널 인지 요인 모형**: 표준 1요인 또는 3요인 암호화폐 요인 모형을 명시적 변동성 비율 성분으로 확장.

### 버전 히스토리 (최신 버전부터)

본 논문은 9차례의 주요 개정을 거쳤다. 각 행은 헤드라인 변경 사항과 그 변경을 동기 부여한 reviewer 우려를 요약한다. 그 중 두 차례는 논문의 골격을 근본적으로 재구성한 *전략적 터닝 포인트*로, ⭐로 표시되었으며 다음 **연구 흐름** 섹션에서 자세히 다룬다.

| 버전 | 주요 변경 | 동기 |
|---|---|---|
| **v9.2 (Final)** | ETH ETF 이벤트 스터디 부록 B 추가 (null 결과를 정직히 보고); 추세 전환 부록 제거; 저자 소개 갱신 | ETF 사건이 ETH 측 43% 기여를 주도하는지에 대한 직접 검증; 논문 집중도 + 선택적 보고 우려 |
| v9.1 | 합성대조군 main spec을 14-donor (TRX/XRP 제외)로 변경, 16-donor를 sensitivity로 강등. Section 5.2에 세 검정 reconciliation (Chow / $t$-test / synthetic) + 검정력·가정 비교 추가. Section 4.5에 DCC vs.\ 정적 베타 차이 논의 추가 | Donor pool의 경제적 유사성은 합성대조군 타당성의 전제 조건; 충돌하는 검정 결과를 정직히 다룬 reviewer 친화적 처리 |
| **v9.0** ⭐ | **인과 효과 paper에서 방법론 paper로 전략적 재포지셔닝.** 새 제목 ("Directional Decoupling and the Volatility-Ratio Channel: A Beta-Decomposition Framework"); HODLer Airdrops를 제목에서 제거하고 "timing benchmark"로 강등; Variance Decomposition을 4.1로 (이전 4.8); "Identification" → "Cross-sectional specificity"; "treatment date" → "reference partition date" 일괄 변경 | 가용 데이터로는 이길 수 없는 인과 식별 논쟁을 우회하기 위해, 분석적 기여의 실제 강점인 방법론적 프레임워크 + 실증적 분해로 재구성 |
| v8.0 | 분자/분모 분해 추가 (Table 6: BNB 측 57% / ETH 측 43%); 추세 전환을 부록으로만 강등; Future Work를 "계획된 후속 논문"으로 강화 | 기존 데이터를 활용한 빠른 분석 확장; BNB 고유 메커니즘과 ETH 측 메커니즘을 분리하는 수학적 분해 |
| v7.0 | $t$-통계량 부호 정정 ($+2.21 \to -2.22$) + 명시적 해석; TRX/XRP 합성대조군 sensitivity check를 부록 C에 추가; HT 포함 robustness 확장; Section 4.7에 DeFi 카테고리 내 이질성 강화 | Reviewer가 부호 관행 지적; donor pool 우려를 robustness로 형식화; 카테고리 내 분산을 정직히 보고 |
| v6.0 | HTX 거래소 위상 하락으로 인한 HT (Huobi Token)를 main control pool에서 제외; 통계적 추론 추가 (one-sample $t$-test, Wilcoxon, empirical-rank); Figure 1 (rolling beta 시각화) 추가 | 오염된 통제군 문제; reviewer가 rank 통계가 아닌 정식 추론 요구; 시각적 증거 요청 |
| **v5.0** ⭐ | **실증적 확장**: control pool을 7개 거래소 토큰에서 4개 카테고리 (거래소 토큰, L1 플랫폼, DeFi/오라클, 기타 알트코인) 17개 다양한 알트코인으로 확장. DeFi *재커플링* ($+0.025$) 발견 — 거래소 토큰과 반대 방향 | 7개 거래소 전용 풀이 너무 좁다는 reviewer 우려; 더 넓은 풀이 카테고리 간 이질성을 드러내어 전체 해석을 재구성 |
| v4.0 | 분산 분해 추가 (Table 5: 변동성 비율 채널 100%, 상관관계 채널 0%); "directional decoupling" 개념 도입 | Reviewer가 상관관계 불변시 베타가 왜 떨어졌는지 질문; 수학적 분해가 채널을 정확히 분리 |
| v1.0–v3.0 | 초기 인과 효과 연구: BNB의 ETH 대비 베타가 2024년 4월 이후 16.9% 하락; Chow test가 구조적 안정성 기각; HODLer Airdrops를 처치로 | HODLer Airdrops 프로그램의 처치 효과 연구로 초기 구성 |

### 연구 흐름: 두 차례의 터닝 포인트

본 논문의 연구 흐름은 두 차례의 전략적 터닝 포인트에 의해 근본적으로 재구성되었다. 각각이 논문이 무엇을 주장하는지를 변경시켰다:

**⭐ 터닝 포인트 1 — v5.0 (통제군 풀의 실증적 확장):** 통제군 풀이 7개 거래소 전용 토큰에서 4개 카테고리에 걸친 17개 다양한 알트코인으로 확장되었다. 이 확장으로 원래 7-token 풀이 보여줄 수 없었던 결과가 드러났다: 거래소 토큰, Layer-1 플랫폼, 기타 알트코인은 평균적으로 ETH로부터 디커플링했지만, **DeFi 및 오라클 토큰은 *재커플링*했다** (평균 $\Delta\beta = +0.025$, 주로 UNI와 LINK에 의해 주도됨). BNB의 더 넓은 풀 내 순위는 17 중 6위 — 중간이지 극단이 아니었다. 이 발견은 원래의 "HODLer Airdrops가 BNB 고유 디커플링을 야기" 이야기를 유지할 수 없게 만들었다: 데이터는 대신 카테고리 간 상당한 이질성을 동반한 시장 전체적 재정렬을 가리켰다. 논문은 더 정직한 해석을 서술하기 시작했고, 이는 직접적으로 v6–v8 개선으로 이어졌다.

**⭐ 터닝 포인트 2 — v9.0 (방법론 재포지셔닝):** v8까지 논문은 강력한 실증 내용 (변동성 비율 채널 100% 분해, 57/43 분자/분모 분할, 전체 횡단면 분석)을 축적했지만, HODLer 프로그램 특정 인과 효과에 대한 식별 전략은 여전히 약했다. 가용 데이터로는 reviewer의 식별 공격이 본질적으로 이길 수 없었다. v9.0의 전략적 결정은 **인과를 주장하지 않고 논문을 실제 가장 강력한 기여인 분산 분해 프레임워크 중심으로 재포지셔닝하는 것**이었다. 제목을 방법론적 아이디어로 시작하도록 변경하고, Variance Decomposition 섹션을 4.1로 옮겨 첫 번째 실증 결과로 삼았으며, 모든 인과 언어 ("treatment", "identification")를 중립 용어 ("reference partition", "cross-sectional specificity")로 교체하고, 도입부를 HODLer Airdrops가 아닌 암호화폐 요인 모형의 gap (Liu & Tsyvinski 2021, 2024)으로 시작하게 했다. 이 전환은 논문을 취약한 인과 효과 연구에서 BNB를 넘어선 적용성을 가진 방어 가능한 방법론 paper로 격상시켰다.

### 연구 질문의 진화

| 단계 | 버전 | 중심 질문 | 상태 |
|---|---|---|---|
| 인과 효과 연구 | v1–v3 | HODLer Airdrops 프로그램이 BNB가 ETH로부터 디커플링하게 만들었는가? | 식별이 유지 불가능함이 증명됨 |
| 분해 연구 | v4–v5 | 베타가 하락했지만 상관관계가 변하지 않았다면, 결합 분포의 *어디*에서 변화가 발생했는가? | 프레임워크가 결정화됨; 횡단면 맥락이 더 광범위한 패턴을 드러냄 |
| 정제 | v6–v8 | 실증 패턴은 얼마나 robust하며, BNB는 횡단면적으로 어떻게 비교되는가? | 모든 robustness 검정 통과; 분자/분모 분해 추가 |
| 방법론 paper | v9.0–v9.2 | 분산 분해 프레임워크가 암호화폐 시장의 베타 동학에 대해 무엇을 드러내는가, BNB-ETH를 illustrative case로 사용하여? | **현재 범위** — 방어 가능, 일반화 가능, reviewer 친화적 |

[Repository 내용 →](#-repository-contents) · [인용 →](#-citation) · [저자 →](#-author)

---

## 🇨🇳 中文

### 摘要

标准加密货币因子模型将 $\beta$ 视为系统性风险敞口的充分统计量。然而恒等式 $\beta = \rho \cdot (\sigma_i / \sigma_m)$ 意味着 Beta 可能由两个不同的原因变化: 方向性共动性变化 (相关性渠道) 或相对波动率变化 (波动率比率渠道)。两种经济学解释截然不同, 但现有文献并未系统地区分它们。

本文提出**方差分解框架**, 分离两个渠道, 并应用于 BNB-ETH 中的一个引人注目的实证模式, 我们将其命名为 *方向性脱钩 (directional decoupling)*: Beta 下降而相关性保持不变。使用 CoinMetrics 提供的 2022 年 5 月至 2026 年 4 月日度数据 (n=1,460), 我们记录: BNB 对 ETH 的静态 Beta 下降 16.9% (从 0.643 至 0.534), 而 Pearson 相关系数基本不变 (0.731 → 0.731)。**分解显示静态 Beta 变化的 100% 来自波动率比率 $\sigma_{BNB}/\sigma_{ETH}$ 的下降, 相关性变化的贡献为 0%。** 进一步的分子/分母分解表明 BNB 端波动率压缩约占比率下降的 57%, ETH 端波动率扩大约占 43%。

2024 年 4 月币安 HODLer Airdrops 计划启动用作分割样本的自然 **时间基准点 (timing benchmark)**, 但 **不是任何因果主张的对象**。

### 我们研究了什么: BNB 与以太坊关系

BNB-ETH 是研究 Beta 分解现象特别有用的案例:

1. **统计功效**: BNB 和 ETH 在整个样本中的同期相关系数高达 $\rho \approx 0.73$, 提供精细分解所需的统计功效。
2. **经济联系**: BNB 链 (前称 BNB Smart Chain) 与以太坊直接竞争, 创造自然的经济联系, 使基于 Beta 的因子敞口成为有意义的研究对象。
3. **交易所代币代表性**: BNB 是最大的交易所原生代币 (币安的实用/奖励代币), ETH 是除比特币外最大的加密货币, 该对捕捉了山寨币世界的大部分。
4. **自然分割时点**: 2024 年 4 月币安 HODLer Airdrops 启动为分解分析提供自然的事前/事后边界 (但不是因果效应估计对象)。

### 我们获得了什么结果

| 结果 | 值 | 解读 |
|---|---|---|
| 静态 Beta 变化 | $0.643 \to 0.534$ ($-16.9\%$) | 实质性下降 |
| Pearson 相关系数变化 | $0.731 \to 0.731$ | 基本不变 |
| 波动率比率变化 | $0.879 \to 0.730$ | 显著压缩 |
| **相关性渠道贡献** | **0.0%** of $\Delta\beta$ | 无方向性减弱 |
| **波动率比率渠道贡献** | **100.0%** of $\Delta\beta$ | 全部 Beta 变化在此 |
| **BNB 端比率变化贡献** | **57%** | BNB 特定压缩 |
| **ETH 端比率变化贡献** | **43%** | ETH 端扩大 |
| DCC-GARCH 动态 Beta | $0.575 \to 0.541$ ($-5.84\%$, $p<0.001$) | 方向一致 |
| 16-池中横截面排名 | 6/17 (第 35 百分位) | 中等, 非极端 |
| 单样本 $t$-检验 vs. 均值 | $t=-2.22$, $p=0.043$ | 横截面有意义高于均值 |
| 合成对照排名 (main, 14-donor) | 4/15 ($p \approx 0.27$) | 中等偏强 |

**核心启示**: BNB 中的方向性脱钩模式真实存在, 略强于典型山寨币反应, 但最佳理解为 **不是资产特定的体制变化**, 而是与 2024 年 ETH 波动率扩大相伴的更广泛山寨币波动率比率压缩的一个实例。HODLer Airdrops 启动只是时间巧合, 似乎不是因果原因 (图 1: BNB Beta 谷底发生在 2024 年 4 月启动 *之前*)。

**一个渠道的直接检验**: 现货以太坊 ETF 批准 (2024-05-23) 和交易启动 (2024-07-23) 的事件研究 (附录 B) 显示 ETF 事件 *不* 驱动 ETH 端 43% 贡献份额——批准后 60 天 ETH 波动率 *下降 42%*, 交易启动后 60 天 *上升 70%*, 净效应近零。ETH 端扩大必须归因于其他渠道 (宏观经济因素、post-Shanghai 质押动态)。

### 为什么重要

1. **Beta 不是系统性风险敞口的充分统计量。** 加密货币因子模型 (Liu & Tsyvinski 2021, Liu et al. 2024) 例行将 Beta 用作主要测度。我们的结果表明, 对于交易所原生代币和山寨币资产, Beta 变动可能歪曲底层共动结构: 表面 "脱钩" 可能反映波动率压缩而非因子敞口减弱。
2. **框架的通用性。** 分解 $\beta = \rho \cdot (\sigma_i/\sigma_m)$ 和进一步的分子/分母分解适用于任何资产-基准对。研究任何资产类别中 Beta 变化的研究人员都可以应用此分解。
3. **横截面推断的方法论警示。** 合成对照结论可能根据 donor pool 构成而反转 (Section 4.8 和附录 C); 我们提供了一个工作示例, 说明当处理单元在横截面中独特时, donor 的经济可比性应优先于统计拟合。

### 未来研究方向

本文 **有意将范围限定为记录与分解, 而非因果推断**。后续研究议程 — 计划中的下一篇论文 — 包括:

1. **链上稳定币流分析**: 在 ETH 压力事件期间, USDT/USDC/FDUSD 流入 BNB 配对流动性池的 Glassnode/Nansen 数据, 用于辨别主动干预与被动供应假设。
2. **错时处理设计**: 利用 OKX (OKB)、Crypto.com (CRO)、KuCoin (KCS)、Bitget (BGB) 的持有者奖励启动日期, 应用 Callaway & Sant'Anna (2021) 错时 DiD 识别项目特定渠道效应。
3. **剂量反应分析**: HODLer airdrop 月度强度 (次数 + 名义价值) 作为时变处理强度, 回归至滚动窗口 Beta 和波动率比率成分。
4. **更广泛事件集的 ETH 端分解**: 超越附录 B 中检验的 ETH ETF 事件 (产生 null 结果), 围绕 FOMC 决议、美元强势拐点、post-Shanghai 质押比率体制、宏观经济因素的事件研究设计, 将 43% ETH 端份额归因于特定渠道。
5. **类别级 Beta 异质性**: 调查为什么 DeFi/Oracle 代币 (UNI、LINK) 平均显示 Beta *增加* — 可能反映与 ETH 生态系统活动 (Gas 费、质押收益、DeFi TVL) 的现金流联系。
6. **波动率渠道感知因子模型**: 用明确的波动率比率成分扩展标准单因子或三因子加密货币因子模型。

### 版本历史 (从最新版本开始)

本文经历了九轮主要修订。每行总结标题更改和触发该更改的审稿人关注点。其中两轮是从根本上重构论文的 *战略转折点*, 用 ⭐ 标记, 并在后续 **研究轨迹** 子部分中详细讨论。

| 版本 | 主要变更 | 动机 |
|---|---|---|
| **v9.2 (Final)** | 添加 ETH ETF 事件研究附录 B (透明地报告 null 结果); 删除趋势转换附录; 更新作者简介 | 直接检验 ETF 事件是否驱动 ETH 端 43% 份额; 论文专注度和选择性报告关注 |
| v9.1 | 合成对照主规范变更为 14-donor (排除 TRX/XRP), 16-donor 降为敏感性分析。Section 5.2 添加三个检验调和 (Chow / $t$-test / synthetic) + 检验功效和假设比较。Section 4.5 添加 DCC vs.\ 静态 Beta 差异讨论 | Donor pool 经济可比性是合成对照有效性的前提条件; 对冲突检验结果的审稿人友好的诚实处理 |
| **v9.0** ⭐ | **从因果效应论文到方法论论文的战略再定位。** 新标题 ("Directional Decoupling and the Volatility-Ratio Channel: A Beta-Decomposition Framework"); HODLer Airdrops 从标题中删除并降为 "时间基准点"; Variance Decomposition 移至 4.1 (原 4.8); "Identification" → "Cross-sectional specificity"; "treatment date" → "reference partition date" 全文统一变更 | 通过将贡献重新构建为方法论框架 + 实证分解, 绕开使用现有数据无法获胜的识别辩论; 与分析贡献的实际优势相匹配 |
| v8.0 | 添加分子/分母分解 (Table 6: BNB 端 57% / ETH 端 43%); 趋势转换降为仅在附录中; Future Work 强化为 "计划中的后续论文" | 利用现有数据的快速分析扩展; 区分 BNB 特定机制和 ETH 端机制的数学分解 |
| v7.0 | $t$-统计量符号修正 ($+2.21 \to -2.22$) + 明确解释; 在附录 C 中添加 TRX/XRP 合成对照敏感性检查; 扩展 HT 包含 robustness; Section 4.7 加强 DeFi 类别内异质性 | 审稿人指出符号惯例; donor pool 关注作为 robustness 形式化; 类别内方差的诚实报告 |
| v6.0 | 由于 HTX 交易所地位下降, 从主对照池中排除 HT (Huobi Token); 添加统计推断 (one-sample $t$-test, Wilcoxon, empirical-rank); 添加图 1 (rolling beta 可视化) | 受污染对照问题; 审稿人要求正式推断而非排名统计; 请求视觉证据 |
| **v5.0** ⭐ | **实证扩展**: 对照池从 7 个仅交易所代币扩展到 4 个类别 (交易所代币、L1 平台、DeFi/Oracle、其他山寨币) 17 个多样化山寨币。揭示 DeFi *再耦合* ($+0.025$) — 与交易所代币方向相反 | 审稿人关注 7 个仅交易所池过于狭窄; 更广泛的池揭示了类别间异质性, 重塑了整体解释 |
| v4.0 | 添加方差分解 (Table 5: 波动率比率渠道 100%, 相关性渠道 0%); 引入 "directional decoupling" 概念 | 审稿人询问相关性不变时 Beta 为何下降; 数学分解精确分离了渠道 |
| v1.0–v3.0 | 初始因果效应研究: BNB 对 ETH 的 Beta 在 2024 年 4 月后下降 16.9%; Chow test 拒绝结构稳定性; HODLer Airdrops 作为处理 | 作为 HODLer Airdrops 计划的处理效应研究的初始构成 |

### 研究轨迹: 两个转折点

本文的研究轨迹被两个战略转折点根本性地重构, 每一个都改变了论文的主张:

**⭐ 转折点 1 — v5.0 (对照池的实证扩展):** 对照池从 7 个仅交易所代币扩展到跨四个类别的 17 个多样化山寨币。这一扩展揭示了原始 7-token 池无法显示的结果: 虽然交易所代币、Layer-1 平台和其他山寨币平均从 ETH 脱钩, 但 **DeFi 和 Oracle 代币 *再耦合*** (平均 $\Delta\beta = +0.025$, 主要由 UNI 和 LINK 推动)。BNB 在更广泛池中的排名为 17 中第 6 — 中等, 非极端。这一发现使原本的 "HODLer Airdrops 导致 BNB 特定脱钩" 故事难以维持: 数据反而指向具有相当大跨类别异质性的市场范围重新排序。论文必须开始叙述更诚实的解释, 这直接导致了 v6–v8 的改进。

**⭐ 转折点 2 — v9.0 (方法论再定位):** 到 v8 时论文积累了强大的实证内容 (波动率比率渠道 100% 分解, 57/43 分子/分母分割, 完整横截面分析), 但其针对任何 HODLer 计划特定因果效应的识别策略仍然薄弱。使用现有数据, 审稿人对识别的攻击本质上无法获胜。v9.0 的战略决定是 **完全停止主张因果关系, 将论文重新定位于其实际最强贡献——方差分解框架**。标题被改为以方法论思想开头, Variance Decomposition 部分被移至 4.1 作为第一个实证结果, 所有因果语言 ("treatment"、"identification") 被替换为中立术语 ("reference partition"、"cross-sectional specificity"), 引言以加密货币因子模型的 gap (Liu & Tsyvinski 2021, 2024) 而非以 HODLer Airdrops 开头。这一转变将论文从脆弱的因果效应研究升级为具有超越 BNB 适用性的可辩护方法论论文。

### 研究问题的演变

| 阶段 | 版本 | 核心问题 | 状态 |
|---|---|---|---|
| 因果效应研究 | v1–v3 | HODLer Airdrops 计划是否使 BNB 与 ETH 脱钩? | 识别被证明无法维持 |
| 分解研究 | v4–v5 | 如果 Beta 下降但相关性不变, 那么变化在联合分布的*何处*发生? | 框架结晶化; 横截面背景揭示了更广泛的模式 |
| 精化 | v6–v8 | 实证模式有多 robust, BNB 在横截面上如何比较? | 所有 robustness 检验通过; 添加分子/分母分解 |
| 方法论论文 | v9.0–v9.2 | 方差分解框架揭示了关于加密货币市场 Beta 动态的什么, 以 BNB-ETH 作为说明性案例? | **当前范围** — 可辩护、可推广、对审稿人友好 |

[Repository 内容 →](#-repository-contents) · [引用 →](#-citation) · [作者 →](#-author)

---

## 📂 Repository Contents

| File | Description |
|---|---|
| `paper.pdf` | Working paper v9.2 Final (27 pages, includes Figure 1) |
| `paper.tex` | LaTeX source |
| `figure1_rolling_beta.pdf` / `.png` | Figure 1: 90-day rolling beta visualization |
| `did_v6_no_ht.csv` | Cross-sectional comparison: 16-token altcoin pool (HT excluded) |
| `v9_2_supplementary.json` | Statistical tests, synthetic counterfactual (main 14-donor + sensitivity 16-donor), robustness, numerator/denominator decomposition, ETH ETF event study |
| `variance_decomposition.json` | Beta change decomposition (100% volatility channel) |
| `synthetic_control.json` / `synthetic_control_gap.csv` | Synthetic counterfactual results |
| `dcc_dynamic_correlation.csv` / `dcc_conditional_beta.csv` | DCC-GARCH dynamic series |
| `garch_conditional_vol.csv` | GARCH(1,1) conditional volatility |
| `bnb_rolling_beta_90d.csv` | 90-day rolling beta time series |
| `structural_breaks.json` | Bai-Perron / PELT / Chow test results |
| `mm_indirect_evidence.json` | Distributional evidence (Appendix A) |

[↑ Back to top](#directional-decoupling-and-the-volatility-ratio-channel)

---

## 📊 Citation

```bibtex
@unpublished{kim2026directional,
  author       = {Kim, Dennis},
  title        = {Directional Decoupling and the Volatility-Ratio Channel:
                  A Beta-Decomposition Framework for Exchange-Native Tokens},
  subtitle     = {Evidence from the {BNB}--{ETH} Relationship, 2022--2026},
  year         = {2026},
  note         = {SSRN Working Paper v9.2 (Final), Betalabs Inc. ORCID: 0009-0002-0962-2175},
  url          = {https://github.com/gameworkerkim/vibe-investing}
}
```

[↑ Back to top](#directional-decoupling-and-the-volatility-ratio-channel)

---

## Author

**Dennis Kim**, CEO, Betalabs Inc.

Dennis Kim has worked in the blockchain industry since 2017, serving as a long-standing intermediary between the Korean and Chinese blockchain ecosystems with substantial contributions to mainnet infrastructure, exchange security, regulatory policy, and token-listing strategy. In 2022 he was appointed CEO and CTO of Cyworld — the world's first social network — where he led the recovery of 3.8 petabytes of historical user data and approximately 18 billion photographs.

[↑ Back to top](#directional-decoupling-and-the-volatility-ratio-channel)

---

## 📚 Related Literature

- **Cryptocurrency asset pricing**: Liu & Tsyvinski (2021, RFS); Liu, Tsyvinski & Wu (2024, JoF); Sockin & Xiong (2023, JoF)
- **Exchange tokens**: Lee, Li & Shin (2023); Howell, Niessner & Yermack (2020, RFS)
- **Crypto volatility & tail risk**: Borri (2019, JEF); Yarovaya & Zięba (2022); Corbet et al. (2018, IRFA); Baur & Dimpfl (2021, EE); Dyhrberg (2016, FRL); Baur et al. (2018, FRL)
- **DeFi tokenomics**: Schär (2021, FRBSL Review)
- **Asymmetric & downside risk**: Ang, Chen & Xing (2006, RFS); Kahneman & Tversky (1979); Barberis & Thaler (2003)
- **Treatment effect methodology** (used for cross-sectional benchmarking): Abadie, Diamond & Hainmueller (2010, JASA); Callaway & Sant'Anna (2021, JoE); Bai & Perron (2003)
- **Volatility modeling**: Engle (2002, JBES)

Full references in `paper.pdf`.

---

## Contact

**Dennis Kim**  
CEO, Betalabs Inc., Seoul, South Korea  
Email: [gameworker@gmail.com](mailto:gameworker@gmail.com)  
ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)  
GitHub: [@gameworkerkim](https://github.com/gameworkerkim)  
Repository: [vibe-investing](https://github.com/gameworkerkim/vibe-investing)

[↑ Back to top](#directional-decoupling-and-the-volatility-ratio-channel)

---

## License

Free to cite with attribution. Academic research use.

## Disclaimer

This paper presents quantitative academic analysis only. **Not investment advice**.
