# Distribution Asymmetry of Centralized Exchange Airdrops and the BNB Chain Ecosystem

[![SSRN: 6688740](https://img.shields.io/badge/SSRN-6688740-orange.svg)](https://ssrn.com/abstract=6688740)
[![Companion: SSRN 6632838](https://img.shields.io/badge/Companion-SSRN%206632838-orange.svg)](https://ssrn.com/abstract=6632838)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

> **Multilingual READMEs**: [한국어](./README_KR.md) · [中文](./README_CN.md) · [日本語](./README_JP.md)

---

## Overview

This repository contains the **preliminary working paper, source code, data, and figures** for an empirical and theoretical study of the asymmetric value distribution mechanism of Binance's centralized exchange (CEX) airdrop programs (Megadrop and HODLer Airdrop) during 2024–2025.

**Authors**: HoKwang Kim (Dennis Kim), CEO of Betalabs Inc.
**Status**: Preliminary Working Paper, May 2026
**SSRN**: [Abstract ID 6688740](https://ssrn.com/abstract=6688740)
**Companion paper**: [Kim, H. (2026). *The 72-Hour Shock: Token Unlock Price Impact*. SSRN 6632838](https://ssrn.com/abstract=6632838)

---

## Research Question

> **Who actually benefits — and at whose cost — from Binance's $2.6 billion airdrop programs?**

In 2024–2025, Binance distributed approximately $2.6 billion across more than 76 reward programs to BNB holders, accounting for approximately 94% of global CEX distributions. The headline programs are *Megadrop* and *HODLer Airdrop*, widely promoted as: *"Lock BNB and receive new project tokens for free."*

This study formalizes the differential impact on three actors:

1. **BNB Holders** — Recipients of distributed tokens
2. **Issuing Foundations** — The project entities issuing new tokens
3. **BNB Chain Ecosystem** — The blockchain platform itself

---

## Key Findings

### 1. Foundation Disaster

For Megadrop tokens with average distribution ratio α = 7.3%:
- **Foundation cost ≈ 30.5% of FDV** (Fully Diluted Valuation)
- **Asymmetry ratio R = 4.18** (Foundation loss : Holder gain)
- **Value destruction D ≈ 23% of FDV** through market friction

### 2. Mathematical Robustness

Across reasonable parameter ranges (α: 2–15%, θ: 30–60%, d: 10–90%):
- Foundation cost is always ≥ 12.75%
- Asymmetry ratio is always R ≥ 1.70
- **Critical distribution ratio α* = 5.95% (R*=5)** — Megadrop's typical 5–8% range falls within the explosion zone

### 3. Empirical Verification

Bootstrap 95% CI analysis (N = 10,000 iterations, sample N = 21 tokens):

| Category | N | Mean Return | 95% CI |
|----------|---|-------------|--------|
| Megadrop | 5 | −76.0% | [−86.4%, −65.8%] |
| HODLer | 8 | −19.5% | [−67.8%, +39.6%] |
| Launchpool | 5 | −29.8% | [−50.4%, +0.0%] |
| Direct (Memecoin) | 2 | +81.5% | [+68.0%, +95.0%] |
| **Direct (with HYPE)** | 3 | **+384.3%** | **[+68.0%, +990.0%]** |

**Cohen's d (Megadrop vs. Direct, N=21) = −1.52** (very large effect, academic credibility achieved through Hyperliquid HYPE counterfactual integration)

### 4. The Decoupling Pattern

While Megadrop tokens declined, BNB Chain ecosystem grew in *opposite direction*:

| Indicator | Q1→Q3 2025 Change |
|-----------|-------------------|
| BNB Chain Trading Volume | **+171.4%** |
| BNB Chain DeFi TVL | **+47.2%** |
| BNB Chain Active Wallets | **+91.6%** |
| BNB Price | $629 → $1,030 (ATH $1,369 in Q4) |
| Megadrop Category Market Cap | **−75%** |

### 5. Three-Actor Monetary Impact (2024–2025)

| Actor | Estimated Impact |
|-------|------------------|
| BNB Holders (Gain) | **+$1.4B–$2.0B** |
| Issuing Foundations (Loss) | **−$4.8B** |
| BNB Chain Market Cap (Growth) | **+$104B** |

**Key insight**: Foundation loss is unambiguous (2.84× holder gain), but constitutes only 4.6% of BNB Chain market cap growth — *a decoupling pattern at the system level*.

### 6. Theoretical Contribution

Seven theorems formalize the foundation cost function and prove:

- **Theorem 6**: *Break-even impossibility* — d* = −α/(1−α−θ) < 0 (foundation can only break even with price increase)
- **Theorem 7**: *Nash equilibrium* — Immediate sell-off is the dominant strategy

This work extends Allen, Berg, and Lane's (2023) analysis of *direct airdrops* to the novel category of *centralized exchange-led (CEX-led) airdrops*, applying Schelling's (1960) coordination game theory and Morris and Shin's (1998) Global Games framework.

---

## Repository Structure

```
.
├── README.md                          # This file (English)
├── README_KR.md                       # Korean version
├── README_CN.md                       # Chinese version
├── README_JP.md                       # Japanese version
├── paper/                             # Main paper deliverables
│   ├── Distribution_Asymmetry_CEX_Airdrops.md
│   ├── Distribution_Asymmetry_CEX_Airdrops.pdf
│   ├── Distribution_Asymmetry_CEX_Airdrops_with_figures.docx
│   └── Distribution_Asymmetry_CEX_Airdrops_with_figures.pdf
├── figures/                           # 7 publication-grade visualizations
│   ├── Chart5_BreakEvenRegion.{png,pdf}      # Figure 1
│   ├── Chart1_ForestPlot.{png,pdf}           # Figure 2
│   ├── Chart4_HYPE_Counterfactual.{png,pdf}  # Figure 3
│   ├── Chart2_Decoupling.{png,pdf}           # Figure 4
│   ├── Diagram2_DecouplingDomains.{png,pdf}  # Figure 5
│   ├── Chart3_ThreeActor.{png,pdf}           # Figure 6
│   └── Diagram1_Causal_Chain.{png,pdf}       # Figure 7
├── scripts/                           # Python source code
│   ├── correlation_analysis.py        # Section 5 BTC/ETH/BNB correlations
│   ├── robustness_analysis.py         # Section 4.10 scenario analysis
│   ├── integrated_analysis_v10.py     # HYPE-integrated v1.0 analysis
│   ├── pair_trading_backtest.py       # Section 5.4 supplementary
│   └── generate_figure[1-7]_*.py      # Figure generators
├── data/                              # Input data (CSV, English)
│   ├── listed_tokens.csv              # N=21 token sample
│   ├── btc_eth_bnb_quarterly.csv      # Quarterly prices N=9
│   ├── bnb_chain_metrics.csv          # BNB Chain Q1–Q3 2025
│   └── correlation_matrix.csv         # Pre-computed correlations
├── results/                           # Pre-computed analysis output
└── docs/                              # Documentation
    ├── data_dictionary.md
    ├── figures_guide.md
    └── CHANGELOG.md
```

---

## Reproducibility

### Quick Start

```bash
# Clone the repository
git clone https://github.com/gameworkerkim/vibe-investing.git
cd vibe-investing/02.Investment\ Idea\ Column/BNBChain

# Install dependencies
pip install pandas numpy scipy matplotlib

# Run all analyses (output to results/)
cd scripts/
python correlation_analysis.py
python robustness_analysis.py
python integrated_analysis_v10.py
python pair_trading_backtest.py

# Regenerate all figures (output to figures/)
for f in generate_figure*.py; do python "$f"; done
```

### Selective Execution

| Script | Purpose | Output |
|--------|---------|--------|
| `correlation_analysis.py` | BTC/ETH/BNB correlations + H1, H2 hypothesis tests | `results/correlation_results.txt` |
| `robustness_analysis.py` | Scenario analysis + bootstrap CI + Cohen's d | `results/robustness_results.txt` |
| `integrated_analysis_v10.py` | HYPE-integrated v1.0 (post external evaluation) | `results/integrated_v10_results.txt` |
| `pair_trading_backtest.py` | Section 5.4 supplementary (observational only) | `results/pair_trading_backtest_results.txt` |

---

## Caveats and Limitations

This is a **preliminary working paper**. The following limitations are explicitly acknowledged:

1. **Sample size**: N=21 tokens (per category N=2–8) is too small for full statistical inference. Subsequent versions will expand to N≥100.
2. **Causality**: The decoupling pattern is **observational evidence only**. Full Granger causality testing requires daily data, deferred to subsequent versions.
3. **Time resolution**: Quarterly data limits short-term causal direction inference.
4. **Selection bias**: Direct category Memecoin bias partially mitigated by HYPE inclusion (N=2→N=3), but selection effect cannot be fully excluded.
5. **Trading strategies**: Section 5.4 BTC dominance pattern is **observational evidence**, not for trading strategy use.
6. **Prediction**: This study produces **descriptive analysis** of past listings. Future tokens may show different patterns due to evolving CEX policies.

---

## Citation

If you use this code, data, or paper in your research, please cite:

```bibtex
@misc{kim2026distribution,
  author = {Kim, HoKwang},
  title = {Distribution Asymmetry of Centralized Exchange Airdrops and the BNB Chain Ecosystem},
  year = {2026},
  publisher = {SSRN},
  doi = {10.2139/ssrn.6688740},
  url = {https://ssrn.com/abstract=6688740},
  note = {Preliminary working paper}
}
```

For the companion paper:

```bibtex
@article{kim2026shock,
  author = {Kim, HoKwang},
  title = {The 72-Hour Shock: Token Unlock Price Impact},
  year = {2026},
  journal = {SSRN Electronic Journal},
  doi = {10.2139/ssrn.6632838},
  url = {https://ssrn.com/abstract=6632838}
}
```

---

## License

This repository uses **dual licensing**:

- **Source code** (Python scripts in `scripts/`): [MIT License](https://opensource.org/licenses/MIT)
- **Paper, data, and figures** (`paper/`, `data/`, `figures/`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

## Author

**HoKwang Kim (Dennis Kim)** · Independent Researcher
- CEO, Betalabs Inc. (Blockchain Company Builder)
- Former CEO, Cyworld Z
- Microsoft Azure MVP (former, 9 years)
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
- Email: gameworker@gmail.com

---

## Roadmap

### v1.2 (Current — May 2026)
- HYPE counterfactual integration (N=2→N=3)
- Bootstrap 95% CI with N=10,000 iterations
- Three-actor differential impact quantification
- 7 publication-grade figures with academic captions
- Section 5.2 correlation values corrected
- Figure renumbering to body-appearance order

### v2.0 (Planned — 2027)
- Sample size N≥100 tokens
- Daily OHLCV data via CoinGecko/Binance APIs
- Full Granger causality testing
- Propensity Score Matching (PSM) for selection bias
- Heckman 2-step estimation
- Multi-exchange comparison (Bybit, OKX, Coinbase)
- LaTeX submission to peer-reviewed journal

---

## Related Work

- **Companion paper**: Kim, H. (2026). *The 72-Hour Shock: Token Unlock Price Impact*. SSRN 6632838.
- **Token unlock literature**: Allen, F., Gu, X., & Li, J.Y. (2023). *Crypto Tokens and Token Offerings: An Introduction*. Annual Review of Financial Economics.
- **Cointegration methodology**: Engle, R.F., & Granger, C.W.J. (1987). *Co-integration and Error Correction*. Econometrica.
- **Coordination games**: Schelling, T.C. (1960). *The Strategy of Conflict*. Harvard University Press.
- **Global Games**: Morris, S., & Shin, H.S. (1998). *Unique Equilibrium in a Model of Self-Fulfilling Currency Attacks*. American Economic Review.

---

*Last updated: May 1, 2026*
