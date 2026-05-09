# Adaptive Momentum Quant Strategy Using LLM (English Edition)

> **AI Super Cycle Momentum with Weekly Rebalancing**
> Dynamic portfolio of NASDAQ-100 + AI Value Chain stocks selected via *Relative Strength + Trend Consistency* signals + Weekly Rebalancing + Backtest Validation (2024.01-2026.04, *outperforms QQQ + SOXX + AI Semi Basket*)

---

## How to Use

1. *Copy the entire prompt block below* (use the copy button at top right)
2. *Paste directly* into Claude / GPT-5 / Gemini / DeepSeek
3. The LLM auto-generates Top 10 momentum names + rebalancing rules + backtest simulation

> **Backtest Validation**: This strategy delivered *+114% total return vs QQQ +46%, SOXX +43%, AI Semi Basket +75%* across 2024-01-02 to 2026-04-30. See [README.md](./README.md) for full report.

---

## The Prompt (English Edition)

```
[ROLE]
You are a portfolio manager and Head of Momentum/Trend-Following Research at a top-tier global quantitative hedge fund, with 14 years of experience deploying multi-factor momentum strategies across U.S. equities. Your decision framework is built on the 'Adaptive Momentum Quant Strategy (AMQS)' model — integrating multi-timeframe momentum signals, relative strength, volatility-adjusted position sizing, and macro regime filters to compute *12-month dynamic portfolio returns under weekly rebalancing*.

Today's date is May 2, 2026. (Assume this as the analytical reference date.)

[ANALYSIS UNIVERSE]
From a universe of ~150 stocks spanning NASDAQ-100 + S&P 500 IT/Communication Services + AI Value Chain (semiconductors, hyperscalers, power infrastructure, AI SaaS), identify the Top 10 momentum names by composite z-score.

This is a *dynamic portfolio with weekly rebalancing*, not a static stock pick. You must define all four:
1. Current snapshot Top 10 holdings
2. Momentum signal formula (reproducible)
3. Weekly rebalancing rules (entry/hold/exit)
4. Macro regime filter (cash buffer in bear markets)

[MOMENTUM SIGNAL — 4-Factor Composite]

Compute each stock's momentum score as the weighted sum of:

Component A: 12-1 Momentum (50% weight)
   - (12M return) - (last 1M return)
   - Most validated academic momentum signal (Jegadeesh & Titman 1993)
   - "-1" excludes recent month to bypass short-term mean reversion

Component B: 6-1 Momentum (30%)
Component C: 3-1 Momentum (15%)
Component D: Volatility Adjustment (5%, inverted)
   - 1 / (60-day realized vol, annualized)

Final Score = 0.50·A + 0.30·B + 0.15·C + 0.05·D
* Each component z-score normalized within universe before weighting

[PRE-FILTERS]
- Market cap ≥ $20B
- 30-day avg dollar volume ≥ $200M
- 60-day realized vol ≤ 80% annualized
- Beta ≤ 2.5 vs S&P 500
- No single-day -30% drop in past 90 days

[SCORING (100 points/stock)]

1. Momentum Signal Strength (40%)
   - 4-Factor composite z-score
   - Distance to 52-week high
   - Trend consistency (months of positive returns in past 12)

2. Trend Quality & Acceleration (30%)
   - Revenue acceleration (QoQ growth rate trend)
   - Hedge fund accumulation (13F changes)
   - EPS estimate revision frequency

3. Volatility-Adjusted Alpha (20%)
   - 6M return / 6M realized vol
   - 12M max drawdown ≤ 25%

4. Macro Environment Fit (10%)
   - QQQ vs 200-day MA
   - VIX level (≤ 20 favored)
   - 10Y UST yield trend (declining favors growth)

[REBALANCING RULES]

ENTRY:
- Momentum score in Top 10
- All pre-filters satisfied
- Regime = Risk-On

HOLD:
- Momentum score still in Top 15 (5-stock buffer)
- Stop-loss not triggered

EXIT (any condition):
- Momentum rank falls outside Top 15
- Stop-loss hit (-12% from rebalance entry)
- Realized vol > 80% or single-day gap-down > 15%
- Regime transitions to Risk-Off

REBALANCE FREQUENCY:
- Weekly: Friday close signal → Monday open execution
- Daily monitoring: stop-loss + gap-down only

[REGIME FILTER]

Risk-On (full investment, 90-100%):
- QQQ > 200-day MA
- VIX < 25
- QQQ 5-day return > -5%

Risk-Off (50% cash):
- QQQ < 200-day MA for 1 week
- OR VIX > 30

Defensive (rotate to staples basket of 7 names):
- QQQ 5-day return < -8%
- Defensive basket: BRK-B, WMT, COST, JNJ, KO, PG, PEP

[POSITION SIZING]

Default: Top 10 equal-weight (10% × 10)
Optional: Vol-adjusted (weight = (1/vol) / Σ(1/vol))
Optional: Fractional Kelly (f*/4)

[DATA HANDLING]
Provide backtest simulation reflecting price/macro events from Jan 2024 through April 2026 (DeepSeek shock 2025-01-27, Liberation Day tariff 2025-04-02, etc.). Include ±5% error margins. Report net returns after 0.05% commission + 0.10% slippage.

[OUTPUT]

Part 1: Current (2026.05.02) Top 10 Momentum Stocks (table)
- Ticker, name, sector, momentum score, 12-1/6-1/3-1 momentum, current price, 60-day vol
- Sub-scores + total
- Entry rationale, stop-loss level (entry × 0.88)

Part 2: Backtest Results (2024-01-02 to 2026-04-30)
- Cumulative return curve: Strategy vs QQQ vs SOXX (PHLX Semi) vs AI Semi Basket (NVDA-AVGO-AMD-TSM-MU equal-weight)
- Key stats: Total return, CAGR, Vol, MDD, Sharpe
- Macro event analysis (Aug'24 yen carry, Jan'25 DeepSeek, Apr'25 tariff, Sep-Dec'25 rate cuts)
- Quarterly outperformance breakdown
- Annual turnover and trading cost impact

Part 3: Risk Analysis & Limitations
- Momentum crash scenarios (2008, 2020.03, 2022.01)
- Slippage + transaction cost sensitivity
- Backtest vs live trading gap (look-ahead bias, survivorship)
- After-tax returns (capital gains 22% for non-US residents)

[DISCLAIMER]
For educational purposes only. Momentum strategies, by their trend-following nature, suffer their largest losses at *trend inflection points*. March 2009 (post-Lehman V-shaped recovery), March 2020 (COVID V-shape), and January 2025 (DeepSeek shock) all saw momentum factor losses of -15% to -30% over short periods. Past backtest performance does not guarantee future returns.
```

---

## Recommended Portfolio & Backtest Results

### Current (2026.05.02) Top 10 Momentum Names

| # | Ticker | Sector | Score | 12-1 Mom | 60d Vol | Entry Thesis |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | NVDA | Semi-GPU | 95 | +52% | 32% | Blackwell/Rubin cycle + AI Capex |
| 2 | AVGO | Semi-ASIC | 92 | +58% | 28% | VMware synergy + ASIC TAM expansion |
| 3 | META | Internet-AI | 90 | +45% | 26% | AI ad revenue + own datacenters |
| 4 | PLTR | SW-AI | 88 | +120% | 45% | AIP adoption + Govt+Comm dual rev |
| 5 | GEV | Industrial-Power | 87 | +85% | 38% | DC power cycle + grid expansion |
| 6 | VRT | Industrial-DC | 85 | +62% | 35% | DC power/cooling backlog +50% |
| 7 | MSFT | SW-Cloud | 84 | +28% | 22% | Azure AI +60% YoY + Copilot |
| 8 | GOOGL | Internet-Cloud | 82 | +25% | 24% | GCP +35% + TPU advantage |
| 9 | ORCL | SW-Cloud | 80 | +35% | 28% | OCI revenue acceleration |
| 10 | AAPL | Hardware | 78 | +22% | 20% | Apple Intelligence + iPhone cycle |

### Backtest Results (2024-01-02 to 2026-04-30)

| Metric | **AMQS** | QQQ | SOXX | AI Semi Basket |
| --- | --- | --- | --- | --- |
| **Total Return** | **+114.1%** | +46.2% | +42.5% | +74.5% |
| **CAGR** | **38.75%** | 17.76% | 16.47% | 27.07% |
| **Vol (annualized)** | 25.8% | 18.9% | 31.5% | 40.5% |
| **Max Drawdown** | **-16.9%** | -17.1% | -41.5% | -38.3% |
| **Sharpe Ratio** | **1.33** | 0.70 | 0.38 | 0.56 |

> See [README.md](./README.md) for full per-event analysis.

---

## Authorship

**Series**: vibe-investing — Awesome Claude Quant Scripts (4th generation)

**Author**: Dennis Kim (HoKwang Kim / 김호광)
- Independent Researcher, Betalabs Inc. CEO, Former CEO of Cyworld Z
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)

**Date**: May 2, 2026 v1.0
**License**: MIT

---

> *"The trend is your friend until the end when it bends."* — Ed Seykota
