# Dividend Growth Stock Quant Script Using LLM (English)

> **US Stock Dividend Growth Strategy LLM Prompt**
> Find Top 10 stocks meeting *dividend growth + value* criteria from S&P 500 + NASDAQ-100, plus 3 dividend ETF recommendations and equal-weight portfolio simulation.

---

## Why This English Version?

**English prompts consume approximately 30% fewer tokens than Korean equivalents** for identical analytical output. Token-efficient design matters for:

* **Cost savings**: Repeated monthly/quarterly rebalancing analysis can save $5–10/year on Claude Opus 4.7 API
* **Faster response**: Less input tokens → lower latency
* **Larger context window**: More room for follow-up questions

| Metric | Korean prompt | English prompt | Savings |
| --- | --- | --- | --- |
| Input tokens | ~1,400 | ~950 | **−32%** |
| Output tokens | ~3,500 | ~2,500 | **−29%** |
| Cost (Claude Opus 4.7) | ~$0.075 | ~$0.052 | **−31%** |

**Tip**: For Korean output from English prompt, append `Respond in Korean.` at the end. This still saves ~25% tokens vs. fully Korean prompt.

---

## How to Use

1. Copy the entire prompt block below (use the copy button at top-right of the code block)
2. Paste it as-is into Claude / GPT-5 / Gemini or any LLM
3. The LLM will automatically generate Top 10 stocks + 3 ETFs + portfolio analysis

---

## The Prompt (English Version)

```text
[Role]
You are a portfolio manager and head of quantitative research at a top-tier global asset management firm, with 15 years of experience in dividend growth strategies. Your decision-making framework is based on the 'Duration-Premium' model, integrating dividend sustainability, growth potential, and current valuation to forecast 12-month total returns (dividends + capital gains).

Today's date is May 2, 2026. (Assumed as the analysis reference date.)

[Analysis Universe]
Screen S&P 500 and NASDAQ-100 constituents that simultaneously meet both criteria:

- Dividend growth screen: 5+ consecutive years of dividend increases, dividend CAGR >= 8%, payout ratio <= 60%
- Growth screen: 5-year average revenue growth >= 7%, consistent positive free cash flow (FCF)

Select 10 stocks total across the following sectors, avoiding concentration in any single sector:

- Consumer Staples
- Healthcare (Pharma, MedTech)
- Financials (Asset Management, Card Networks)
- Tech (Legacy Software, Semiconductor Equipment)
- Energy (Infrastructure, Midstream)
- Industrials (Defense, Commercial Services)

Additionally, recommend 3 USD-denominated dividend ETFs meeting:

- Expense ratio <= 0.35%
- AUM >= $10B
- 30-day SEC yield >= 2.5%
- Monthly or quarterly distributions
- Candidates: SCHD, VIG, DGRO, VYM, DGRW, JEPI, JEPQ, etc.

[Scoring Framework — 100 points per stock]

1. Dividend Sustainability (40% weight)
   - Payout ratio (last 4 quarters; lower than 40% scores higher)
   - FCF dividend coverage (FCF / dividend > 1.5)
   - Leverage (Debt/EBITDA < 2.5x)
   - Interest coverage ratio + buyback program coexistence

2. Dividend Growth Momentum (35%)
   - 3yr / 5yr / 10yr dividend CAGR
   - Dividend growth vs. revenue and EPS growth (payout ratio stabilization trend)
   - Price pattern around dividend declarations + ex-div recovery speed

3. Valuation and Flows (25%)
   - Forward P/E, P/B, EV/EBITDA discount vs. 5-year averages
   - Dividend yield spread vs. 10-year Treasury
   - Institutional ownership change (13F-based), short interest, implied volatility

[Data Handling]
Given limited real-time data access, run reasonable simulations based on financial data and price history known up to April 2025. Annotate all estimates with a +/-5% confidence range.

[Output Requirements]

Part 1: Top 10 Stocks Report (include table format)
- Ticker, Company name, Sector, Current price (estimate), Dividend yield, 5yr Dividend CAGR, Payout ratio
- Sub-scores for Sustainability, Growth Momentum, Valuation + Total score
- 3 key investment theses (dividend growth narrative + quantitative metrics)
- 2 risk factors (sector cycle, regulatory, etc.)
- 12-month target dividend + capital return + stop-loss threshold

Part 2: 3 Recommended Dividend ETFs
- Ticker, ETF name, Issuer, Expense ratio, AUM, 30-day SEC yield, Annual distribution rate, Monthly/quarterly distribution
- Top 5 holdings + sector breakdown
- Suitability as a dividend growth ETF + role within portfolio

Part 3: Equal-Weight Portfolio of 10 Stocks
- Pre-tax expected dividend yield
- Estimated Sharpe ratio + MDD (Maximum Drawdown) based on 3-year historical data
- Qualitative assessment of potential outperformance vs. S&P 500

[Disclaimer]
This analysis is for educational and informational purposes only. Actual investment decisions must reflect personal judgment and consultation with qualified professionals. Past dividend records do not guarantee future dividends.
```

---

## Prompt Structure Explanation

### Duration-Premium Model

This prompt requires the LLM to integrate three dimensions:

| Dimension | Weight | Core Question |
| --- | --- | --- |
| **Dividend Sustainability** | **40%** | "Can this company *continue paying* dividends next year?" |
| **Dividend Growth Momentum** | **35%** | "Can this company *keep growing* dividends like before?" |
| **Valuation & Flows** | **25%** | "Is the *current price reasonable* for entry?" |

### 6-Sector Diversification Strategy

To avoid sector concentration, select *1-2 stocks from each of 6 sectors*:

1. **Consumer Staples** — Defensive dividends (P&G, KO classics)
2. **Healthcare** — Pharma/MedTech (JNJ, ABBV, MDT)
3. **Financials** — Asset management/card networks (V, MA, BLK — capital-light)
4. **Tech** — Legacy software/semi equipment (MSFT, AVGO, TXN)
5. **Energy** — Infrastructure/midstream (EPD, ET — MLPs)
6. **Industrials** — Defense/commercial services (LMT, RTX, WM)

### ETF Recommendation Criteria

| Criterion | Threshold |
| --- | --- |
| Expense ratio | <= 0.35% |
| AUM | >= $10B |
| 30-day SEC Yield | >= 2.5% |
| Distribution frequency | Monthly or quarterly |

**Top candidates**: SCHD (Schwab Dividend Equity), VIG (Vanguard Dividend Appreciation), DGRO (iShares Core Dividend Growth), VYM (Vanguard High Dividend Yield), DGRW (WisdomTree Quality Dividend Growth), JEPI (JPMorgan Equity Premium Income), JEPQ (JPMorgan Nasdaq Equity Premium Income)

---

## Output Interpretation Guide

### Part 1 (Top 10 Stocks)

| Total Score | Position Type | Holding Period |
| --- | --- | --- |
| **>= 70 points** | Core position | 5-10 years |
| **60-70 points** | Satellite position | 1-3 years (re-evaluate) |
| **< 60 points** | Watchlist | Wait for price correction |

### Part 2 (3 ETFs)

* **Portfolio core (60-70%)**: SCHD or DGRO type — *Dividend Growth + Value* integrated
* **Yield enhancement (20-30%)**: VYM or JEPI type — *High Yield* focus
* **International diversification (10%)**: This prompt is US-only; consider VXUS for global exposure

### Part 3 (Equal-Weight Portfolio)

* Pre-tax expected dividend yield: typically *2.5-4.0%* range
* US tax: 15% withholding; consider domestic tax laws separately
* Outperformance vs. S&P 500 favored in *high-rate regimes* (2025-2026 environment)

---

## Token Efficiency Strategy

### Use Cases for Each Language

| Use Case | Recommended Language |
| --- | --- |
| Single one-time analysis | Korean (full Korean output) |
| **Monthly/quarterly rebalancing** | **English (cost saving)** |
| Mixed language team | English prompt + "Respond in Korean" |
| API automation pipeline | English (token-cost-sensitive) |
| Educational learning | Korean (intuitive understanding) |

### Hybrid Approach

For maximum token efficiency with Korean readability:

```text
[Append at the end of the English prompt above]

Output format: Use the English prompt structure but provide all explanations and narrative analysis in Korean. Keep ticker symbols, ETF names, and metric labels in English.
```

This hybrid saves ~25% tokens compared to fully Korean prompt while preserving Korean readability.

---

## Multi-LLM Compatibility

| LLM | Compatibility | Notes |
| --- | --- | --- |
| Claude Opus 4.7 | Excellent | Best for nuanced narrative + risk analysis |
| Claude Sonnet 4.6 | Good | Faster, lower cost; suitable for routine rebalancing |
| GPT-5 / GPT-5.4 | Good | Strong quantitative reasoning; verify dividend data accuracy |
| Gemini 3.x | Good | Best for accessing Google Finance integration (when available) |
| DeepSeek V3.1/V4 | Excellent for cost | +46% in Alpha Arena Season 1; strong cost efficiency |
| Qwen3 Max | Good | Lower cost alternative for high-frequency rebalancing |
| Local LLM (Ollama) | Limited | Acceptable for prompt iteration; lacks fresh financial data |

---

## Risk Disclosures

* The output is *educational/research simulation* only — *not investment advice*
* LLM data reflects *information known up to April 2025*; *not real-time prices or dividends*
* Estimates have *+/-5% error range*; *cross-verify with independent data sources* (SeekingAlpha, Morningstar, Yahoo Finance) before trading
* **Past dividend records do not guarantee future dividends** — even Dividend Aristocrats can cut dividends (e.g., GE 2008-2009)
* **Dividend growth stocks can suffer 50%+ drawdowns during recessions + debt crises** — long-only systematic risk acknowledgment required
* Korean residents must separately verify *foreign exchange law + capital gains tax + comprehensive income tax*
* Cross-verify LLM-generated recommendations with *independent data sources* before live trading
* Tax implications vary by jurisdiction; consult a qualified tax advisor

---

## Author Information

**Series**: vibe-investing — Awesome Claude Quant Scripts
**Related sub-strategies**:
* [Long-Term Dividend Investing](../Long-Term%20Dividend%20Investing) — Code implementation companion
* [DAT Quant Strategy](../DAT%20quant%20strategy) — Digital Asset Treasury alternative
* [Declining Stock Quant Script Using LLM](../Declining%20Stock%20Quant%20Script%20Using%20LLM) — Opposite strategy (downside betting + inverse ETFs)

**Author**: HoKwang Kim (Dennis Kim)
- Independent Researcher, Betalabs Inc. CEO, Former Cyworld Z CEO
- ORCID: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- GitHub: [@gameworkerkim](https://github.com/gameworkerkim)
- Email: [gameworker@gmail.com](mailto:gameworker@gmail.com)

**Created**: May 2, 2026, v1.0
**License**: MIT (free use; attribution recommended)

---

> *"Dividend growth is not a strategy. It is a discipline."*
