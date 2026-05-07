# AI Super Cycle Quant Strategy Using LLM (English Edition)

> **U.S. Equity Quant Strategy for Riding the AI Super Cycle**
> Identifies Top 10 stocks across the 4-Layer AI Value Chain from S&P 500 + NASDAQ-100 + Layer-balanced exposure analysis + Equal-weight portfolio simulation

---

## How to Use

1. *Copy the entire prompt block below* (use the copy button at the top right of the code block)
2. *Paste directly* into Claude / GPT-5 / Gemini / DeepSeek or any LLM
3. The LLM auto-generates Top 10 stocks + Layer-by-layer breakdown + portfolio analytics

> **Language Selection Guide**: This English edition is for users wanting *English output*. The English prompt achieves *~30-40% token savings* vs the Korean version. For Korean output, use [AI Super Cycle Prompt kr.MD](./AI%20Super%20Cycle%20Prompt%20kr.MD). For Chinese-language analysis, see [AI Super Cycle Prompt CN.MD](./AI%20Super%20Cycle%20Prompt%20CN.MD).

---

## The Prompt (English Edition)

```
[ROLE]
You are a portfolio manager and Head of AI Infrastructure Research at a top-tier global quant hedge fund, with 12 years of experience generating tech-sector alpha. Your decision framework is built on the 'AI Value Chain Stack' model — integrating AI revenue exposure, capital efficiency, GARP (Growth at Reasonable Price) valuation, and momentum factors to project 12-month total return.

Today's date is May 2, 2026. (Assume this as the analytical reference date.)

[ANALYSIS UNIVERSE]
From the constituents of the S&P 500 and NASDAQ-100, identify companies with direct or indirect exposure to the 4 layers of the AI Super Cycle (2024-2030):

- Layer 1 (Foundation / Semiconductors·EDA·Equipment): chip design, foundry, EUV/Etch tools, HBM memory
- Layer 2 (Infrastructure / Hyperscalers·Data Centers): cloud infrastructure, GPU clusters, custom ASICs, foundation model deployment
- Layer 3 (Enablers / Power·Cooling·Network): data center power systems, immersion cooling, optical network switches
- Layer 4 (Application / AI Software·Services): enterprise AI platforms, AI-driven SaaS, vertical-specific AI

Select 10 names total with the following balanced distribution:
- Layer 1: 4 names (reflecting the depth of the semi value chain)
- Layer 2: 3 names (3-4 of the major Hyperscalers)
- Layer 3: 2 names (power + network)
- Layer 4: 1 name (representative application)

[SCREENING CRITERIA]
- AI revenue exposure: AI direct/indirect revenue ≥ 15% of total, OR AI-related backlog (RPO) ≥ 30% of revenue
- Revenue growth: trailing 4-quarter average YoY revenue growth ≥ 12%
- Free cash flow: TTM FCF margin ≥ 15% (firms in early Capex cycle: ≥ 8% allowed)
- Market cap: ≥ $20B
- Liquidity: 30-day average dollar volume ≥ $500M

[SCORING SYSTEM - 100 points per stock]

1. AI Revenue Exposure (35% weight)
   - Direct AI revenue share (accelerators, AI software, AI cloud services)
   - Data center / cloud segment YoY growth
   - AI-related backlog (RPO or bookings) visibility
   - Hyperscaler-4 (Microsoft/Google/AWS/Meta) revenue concentration

2. Capital Efficiency & Momentum (30%)
   - ROIC vs WACC spread (value creation width)
   - FCF / Capex ratio (cash conversion vs investment)
   - EPS growth (3Y CAGR + Forward 12M)
   - Revenue acceleration (trend in QoQ % change)

3. Valuation - GARP (20%)
   - PEG ratio (P/E ÷ EPS Growth, ≤ 1.5 preferred)
   - EV/Sales vs revenue growth (Rule of 40 analysis)
   - EV/EBITDA position vs 5-year average
   - DCF intrinsic value vs market price (scenario-based IRR)

4. Momentum & Flows (15%)
   - 6M / 12M price momentum (position vs 52-week high)
   - 13F-based institutional ownership change (hedge fund net buys)
   - EPS estimate revision frequency (Beat & Raise track record)
   - Options market skew (downside hedge cost vs upside bet)

[DATA HANDLING PRINCIPLES]
Conduct simulation based on financial data and price history known through April 2025 + Q1 2026 guidance. Disclose ±5% error margins on all estimates. For non-U.S. ADRs (e.g., TSM, ASML), note fiscal-year timing differences from U.S. peers.

[OUTPUT REQUIREMENTS]

Part 1: Top 10 Stock Report (table format included)

- Ticker, company name, sector, AI Layer (1/2/3/4), current price (estimated), market cap
- AI revenue exposure, revenue growth, FCF margin, ROIC
- Sub-scores for all 4 categories + total score
- 3 core investment theses (AI super cycle narrative + quantitative metrics)
- 2 risk factors (export controls, ASIC competition, Capex cycle peak, etc.)
- 12-month target return + stop-loss level

Part 2: 4-Layer Exposure Analysis

- Weight and representative names by Layer
- Inter-layer correlation and diversification benefit
- Optimal weighting suggestion by AI cycle stage (Early Capex / Mid Build-out / Late Monetization)

Part 3: 10-Stock Equal-Weight Portfolio

- Weighted-average revenue growth forecast
- Estimated beta, volatility, Sharpe Ratio (3Y)
- Qualitative outperformance assessment vs NASDAQ-100
- Cycle inflection signals (e.g., GPU ASP decline, Hyperscaler Capex guidance cut, cloud growth deceleration)

[DISCLAIMER]
This analysis is for educational and informational purposes only. The AI super cycle is one of the largest capital cycles in history, but carries volatility risk comparable to the 2000 dot-com bubble. Actual investment decisions must be made through individual judgment and consultation with qualified professionals. Past revenue growth does not guarantee future growth.
```

---

## Prompt Architecture

### AI Value Chain 4-Layer Model

The prompt forces the LLM to evaluate *vertical-integration diversification* by decomposing the AI value chain into 4 layers:

| Layer | Function | Representative Names | AI Capex Beneficiary Stage |
| --- | --- | --- | --- |
| **Layer 1: Foundation** | Chips·Tools·Memory | NVDA, AVGO, TSM, ASML, MU, AMD | **Early Capex (2024-2026)** |
| **Layer 2: Infrastructure** | Hyperscalers·Cloud | MSFT, GOOGL, AMZN, META, ORCL | **Mid Build-out (2025-2028)** |
| **Layer 3: Enablers** | Power·Cooling·Network | VRT, ANET, ETN, GEV, NVT | **Mid Build-out (2025-2028)** |
| **Layer 4: Application** | Enterprise AI SW | PLTR, NOW, CRM, CRWD, ADBE | **Late Monetization (2027-2030)** |

### Scoring Weight Philosophy

| Dimension | Weight | Core Question |
| --- | --- | --- |
| **AI Revenue Exposure** | **35%** | "Is this company a *direct beneficiary* of the AI cycle?" |
| **Capital Efficiency & Momentum** | **30%** | "Is AI Capex translating into *real cash flow*?" |
| **Valuation (GARP)** | **20%** | "Is the price *reasonable relative to growth*?" |
| **Momentum & Flows** | **15%** | "Do *institutions and options markets agree*?" |

> **Difference vs Dividend Growth Prompt**: Dividend weight (40%) is removed; *AI Revenue Exposure (35%) + Capital Efficiency (30%)* take center stage. *Valuation weight is also reduced from 25% to 20%* — in late-cycle growth phases, *revenue acceleration generates more alpha* than multiple compression.

---

## Recommended Portfolio & Outlook

The 10 stocks the LLM is *expected to surface* (simulation-based):

### Layer 1: Foundation (4)

| # | Ticker | Company | Score | AI Exposure | 12M Target |
| --- | --- | --- | --- | --- | --- |
| 1 | **NVDA** | NVIDIA | **95** | 90%+ | +20~28% |
| 2 | **AVGO** | Broadcom | **90** | 60% | +15~22% |
| 3 | **TSM** | TSMC (ADR) | **92** | 50% | +18~24% |
| 4 | **ASML** | ASML Holding (ADR) | **87** | 45% | +12~18% |

### Layer 2: Infrastructure (3)

| # | Ticker | Company | Score | AI Exposure | 12M Target |
| --- | --- | --- | --- | --- | --- |
| 5 | **MSFT** | Microsoft | **91** | 35% (Azure AI) | +14~18% |
| 6 | **GOOGL** | Alphabet | **88** | 30% (GCP+TPU) | +13~17% |
| 7 | **META** | Meta Platforms | **89** | 40% (Ad AI) | +15~20% |

### Layer 3: Enablers (2)

| # | Ticker | Company | Score | AI Exposure | 12M Target |
| --- | --- | --- | --- | --- | --- |
| 8 | **VRT** | Vertiv Holdings | **86** | 70% (DC Power) | +18~25% |
| 9 | **ANET** | Arista Networks | **84** | 65% (DC Network) | +14~20% |

### Layer 4: Application (1)

| # | Ticker | Company | Score | AI Exposure | 12M Target |
| --- | --- | --- | --- | --- | --- |
| 10 | **PLTR** | Palantir | **78** | 80% (AIP) | +10~30% (high vol) |

### Portfolio Selection Rationale (Quant Lens)

1. **Vertical Hedge Structure**: When AI Capex slows, Layer 1 (semis) gets hit first, but Layer 4 (apps) recognizes revenue with a *2-3 year lag* → **Layer diversification absorbs cycle volatility**.

2. **Picks & Shovels of AI Capex**: 2026 Capex of the four major Hyperscalers is estimated at ~$400B. Roughly *60% flows into GPUs + data center infrastructure*, and the Layer 1 + Layer 3 weight (60%) of this portfolio sits directly on that capital flow.

3. **Momentum + GARP Blend**: Combines momentum leaders (NVDA, AVGO) with relatively-discounted names (GOOGL on GARP, META on ad AI acceleration) → **mitigates pure-momentum cycle risk**.

### 12-Month Market Scenarios

| Scenario | Probability | NASDAQ-100 Return | Portfolio Return |
| --- | --- | --- | --- |
| 🟢 **AI Capex Acceleration** (Hyperscaler guide-up) | 30% | +25% | **+32%** |
| 🟡 **Base Case** (Capex plateau + revenue acceleration) | 45% | +14% | **+18%** |
| 🟠 **Capex Slowdown** (1H'27 guide-down) | 20% | -3% | **-1%** |
| 🔴 **AI Bubble Burst** (Demand visibility cracks) | 5% | -28% | **-22%** |

> **Probability-Weighted Expected Return**: NASDAQ-100 +13.6% vs Portfolio **+18.4%** → **~+4.8pp Alpha**

### AI Cycle Inflection Signals (Watch List)

- ⚠️ **GPU ASP Decline**: NVDA Blackwell/Rubin generation ASP dropping ≥5% QoQ signals cycle peak
- ⚠️ **Hyperscaler Capex Guidance**: MSFT + GOOGL + META + AMZN aggregate Capex YoY growth slowing to ≤+10%
- ⚠️ **Data Center Vacancy**: Cushman & Wakefield North America data center vacancy bouncing back to ≥5%
- ⚠️ **AI Application Revenue**: ChatGPT/Copilot/Gemini ARR growth deceleration (currently +100% YoY)

---

## Output Utilization Guide

### Part 1 (Top 10 Stocks)

* **Score ≥ 85**: *Core position* candidates — 12-15% weight (NVDA, MSFT, TSM)
* **Score 75-85**: *Satellite positions* — 8-10% weight, quarterly review
* **Score < 75**: *Tactical positions* — ≤5% weight, momentum-driven entries

### Part 2 (Layer Exposure)

* **Early Capex Stage (2026-now)**: Layer 1 weight ↑ (40-50%)
* **Mid Build-out Stage (2027-2028)**: Layer 2+3 weight ↑ (50-60%)
* **Late Monetization Stage (2029+)**: Layer 4 weight ↑ (≥30%)

### Part 3 (Equal-Weight Portfolio)

* Expected revenue growth (weighted average): *18-25%* range
* Estimated beta: *1.25-1.40* (vs market beta 1.0)
* Outperformance vs NASDAQ-100 favored *while Hyperscaler Capex cycle persists*

---

## Token Efficiency Comparison

| Language | Input Tokens | Output Tokens | Total Cost (Claude Opus 4.7) |
| --- | --- | --- | --- |
| Korean | ~1,650 tokens | ~4,200 tokens | ~$0.092 |
| English | ~1,100 tokens | ~3,000 tokens | ~$0.064 |
| Chinese (Simplified) | ~1,200 tokens | ~3,300 tokens | ~$0.071 |

> **Recommendation**: For *recurring use (e.g., monthly rebalancing)*, English version saves *~$5-10 per year*. To get English analysis with Korean/Chinese summary, append *"Provide a 3-bullet summary in [language]"* at the end of the prompt.

---

## Considerations for International Investors

### Tax (U.S. Non-Resident Investors)

* **Dividend Withholding**: U.S. statutory 30%, reduced to 10-15% under most tax treaties (consult your country's treaty)
* **Capital Gains**: Generally taxed in your country of residence, not in the U.S. (W-8BEN required)
* **Estate Tax**: U.S. estate tax exposure for non-resident aliens with U.S. assets > $60K — consider trust structures for large positions

### Currency Hedging Decision

* **USD Exposure** (direct holdings): Benefits from dollar strength during AI cycle tailwinds
* **Hedged Vehicles** (currency-hedged ETFs): Eliminates FX volatility — recommended when local currency is at multi-year lows vs USD

### Regional ETF Alternatives

| ETF | Region | Tracking | Notes |
| --- | --- | --- | --- |
| QQQ | U.S. | NASDAQ-100 | Largest AI-tilted broad ETF |
| SOXX | U.S. | PHLX Semi | NVDA/AVGO/TSM/ASML concentration |
| SMH | U.S. | MVIS Semi | Similar to SOXX, lower fee |
| AIQ | U.S. | Global X AI & Tech | Pure AI thematic |

> All ETFs above are listed on U.S. exchanges. International investors should check local tax treaty implications and brokerage access.

---

## Risk Disclaimer

* This prompt's output is *educational/research-grade simulation*, not actual investment advice
* LLM data is based on *information known through April 2025*; *not real-time price/revenue data*
* Estimates carry *±5% error margins*; *re-validate against live market data* before action
* **The AI super cycle has stronger fundamentals than the 2000 dot-com bubble, but *post-Capex-peak drawdowns of -50%* are possible** — recall the SOX index's -82% crash in 2000-2002
* **Monitor 2026-2027 GPU ASP decline + Hyperscaler Capex deceleration signals** carefully
* **High-volatility names like PLTR and SMCI carry *80%+ implied vol*** — size positions conservatively
* Always *cross-validate LLM-generated recommendations* against independent data sources (SeekingAlpha, Morningstar, Bloomberg)

---

## Authorship

**Series**: vibe-investing — Awesome Claude Quant Scripts
**Related sub-strategies**:

* [Dividend Growth Prompt EN.MD](../Dividend%20growth%20prompt/Dividend_Growth_Prompt_EN.md) — *Opposite factor* prompt (dividend growth + value)
* [Long-Term Dividend Investing](../Long-Term%20Dividend%20Investing) — Code implementation for long-term holdings
* [DAT Quant Strategy](../DAT%20quant%20strategy) — Digital asset treasury company strategy

**Author**: Dennis Kim (HoKwang Kim / 김호광)

* Independent Researcher, Betalabs Inc. CEO, Former CEO of Cyworld Z
* ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
* GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
* Email: [gameworker@gmail.com](mailto:gameworker@gmail.com)

**Date**: May 2, 2026 v1.0
**License**: MIT (free use, attribution appreciated)

---

> *"In the AI super cycle, the picks and shovels matter more than the gold."*
