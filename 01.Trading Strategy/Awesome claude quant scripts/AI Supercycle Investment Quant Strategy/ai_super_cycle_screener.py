#!/usr/bin/env python3
"""
AI Super Cycle Quant Screener
==============================
Screens S&P 500 + NASDAQ-100 constituents for AI Super Cycle exposure
across the 4-layer AI Value Chain (Foundation / Infrastructure / Enablers / Application).

Author: Dennis Kim (HoKwang Kim / 김호광)
GitHub: https://github.com/gameworkerkim/vibe-investing
License: MIT
Version: 1.0 (2026-05-02)

Usage:
    python ai_super_cycle_screener.py                    # Run with default universe
    python ai_super_cycle_screener.py --layer 1          # Filter by AI Layer
    python ai_super_cycle_screener.py --min-score 80     # Minimum score filter
    python ai_super_cycle_screener.py --output custom.csv

Dependencies:
    pip install yfinance pandas numpy tabulate
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance is required. Install with: pip install yfinance")
    sys.exit(1)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# -------------------------------------------------------------------
# AI Value Chain Universe
# -------------------------------------------------------------------
# Curated AI-exposed names across the 4-layer AI Value Chain.
# Manually classified — yfinance does not expose AI-specific exposure metadata,
# so the layer mapping reflects industry research and reporting segments.
# -------------------------------------------------------------------

AI_UNIVERSE: Dict[str, Dict] = {
    # Layer 1: Foundation - chips, foundry, equipment, memory
    "NVDA":  {"layer": 1, "name": "NVIDIA",            "ai_pct": 90, "subsegment": "GPU"},
    "AVGO":  {"layer": 1, "name": "Broadcom",          "ai_pct": 60, "subsegment": "ASIC/Network"},
    "TSM":   {"layer": 1, "name": "TSMC (ADR)",        "ai_pct": 50, "subsegment": "Foundry"},
    "ASML":  {"layer": 1, "name": "ASML (ADR)",        "ai_pct": 45, "subsegment": "EUV Equipment"},
    "AMD":   {"layer": 1, "name": "AMD",               "ai_pct": 40, "subsegment": "GPU/CPU"},
    "MU":    {"layer": 1, "name": "Micron",            "ai_pct": 45, "subsegment": "HBM Memory"},
    "LRCX":  {"layer": 1, "name": "Lam Research",      "ai_pct": 35, "subsegment": "Etch Equipment"},
    "AMAT":  {"layer": 1, "name": "Applied Materials", "ai_pct": 35, "subsegment": "Semi Equipment"},
    "KLAC":  {"layer": 1, "name": "KLA",               "ai_pct": 35, "subsegment": "Process Control"},
    "MRVL":  {"layer": 1, "name": "Marvell",           "ai_pct": 50, "subsegment": "Custom Silicon"},

    # Layer 2: Infrastructure - hyperscalers
    "MSFT":  {"layer": 2, "name": "Microsoft",         "ai_pct": 35, "subsegment": "Azure"},
    "GOOGL": {"layer": 2, "name": "Alphabet",          "ai_pct": 30, "subsegment": "GCP/TPU"},
    "META":  {"layer": 2, "name": "Meta Platforms",    "ai_pct": 40, "subsegment": "Ad AI"},
    "AMZN":  {"layer": 2, "name": "Amazon",            "ai_pct": 25, "subsegment": "AWS"},
    "ORCL":  {"layer": 2, "name": "Oracle",            "ai_pct": 30, "subsegment": "OCI"},

    # Layer 3: Enablers - power, cooling, network
    "VRT":   {"layer": 3, "name": "Vertiv",            "ai_pct": 70, "subsegment": "DC Power/Cooling"},
    "ANET":  {"layer": 3, "name": "Arista Networks",   "ai_pct": 65, "subsegment": "DC Network"},
    "ETN":   {"layer": 3, "name": "Eaton",             "ai_pct": 35, "subsegment": "Power Mgmt"},
    "GEV":   {"layer": 3, "name": "GE Vernova",        "ai_pct": 25, "subsegment": "Grid/Power"},
    "NVT":   {"layer": 3, "name": "nVent Electric",    "ai_pct": 30, "subsegment": "Cooling/Enclosures"},
    "SMCI":  {"layer": 3, "name": "Super Micro",       "ai_pct": 80, "subsegment": "AI Servers"},

    # Layer 4: Application - enterprise AI software
    "PLTR":  {"layer": 4, "name": "Palantir",          "ai_pct": 80, "subsegment": "AIP Platform"},
    "NOW":   {"layer": 4, "name": "ServiceNow",        "ai_pct": 30, "subsegment": "Enterprise AI"},
    "CRM":   {"layer": 4, "name": "Salesforce",        "ai_pct": 25, "subsegment": "Agentforce"},
    "CRWD":  {"layer": 4, "name": "CrowdStrike",       "ai_pct": 50, "subsegment": "AI Security"},
    "ADBE":  {"layer": 4, "name": "Adobe",             "ai_pct": 25, "subsegment": "Generative AI"},
}


# -------------------------------------------------------------------
# Screening Configuration
# -------------------------------------------------------------------

@dataclass
class ScreeningConfig:
    """Configuration thresholds for the AI Super Cycle screener."""
    min_market_cap_b: float = 20.0       # ≥ $20B
    min_revenue_growth_pct: float = 12.0  # ≥ 12% YoY
    min_fcf_margin_pct: float = 8.0       # ≥ 8% (relaxed for early-Capex names)
    min_ai_exposure_pct: float = 15.0     # ≥ 15% AI revenue exposure
    min_avg_dollar_volume_m: float = 500.0  # ≥ $500M daily liquidity
    min_total_score: float = 0.0          # No floor by default


@dataclass
class StockMetrics:
    """Container for fetched + computed metrics per stock."""
    ticker: str
    name: str
    layer: int
    subsegment: str
    ai_pct: float

    # Live market data (filled by yfinance)
    current_price: float = 0.0
    market_cap_b: float = 0.0
    avg_dollar_volume_m: float = 0.0

    # Fundamentals
    revenue_growth_pct: float = 0.0
    fcf_margin_pct: float = 0.0
    forward_pe: float = 0.0
    eps_growth_pct: float = 0.0
    roic_pct: float = 0.0  # approximated from ROE

    # Momentum
    price_6m_pct: float = 0.0
    price_12m_pct: float = 0.0
    pct_from_52w_high: float = 0.0

    # Computed scores
    score_ai_exposure: float = 0.0
    score_capital_efficiency: float = 0.0
    score_valuation: float = 0.0
    score_momentum: float = 0.0
    total_score: float = 0.0

    # Pass/fail flag
    passes_screen: bool = False
    fail_reasons: List[str] = field(default_factory=list)


# -------------------------------------------------------------------
# Data Fetching
# -------------------------------------------------------------------

def fetch_stock_metrics(ticker: str, meta: Dict) -> Optional[StockMetrics]:
    """Pull market data + fundamentals for a single ticker via yfinance."""
    try:
        tk = yf.Ticker(ticker)
        info = tk.info

        # Skip if no fundamental data
        if not info or info.get("regularMarketPrice") is None:
            print(f"  ⚠ {ticker}: no market data, skipping")
            return None

        m = StockMetrics(
            ticker=ticker,
            name=meta["name"],
            layer=meta["layer"],
            subsegment=meta["subsegment"],
            ai_pct=meta["ai_pct"],
        )

        # Price + market cap
        m.current_price = float(info.get("regularMarketPrice") or info.get("currentPrice") or 0)
        m.market_cap_b = float(info.get("marketCap") or 0) / 1e9

        # Dollar volume (avg 30d via history)
        hist = tk.history(period="3mo", auto_adjust=True)
        if not hist.empty:
            m.avg_dollar_volume_m = float((hist["Close"] * hist["Volume"]).mean()) / 1e6

        # Fundamentals from info dict
        m.revenue_growth_pct = float(info.get("revenueGrowth") or 0) * 100
        m.forward_pe = float(info.get("forwardPE") or 0)
        m.eps_growth_pct = float(info.get("earningsGrowth") or 0) * 100

        # FCF Margin = FCF / Revenue
        fcf = float(info.get("freeCashflow") or 0)
        revenue = float(info.get("totalRevenue") or 1)
        m.fcf_margin_pct = (fcf / revenue) * 100 if revenue > 0 else 0

        # ROIC proxy: use ROE since ROIC is not directly available
        m.roic_pct = float(info.get("returnOnEquity") or 0) * 100

        # Momentum from price history
        hist_1y = tk.history(period="1y", auto_adjust=True)
        if len(hist_1y) > 0:
            current = m.current_price
            price_6m = float(hist_1y["Close"].iloc[-126]) if len(hist_1y) > 126 else float(hist_1y["Close"].iloc[0])
            price_12m = float(hist_1y["Close"].iloc[0])
            high_52w = float(hist_1y["High"].max())

            m.price_6m_pct = ((current / price_6m) - 1) * 100 if price_6m > 0 else 0
            m.price_12m_pct = ((current / price_12m) - 1) * 100 if price_12m > 0 else 0
            m.pct_from_52w_high = ((current / high_52w) - 1) * 100 if high_52w > 0 else 0

        return m

    except Exception as exc:
        print(f"  ✗ {ticker}: fetch error — {type(exc).__name__}: {exc}")
        return None


# -------------------------------------------------------------------
# Scoring Engine
# -------------------------------------------------------------------

def score_ai_exposure(m: StockMetrics) -> float:
    """Score 0-35 based on AI revenue exposure + sub-segment quality."""
    # Base score from AI revenue percentage
    base = min(m.ai_pct / 100 * 30, 30)

    # Bonus for high-conviction segments
    bonus = 0
    if m.layer == 1 and m.ai_pct >= 60:
        bonus = 5  # Pure-play semis
    elif m.layer == 2 and m.ai_pct >= 30:
        bonus = 4  # Hyperscaler
    elif m.layer == 3 and m.ai_pct >= 60:
        bonus = 4  # Pure-play enabler
    elif m.layer == 4 and m.ai_pct >= 70:
        bonus = 3  # Pure AI app
    else:
        bonus = 2

    return min(base + bonus, 35)


def score_capital_efficiency(m: StockMetrics) -> float:
    """Score 0-30 based on FCF margin, revenue growth, ROIC, EPS growth."""
    score = 0.0

    # FCF margin (0-8 points)
    if m.fcf_margin_pct >= 30: score += 8
    elif m.fcf_margin_pct >= 20: score += 6
    elif m.fcf_margin_pct >= 10: score += 4
    elif m.fcf_margin_pct >= 5: score += 2

    # Revenue growth (0-9 points)
    if m.revenue_growth_pct >= 40: score += 9
    elif m.revenue_growth_pct >= 25: score += 7
    elif m.revenue_growth_pct >= 15: score += 5
    elif m.revenue_growth_pct >= 8: score += 3

    # ROIC proxy (0-7 points)
    if m.roic_pct >= 30: score += 7
    elif m.roic_pct >= 20: score += 5
    elif m.roic_pct >= 10: score += 3
    elif m.roic_pct >= 5: score += 1

    # EPS growth momentum (0-6 points)
    if m.eps_growth_pct >= 30: score += 6
    elif m.eps_growth_pct >= 15: score += 4
    elif m.eps_growth_pct >= 5: score += 2

    return min(score, 30)


def score_valuation(m: StockMetrics) -> float:
    """Score 0-20 based on Forward P/E + PEG + GARP factors."""
    score = 0.0

    if m.forward_pe <= 0:
        return 10  # Neutral if data unavailable

    # PEG-style scoring (0-12 points)
    if m.eps_growth_pct > 0:
        peg = m.forward_pe / m.eps_growth_pct
        if peg <= 1.0: score += 12
        elif peg <= 1.5: score += 9
        elif peg <= 2.0: score += 6
        elif peg <= 3.0: score += 3
    else:
        # Use Forward P/E alone
        if m.forward_pe <= 25: score += 8
        elif m.forward_pe <= 35: score += 5
        elif m.forward_pe <= 50: score += 2

    # Forward P/E absolute (0-8 points)
    if m.forward_pe <= 20: score += 8
    elif m.forward_pe <= 30: score += 6
    elif m.forward_pe <= 40: score += 4
    elif m.forward_pe <= 60: score += 2

    return min(score, 20)


def score_momentum(m: StockMetrics) -> float:
    """Score 0-15 based on price momentum + 52w high proximity."""
    score = 0.0

    # 12-month return (0-7 points)
    if m.price_12m_pct >= 50: score += 7
    elif m.price_12m_pct >= 30: score += 5
    elif m.price_12m_pct >= 10: score += 3
    elif m.price_12m_pct >= 0: score += 1

    # 6-month return (0-5 points)
    if m.price_6m_pct >= 25: score += 5
    elif m.price_6m_pct >= 10: score += 3
    elif m.price_6m_pct >= 0: score += 1

    # Distance from 52w high (0-3 points) — closer is better
    if m.pct_from_52w_high >= -5: score += 3
    elif m.pct_from_52w_high >= -15: score += 2
    elif m.pct_from_52w_high >= -25: score += 1

    return min(score, 15)


def compute_scores(m: StockMetrics) -> StockMetrics:
    """Run all scoring functions + total."""
    m.score_ai_exposure = round(score_ai_exposure(m), 1)
    m.score_capital_efficiency = round(score_capital_efficiency(m), 1)
    m.score_valuation = round(score_valuation(m), 1)
    m.score_momentum = round(score_momentum(m), 1)
    m.total_score = round(
        m.score_ai_exposure
        + m.score_capital_efficiency
        + m.score_valuation
        + m.score_momentum,
        1,
    )
    return m


# -------------------------------------------------------------------
# Screening Logic
# -------------------------------------------------------------------

def apply_screen(m: StockMetrics, cfg: ScreeningConfig) -> StockMetrics:
    """Mark pass/fail + record reasons."""
    m.fail_reasons = []

    if m.market_cap_b < cfg.min_market_cap_b:
        m.fail_reasons.append(f"market_cap<${cfg.min_market_cap_b}B")
    if m.revenue_growth_pct < cfg.min_revenue_growth_pct:
        m.fail_reasons.append(f"rev_growth<{cfg.min_revenue_growth_pct}%")
    if m.fcf_margin_pct < cfg.min_fcf_margin_pct:
        m.fail_reasons.append(f"fcf_margin<{cfg.min_fcf_margin_pct}%")
    if m.ai_pct < cfg.min_ai_exposure_pct:
        m.fail_reasons.append(f"ai_exposure<{cfg.min_ai_exposure_pct}%")
    if m.avg_dollar_volume_m < cfg.min_avg_dollar_volume_m:
        m.fail_reasons.append(f"liquidity<${cfg.min_avg_dollar_volume_m}M")
    if m.total_score < cfg.min_total_score:
        m.fail_reasons.append(f"total_score<{cfg.min_total_score}")

    m.passes_screen = len(m.fail_reasons) == 0
    return m


# -------------------------------------------------------------------
# Main Pipeline
# -------------------------------------------------------------------

def run_screener(
    layer_filter: Optional[int] = None,
    min_score: float = 0.0,
    output_csv: str = "ai_super_cycle_screen_results.csv",
    config: Optional[ScreeningConfig] = None,
) -> pd.DataFrame:
    """Execute the full AI Super Cycle screener."""
    cfg = config or ScreeningConfig()
    cfg.min_total_score = max(cfg.min_total_score, min_score)

    print("=" * 70)
    print(f"  AI Super Cycle Quant Screener  (Run: {datetime.now():%Y-%m-%d %H:%M})")
    print("=" * 70)
    print(f"Universe size:         {len(AI_UNIVERSE)} tickers")
    print(f"Layer filter:          {'Layer ' + str(layer_filter) if layer_filter else 'All Layers'}")
    print(f"Min total score:       {cfg.min_total_score}")
    print(f"Min market cap:        ${cfg.min_market_cap_b}B")
    print(f"Min revenue growth:    {cfg.min_revenue_growth_pct}% YoY")
    print(f"Min FCF margin:        {cfg.min_fcf_margin_pct}%")
    print(f"Min AI exposure:       {cfg.min_ai_exposure_pct}%")
    print("=" * 70)

    results: List[StockMetrics] = []

    for ticker, meta in AI_UNIVERSE.items():
        if layer_filter is not None and meta["layer"] != layer_filter:
            continue

        print(f"  → fetching {ticker} ({meta['name']})...")
        m = fetch_stock_metrics(ticker, meta)
        if m is None:
            continue
        m = compute_scores(m)
        m = apply_screen(m, cfg)
        results.append(m)

    if not results:
        print("\nNo stocks fetched. Check network connectivity.")
        return pd.DataFrame()

    # Build dataframe
    rows = []
    for m in results:
        rows.append({
            "ticker": m.ticker,
            "name": m.name,
            "layer": f"Layer {m.layer}",
            "subsegment": m.subsegment,
            "price": round(m.current_price, 2),
            "mcap_$B": round(m.market_cap_b, 1),
            "ai_pct": m.ai_pct,
            "rev_growth_%": round(m.revenue_growth_pct, 1),
            "fcf_margin_%": round(m.fcf_margin_pct, 1),
            "roe_%": round(m.roic_pct, 1),
            "fwd_PE": round(m.forward_pe, 1),
            "ret_6m_%": round(m.price_6m_pct, 1),
            "ret_12m_%": round(m.price_12m_pct, 1),
            "score_ai": m.score_ai_exposure,
            "score_cap": m.score_capital_efficiency,
            "score_val": m.score_valuation,
            "score_mom": m.score_momentum,
            "total_score": m.total_score,
            "passes": "✓" if m.passes_screen else "✗",
            "fail_reasons": "; ".join(m.fail_reasons) if m.fail_reasons else "",
        })

    df = pd.DataFrame(rows).sort_values("total_score", ascending=False)

    # Display
    print("\n" + "=" * 70)
    print("  Screening Results (sorted by total score)")
    print("=" * 70)
    display_cols = ["ticker", "name", "layer", "ai_pct", "rev_growth_%",
                    "fcf_margin_%", "fwd_PE", "total_score", "passes"]
    try:
        from tabulate import tabulate
        print(tabulate(df[display_cols], headers="keys", tablefmt="github", showindex=False))
    except ImportError:
        print(df[display_cols].to_string(index=False))

    # Save
    df.to_csv(output_csv, index=False)
    print(f"\n✓ Full results saved to: {output_csv}")

    # Summary
    passes = df[df["passes"] == "✓"]
    print(f"\n  Total fetched:       {len(df)}")
    print(f"  Passed all filters:  {len(passes)}")
    print(f"  Score ≥ 80:          {len(df[df['total_score'] >= 80])}")
    print(f"  Score ≥ 70:          {len(df[df['total_score'] >= 70])}")

    # Layer breakdown
    print("\n  Layer breakdown (passes only):")
    for layer in [1, 2, 3, 4]:
        layer_passes = passes[passes["layer"] == f"Layer {layer}"]
        print(f"    Layer {layer}: {len(layer_passes)} names "
              f"(avg score {layer_passes['total_score'].mean():.1f})"
              if len(layer_passes) > 0
              else f"    Layer {layer}: 0 names")

    return df


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI Super Cycle Quant Screener for U.S. equities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_super_cycle_screener.py
  python ai_super_cycle_screener.py --layer 1 --min-score 80
  python ai_super_cycle_screener.py --output ai_screen_2026Q2.csv
        """,
    )
    parser.add_argument("--layer", type=int, choices=[1, 2, 3, 4],
                        help="Filter by AI Layer (1=Foundation, 2=Infra, 3=Enablers, 4=App)")
    parser.add_argument("--min-score", type=float, default=0.0,
                        help="Minimum total score (default: 0)")
    parser.add_argument("--output", type=str, default="ai_super_cycle_screen_results.csv",
                        help="Output CSV path (default: ai_super_cycle_screen_results.csv)")
    parser.add_argument("--min-mcap", type=float, default=20.0,
                        help="Minimum market cap in $B (default: 20)")

    args = parser.parse_args()

    cfg = ScreeningConfig(min_market_cap_b=args.min_mcap)

    run_screener(
        layer_filter=args.layer,
        min_score=args.min_score,
        output_csv=args.output,
        config=cfg,
    )


if __name__ == "__main__":
    main()
