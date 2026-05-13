# Changelog

All notable changes to this paper are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [5.1] — 2026-05-13 (Trilingual edition)

### Added
- **English edition** (`paper_en.tex`, `paper_en.pdf`, 21 pages) with all
  figures regenerated using English labels (`figures/en/`) and tables
  translated.
- **Chinese (Simplified) edition** (`paper_zh.tex`, `paper_zh.pdf`, 18 pages)
  using xeCJK with Noto Serif CJK SC. Reuses the English figures, following
  Chinese academic finance convention.
- Term-mapping table standardising Chinese translations:
  김치 프리미엄 → 泡菜溢价, BTC-numéraire → BTC本位,
  자본통제 → 资本管制, 정규화 분산 비율 → 标准化方差比.
- Citation files: `CITATION.cff`, `.zenodo.json`, `references.bib` for
  GitHub citation widget and Zenodo DOI integration.

### Changed
- Author block simplified across all editions: **HoKwang Kim** (single form).
  Korean edition retains 김호광 (HoKwang Kim) as the native form.

## [5.0] — 2026-05-13 (Tone calibration)

### Changed
- **Policy claim tone softened** (§7, §9): "should be maintained" →
  "appears appropriate to maintain"; "should be liberalised" → "merit gradual
  liberalisation"; "will converge" → "may converge". §7 opens with an
  explicit conditional: "Under the assumption that the present simulation
  reflects a first-order approximation of the real market structure".
- **§9 conclusion** restated as "Policy direction suggested by the
  simulation" rather than "Core policy message", and closes with a hedge:
  "Actual policy decisions should be informed by follow-up empirical work
  re-estimating the present model on real exchange data."
- §6.5 causal claim softened: "the kimchi premium is the regulatory cost"
  is now framed as one of "principal structural drivers". The KCS-detected
  14.2 trillion KRW reported as an *indirect indicator* rather than a
  *direct measure*.
- §5 methodology now discloses ±20% winsorisation up-front (previously
  only mentioned in §8 Limitation 3).

### Added
- **§6.4 "Reading caveat"** subsection naming the modelling assumption
  directly: OKX and Bybit are modelled as "microstructure noise without
  regulatory friction", so the offshore-only 0.2–0.3% premium is partly a
  function of this assumption.
- **Appendix A "Core modelling assumption — offshore-exchange spread"** new
  subsection detailing AR(1) noise calibration (φ=0.55, σ_ε ∈ [0.0012, 0.0016])
  and citing Pieters & Vivanco (2017) for empirical plausibility.
- **Follow-up agenda 7**: empirical verification of the offshore-exchange
  spread using Binance/OKX/Bybit one-minute BTC data.
- Author block now identifies "Cyworld Z former CEO" and "Practitioner in
  Blockchain and Web3 since 2017", with GitHub repository URL.

## [4.0] — 2026-05-12 (Cross-exchange identification + policy cost)

### Added
- **§6.4 Cross-exchange comparison**. New identification strategy: directly
  compare the BTC-numéraire premium variability across Binance, OKX, Bybit
  (offshore-only pairs) with Bithumb-vs-offshore pairs. Simulation results:
  offshore pairs 0.22–0.34% standard deviation vs Bithumb pairs 0.85–1.63%
  (3–7× asymmetry). Identifies the kimchi premium as a regulatory cost
  rather than a market inefficiency.
- **§6.5 Policy cost** with Korea Customs Service detection data
  (released 2025-10-21 by NA Member Choi Eun-seok). Crypto-mediated illegal
  forex transactions: 14.2 trillion KRW cumulative 2018–2025; 1.158 trillion
  KRW in 2024; 0.881 trillion KRW in 2025 Jan–Aug.
- **Figure 10** cross-exchange comparison (4-panel layout).
- **Figure 11** policy-cost time series.
- **Table 7** cross-exchange summary statistics.
- **Table 8** annual KCS detection figures.
- New `data/cross_exchange_premium.csv`, `data/cross_exchange_summary.csv`,
  and `data/policy_cost.csv`.

### Changed
- §1 Introduction strengthened with cross-exchange motivation and capital
  outflow paragraph citing KCS data.
- §9 Conclusion adds "Core policy message" paragraph.
- §7 Discussion adds policy implication subsection.

## [3.0] — 2026-05-12 (Calibration transparency + Student-t EGARCH)

### Added
- **Appendix A** "Calibration Mechanism and Moment Matching" documenting
  the stochastic generative process for every component (FX, prices,
  premium event bumps, USDT premium, volume ratio) and reporting
  moment-matching statistics against the literature: π^KRW_BTC mean
  0.89% (Makarov-Schoar 2020 range 0.5-3%), AR(1) coef 0.911 (Choi et al.
  2022 range 0.85-0.95), excess kurtosis 29.4 (Eom 2021 leptokurtic).
- **Figure 9** EGARCH(1,1) diagnostic (Q-Q + ACF of squared residuals).
- **§7 micro-structure interpretation** of ρ_BNB > ρ_XVS puzzle: two
  complementary hypotheses — basis-trading-induced perturbation and
  microstructure noise amplification.
- **§8 Limitation 3**: EGARCH distributional assumption and winsorisation.
- **Follow-up agenda 6**: duration analysis (survival/Hawkes).

### Changed
- **EGARCH(1,1) re-estimated** in percent units with **Student-t
  innovations**. Previous v2 log-likelihood +4,145 (artefact of decimal
  scale) corrected to −4,616. Estimated parameters: γ̂=−0.073 (t=−2.10,
  p<0.05), ν̂=37.4, AIC=9,244.72, BIC=9,278.03.
- Author block updated: Web3Paper removed; ORCID 0009-0002-0962-2175
  added as hyperlink; GitHub repository URL added to data/code disclosure.
- §7 and §8 cleanly separated: §7 contains only implications and
  applications; §8 holds all limitations and follow-up agenda.

## [2.0] — 2026-05-12 (Methodological rigour)

### Added
- **BNB** as a primary analysis target (Bithumb-listed since 2021-05-27).
  Previously v1 analysed only XVS and ETH.
- **Normalised variance ratio** ρ_X = Var[π^BTC_X] / Var[Δlog P_X] (Eq. 7
  and Fig. 7) to control for token-level own volatility in the H_BSC test.
  Result: ETH 0.42, XVS 0.82, BNB 1.13 → H_BSC tentatively rejected.
- **Newey-West HAC standard errors** (Bartlett kernel, L=7) reported
  alongside classical OLS. Key finding: Korean regulatory dummy
  t_OLS=3.1 → t_HAC=1.12 (loses significance), while global shock dummy
  remains strongly significant (t_HAC=−3.81).
- **EGARCH(1,1) volatility model** (Table 4, Fig 8) testing H2.
- **Five new references**: Gromb & Vayanos (2010), Liu, Tsyvinski & Wu
  (2022, JF), Ahn & Kim (2023), Hwang et al. (2024), Capponi & Jia (2021),
  plus Newey & West (1987).
- **§8 Limitations and follow-up agenda** with 2 explicit limitations and
  5 follow-up research items.

### Changed
- Subtitle: "A Theoretical Framework with Calibrated Simulation Evidence"
  to clarify that all quantitative results are simulation-based.
- §1 "Disclosure on data" note added.

## [1.0] — 2026-05-12 (Initial release)

### Added
- Theoretical framework for the BTC-numéraire kimchi premium
  $\pi^{\text{BTC}}_X(t)$ with FX-noise cancellation (Proposition 1).
- Four premium measures (FX, USDT, BTC, ETH-alpha) and BSC triangular
  arbitrage structure.
- Five testable hypotheses (H1 through H5).
- Synthetic dataset (T=2,192 daily observations, 2020-01-01 to 2025-12-31)
  calibrated to literature stylized facts.
- OLS regression with 6 explanatory variables and dummies.
- Eight figures and three tables.
- 12 references.
