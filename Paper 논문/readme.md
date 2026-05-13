# The Bithumb–Binance BTC-numéraire Premium

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid)](https://orcid.org/0009-0002-0962-2175)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![LaTeX](https://img.shields.io/badge/typeset-XeLaTeX-008080.svg)](https://www.latex-project.org/)
[![DOI](https://img.shields.io/badge/Cite-CITATION.cff-success)](./CITATION.cff)

> **A Theoretical Framework with Calibrated Simulation Evidence on BNB Chain Tokens**
>
> **HoKwang Kim** (Betalabs Inc., former CEO of Cyworld Z)
> Practitioner in Blockchain and Web3 since 2017
> Working paper, May 2026 — Version 5.1 (trilingual edition)

This paper proposes a new measure of the Korean "kimchi premium" using BTC
as an internal *numéraire*, denoted $\pi^{\text{BTC}}_X(t)$. The measure
is invariant to exchange-rate and stablecoin-level fluctuations by
numerator–denominator cancellation (Proposition 1). Calibrated simulation
evidence on 2020–2025 daily series shows that a cross-exchange comparison
among Binance, OKX, Bybit, and Bithumb identifies the kimchi premium as
the **price of a Korea-specific regulatory friction**, not a market
inefficiency — and Korea Customs Service detection of crypto-mediated
illegal foreign-exchange transactions (≈ 14.2 trillion KRW over 2018–2025;
≈ 2.04 trillion KRW over 2024–2025) is read as a lower-bound indicator
of the policy cost.

---

## Available in three languages

| Language | PDF | LaTeX source | Pages | Engine |
|----------|-----|--------------|-------|--------|
| **한국어 (Korean)** | [`ko/paper.pdf`](./ko/paper.pdf) | [`ko/paper.tex`](./ko/paper.tex) | 19 | XeLaTeX + xeCJK + Noto Serif CJK KR |
| **English** | [`en/paper_en.pdf`](./en/paper_en.pdf) | [`en/paper_en.tex`](./en/paper_en.tex) | 21 | XeLaTeX + Latin Modern Roman |
| **中文 (Chinese, Simplified)** | [`zh/paper_zh.pdf`](./zh/paper_zh.pdf) | [`zh/paper_zh.tex`](./zh/paper_zh.tex) | 18 | XeLaTeX + xeCJK + Noto Serif CJK SC |

All three editions share identical content (figures, data, equations, structure).

---

## Quick start

### Read the paper

Open `en/paper_en.pdf` (or the Korean / Chinese equivalents) directly.

### Cite this work

The [`CITATION.cff`](./CITATION.cff) file allows GitHub to display a
"Cite this repository" button (top-right of the repo page). Alternatively,
copy the BibTeX entry from [`references.bib`](./references.bib):

```bibtex
@techreport{kim2026satoshi,
  author      = {Kim, HoKwang},
  title       = {The Bithumb--Binance {BTC}-num\'eraire Premium},
  institution = {Betalabs Inc.},
  type        = {Working Paper},
  year        = {2026},
  month       = {5},
  url         = {https://github.com/gameworkerkim/vibe-investing},
  version     = {5.1},
}
```

### Reproduce all results

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Rebuild data, figures, equations, tables
python3 build_data_v2.py     # baseline synthetic dataset
python3 build_data_v3.py     # Student-t EGARCH, moment matching
python3 build_data_v4.py     # OKX/Bybit, cross-exchange, policy cost
python3 build_figures_v2.py
python3 build_figures_v3.py
python3 build_figures_v4.py
python3 build_figures_en.py  # English-labeled versions
python3 build_equations.py
python3 build_tables_v2.py
python3 build_tables_v3.py
python3 build_tables_v4.py
python3 build_tables_en.py

# 3. Compile the PDFs (XeLaTeX required)
cd ko && xelatex paper.tex && xelatex paper.tex
cd en && xelatex paper_en.tex && xelatex paper_en.tex
cd zh && xelatex paper_zh.tex && xelatex paper_zh.tex
```

Random seed (`numpy.random.default_rng(20260513)`) is fixed in
`build_data_*.py`, so the synthetic series and all derived statistics are
exactly reproducible.

---

## Repository structure

```
.
├── ko/                            # Korean edition
│   ├── paper.pdf                  # 19-page PDF
│   ├── paper.tex                  # LaTeX source
│   └── tab_*.tex                  # 7 tables
├── en/                            # English edition
│   ├── paper_en.pdf               # 21-page PDF
│   ├── paper_en.tex
│   └── tab_*.tex
├── zh/                            # Chinese (Simplified) edition
│   ├── paper_zh.pdf               # 18-page PDF
│   ├── paper_zh.tex
│   └── tab_*.tex
│
├── figures/                       # 11 PNGs (English-labeled, shared)
├── data/                          # 15 reproducible synthetic CSVs
├── equations/                     # 14 displayed equation PNGs
│
├── build_*.py                     # Python reproduction scripts
├── build_docx_*.js                # Word docx generator (Node.js + docx)
├── requirements.txt               # Python dependencies
│
├── CITATION.cff                   # GitHub citation widget
├── .zenodo.json                   # Zenodo DOI metadata
├── references.bib                 # BibTeX citation
├── CHANGELOG.md                   # Version history (v1 → v5.1)
├── AUTHORS.md                     # Author details
├── LICENSE                        # CC BY 4.0 (content) + MIT (code)
└── README.md                      # This file
```

---

## Key findings (simulation evidence)

The paper is positioned as **simulation evidence** of a new measurement
framework, not as an empirical study on real exchange data. All
quantitative results below are properties of the calibrated synthetic
series and need to be re-estimated on real API data by follow-up work.

1. **FX-noise removal.** Satoshi-premium standard deviation is roughly
   half the KRW-premium standard deviation, consistent with Proposition 1.

2. **Cross-exchange identification.** Among non-Korean exchanges, the
   pairwise satoshi-premium standard deviation is 0.22–0.34% (ETH) and
   0.22–0.32% (BNB). Among Bithumb-vs-non-Korean pairs it is 0.85–0.90%
   (ETH) and 1.59–1.63% (BNB) — a **3 to 7× asymmetry** concentrated on
   the Bithumb side. This identifies the kimchi premium as a regulatory
   cost rather than a market inefficiency.

3. **HAC adjustment changes the conclusion.** The Korean regulatory dummy
   has $t_{\text{OLS}}=3.1$ but $t_{\text{HAC}}=1.12$ (loses significance),
   while the global shock dummy stays at $t_{\text{HAC}}=-3.81$ (highly
   significant). Simple OLS event studies overstate the strength of
   Korean regulatory events.

4. **Asymmetric volatility (H2).** The EGARCH(1,1) leverage parameter is
   $\hat\gamma=-0.073$ ($t=-2.10$, $p<0.05$), supporting H2. Estimated
   with Student-t innovations on percent-scale, winsorized data, with
   AIC=9,244.72 and BIC=9,278.03.

5. **Quantitative policy cost.** Korea Customs Service detection of
   crypto-mediated illegal forex transactions: **14.2 trillion KRW**
   cumulative 2018–2025, of which **1.158 trillion KRW** in 2024 and
   **0.881 trillion KRW** in Jan–Aug 2025. This is a strict lower bound
   on capital outflow related to the kimchi-premium opportunity.

---

## Standing caveats

1. **Synthetic data caveat.** All CSVs are calibrated to literature
   stylized facts (Appendix A documents the generative mechanism). Real
   empirical estimation requires 1-min or daily-bar data from the
   Bithumb, Binance, OKX, and Bybit APIs.

2. **Modeling-assumption caveat.** OKX and Bybit are modelled as AR(1)
   microstructure noise without regulatory friction. The offshore-only
   premium of 0.2–0.3% in the simulation is partly a function of this
   assumption.

3. **Policy-cost caveat.** KCS-detected figures are a lower bound (true
   detection rate is small); and not all detected illegal forex is
   kimchi-arbitrage-driven (property flight, money laundering, simple
   remittance avoidance also contribute).

---

## Policy direction suggested by the simulation

Under the assumption that the simulation reflects a first-order
approximation of the real market structure, the cross-exchange evidence
suggests a policy package combining:

1. **Maintain KYC/AML/CFT at current intensity** — FATF Recommendation 16
   standard, independent of the arbitrage channel.

2. **Gradual liberalisation of foreign access to Korean exchanges** —
   the current ban appears to be a key mechanism sustaining the premium
   and the associated capital outflow.

3. **KRW-stablecoin infrastructure** — provides a *route* (within the same
   KYC standard) for legitimate arbitrage to compress the premium.

Within the simulation model, this package would compress Bithumb-vs-offshore
satoshi premia toward the offshore range (0.2–0.3%) and remove the
structural impetus for capital outflow. Actual policy decisions should
nevertheless be informed by follow-up empirical work on real exchange data.

---

## License

This repository uses a dual license:

- **Paper content, figures, data**: [Creative Commons Attribution 4.0
  International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Reproduction code** (`build_*.py`, `build_docx_*.js`): [MIT License](./LICENSE)

See [LICENSE](./LICENSE) for full text.

---

## Contact

For questions, corrections, or empirical-data collaboration:

**HoKwang Kim**
Betalabs Inc.
gameworker@gmail.com
ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
