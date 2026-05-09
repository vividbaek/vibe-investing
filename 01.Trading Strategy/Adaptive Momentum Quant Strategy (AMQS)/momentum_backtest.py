#!/usr/bin/env python3
"""
momentum_backtest.py
=====================
Production backtest engine for the Adaptive Momentum Quant Strategy (AMQS).

Core algorithm:
  1. Universe: NASDAQ-100 + AI Value Chain stocks (~150 names)
  2. Signal: 4-Factor Composite Momentum
       - 50% weight: 12-1 momentum (12M return excl. last month)
       - 30% weight: 6-1 momentum
       - 15% weight: 3-1 momentum
       -  5% weight: inverse 60-day realized volatility
  3. Selection: Top 10 by composite z-score, with 5-stock buffer for hold
  4. Rebalance: Weekly (every Friday close) + daily stop-loss check
  5. Risk filter: Defensive basket when QQQ < 200d MA or VIX > 30
  6. Costs: 0.05% commission + 0.10% slippage per trade

This script fetches live data from yfinance and runs the full backtest.
Produces the same CSV outputs as generate_backtest_data.py for cross-validation.

Author:  Dennis Kim (HoKwang Kim / 김호광)
GitHub:  https://github.com/gameworkerkim/vibe-investing
License: MIT
Version: 1.0 (2026-05-02)

Usage:
    python momentum_backtest.py
    python momentum_backtest.py --start 2024-01-02 --end 2026-04-30
    python momentum_backtest.py --top-n 10 --rebalance weekly
    python momentum_backtest.py --no-regime-filter   # disable defensive mode

Dependencies:
    pip install yfinance pandas numpy tabulate
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

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
# AMQS Universe
# -------------------------------------------------------------------
# ~150 names spanning NASDAQ-100 majors + AI Value Chain
# -------------------------------------------------------------------

AMQS_UNIVERSE = [
    # Mega-cap Tech (NASDAQ-100 Top 20)
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL",
    "NFLX", "ADBE", "CRM", "INTC", "CSCO", "AMD", "QCOM", "TXN", "AMAT", "INTU", "ISRG",
    # Semiconductors (Layer 1)
    "TSM", "ASML", "MU", "LRCX", "KLAC", "MRVL", "ON", "MCHP", "ARM", "SMCI",
    # Hyperscaler-adjacent (Layer 2)
    "PLTR", "NOW", "SNOW", "DDOG", "MDB", "PANW", "CRWD", "ZS", "TEAM",
    # Power/Cooling/Network (Layer 3)
    "VRT", "ANET", "ETN", "GEV", "NVT", "PWR", "GE", "EMR", "ROK", "JCI", "TT",
    # Internet & Software
    "SHOP", "UBER", "ABNB", "DASH", "ROKU", "PINS", "SPOT",
    # Premium consumer & retailers
    "COST", "WMT", "HD", "MCD", "SBUX", "NKE", "LULU", "TJX", "DPZ",
    # Financials with momentum/growth tilts
    "V", "MA", "AXP", "JPM", "BLK", "GS", "MS", "SCHW",
    # Healthcare with momentum
    "LLY", "UNH", "ABBV", "MRK", "TMO", "DHR", "VRTX",
    # Defense/Industrial
    "NOC", "LMT", "RTX", "GD", "BA", "CAT", "DE", "GWW",
    # Energy momentum
    "XOM", "CVX", "OXY", "EOG",
    # Defensive basket (used in Risk-Off regime)
    "BRK-B", "JNJ", "PG", "KO", "PEP", "ABT", "MO",
]

DEFENSIVE_BASKET = ["BRK-B", "WMT", "COST", "JNJ", "KO", "PG", "PEP"]


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

@dataclass
class BacktestConfig:
    start_date: str = "2024-01-02"
    end_date: str = "2026-04-30"
    initial_capital: float = 100_000.0
    top_n: int = 10
    hold_buffer: int = 5  # hold if rank <= top_n + hold_buffer
    rebalance_freq: str = "weekly"  # "weekly" | "daily" | "monthly"
    stop_loss_pct: float = -0.12     # -12% from rebalance entry
    commission_pct: float = 0.0005    # 5 bps
    slippage_pct: float = 0.0010      # 10 bps
    # Signal weights
    w_mom_12_1: float = 0.50
    w_mom_6_1: float = 0.30
    w_mom_3_1: float = 0.15
    w_vol_inv: float = 0.05
    # Pre-filters
    min_market_cap_b: float = 20.0
    min_avg_dollar_volume_m: float = 200.0
    max_vol_60d_annualized: float = 0.80
    # Regime filter
    enable_regime_filter: bool = True
    regime_ma_window: int = 200
    vix_threshold_riskoff: float = 30.0


# -------------------------------------------------------------------
# Data Loader
# -------------------------------------------------------------------

def fetch_price_history(tickers: List[str], start: str, end: str) -> pd.DataFrame:
    """Pull adjusted close prices from yfinance, returning a DataFrame indexed by date."""
    print(f"Fetching {len(tickers)} tickers from {start} to {end}...")
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data
    # Drop columns with too many NaN
    prices = prices.dropna(axis=1, thresh=int(len(prices) * 0.7))
    print(f"  Successfully loaded {prices.shape[1]} tickers, {prices.shape[0]} days")
    return prices


def fetch_benchmarks(start: str, end: str) -> pd.DataFrame:
    """Fetch QQQ + SOXX + AI Semi basket benchmarks."""
    bench_tickers = ["QQQ", "SOXX", "NVDA", "AVGO", "AMD", "TSM", "MU", "^VIX"]
    data = yf.download(bench_tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        prices = data
    # Build AI Semi basket (NVDA + AVGO + AMD + TSM + MU equal-weight)
    semi_components = ["NVDA", "AVGO", "AMD", "TSM", "MU"]
    semi_returns = prices[semi_components].pct_change()
    aisemi_basket = (1 + semi_returns.mean(axis=1)).cumprod() * 100
    aisemi_basket.iloc[0] = 100
    prices["AISEMI"] = aisemi_basket
    return prices


# -------------------------------------------------------------------
# Momentum Signal
# -------------------------------------------------------------------

def compute_momentum_signals(prices: pd.DataFrame, asof: pd.Timestamp,
                              cfg: BacktestConfig) -> pd.Series:
    """Compute 4-factor composite momentum z-score for all tickers as of date."""
    end = asof
    # Date ranges
    d_1m = end - pd.Timedelta(days=30)
    d_3m = end - pd.Timedelta(days=92)
    d_6m = end - pd.Timedelta(days=183)
    d_12m = end - pd.Timedelta(days=365)
    d_60d = end - pd.Timedelta(days=90)

    # Find nearest available trading day
    def nearest(target):
        idx = prices.index.searchsorted(target)
        if idx >= len(prices.index):
            idx = len(prices.index) - 1
        return prices.index[idx]

    p_now = prices.loc[nearest(end)]
    p_1m = prices.loc[nearest(d_1m)]
    p_3m = prices.loc[nearest(d_3m)]
    p_6m = prices.loc[nearest(d_6m)]
    p_12m = prices.loc[nearest(d_12m)]

    # Compute time-shifted returns
    ret_12m_to_1m = (p_1m / p_12m) - 1   # 12M return up to 1M ago
    ret_6m_to_1m = (p_1m / p_6m) - 1
    ret_3m_to_1m = (p_1m / p_3m) - 1

    # 60-day realized volatility (annualized)
    window_prices = prices.loc[d_60d:end]
    daily_returns = window_prices.pct_change().dropna()
    vol_60d = daily_returns.std() * np.sqrt(252)
    inv_vol = 1 / vol_60d.replace(0, np.nan)

    # Z-score normalize each component within the universe
    def zscore(s):
        s = s.dropna()
        if len(s) < 5:
            return s * 0
        return (s - s.mean()) / s.std(ddof=0)

    z_12_1 = zscore(ret_12m_to_1m)
    z_6_1 = zscore(ret_6m_to_1m)
    z_3_1 = zscore(ret_3m_to_1m)
    z_vol = zscore(inv_vol)

    # Composite (align indices, fill NaN with 0)
    composite = (
        cfg.w_mom_12_1 * z_12_1.reindex(prices.columns).fillna(-99) +
        cfg.w_mom_6_1 * z_6_1.reindex(prices.columns).fillna(-99) +
        cfg.w_mom_3_1 * z_3_1.reindex(prices.columns).fillna(-99) +
        cfg.w_vol_inv * z_vol.reindex(prices.columns).fillna(-99)
    )
    return composite.sort_values(ascending=False)


# -------------------------------------------------------------------
# Regime Filter
# -------------------------------------------------------------------

def regime_state(qqq_prices: pd.Series, vix_prices: pd.Series,
                 asof: pd.Timestamp, cfg: BacktestConfig) -> str:
    """Return 'risk_on', 'risk_off', or 'defensive'."""
    if not cfg.enable_regime_filter:
        return "risk_on"

    # 200-day MA of QQQ
    if len(qqq_prices.loc[:asof]) < cfg.regime_ma_window:
        return "risk_on"

    qqq_ma = qqq_prices.loc[:asof].rolling(cfg.regime_ma_window).mean().iloc[-1]
    qqq_now = qqq_prices.loc[:asof].iloc[-1]
    vix_now = vix_prices.loc[:asof].iloc[-1] if asof in vix_prices.index else 20

    # Check 5-day QQQ return for crash detection
    if len(qqq_prices.loc[:asof]) >= 5:
        qqq_5d_ret = (qqq_prices.loc[:asof].iloc[-1] / qqq_prices.loc[:asof].iloc[-5]) - 1
        if qqq_5d_ret < -0.08:
            return "defensive"

    if qqq_now < qqq_ma or vix_now > cfg.vix_threshold_riskoff:
        return "risk_off"
    return "risk_on"


# -------------------------------------------------------------------
# Backtest Engine
# -------------------------------------------------------------------

@dataclass
class BacktestResult:
    nav_history: pd.Series
    holdings_history: List[Tuple[pd.Timestamp, List[str], str]]  # (date, tickers, regime)
    total_trades: int = 0
    total_costs: float = 0.0


def run_backtest(prices: pd.DataFrame, benchmarks: pd.DataFrame,
                 cfg: BacktestConfig) -> BacktestResult:
    """Run the AMQS strategy backtest. Returns NAV history + holdings log."""
    qqq = benchmarks["QQQ"]
    vix = benchmarks.get("^VIX", pd.Series(20, index=qqq.index))

    # Determine rebalance dates
    all_dates = prices.index
    if cfg.rebalance_freq == "weekly":
        rebal_dates = [d for d in all_dates if d.weekday() == 4]  # Friday
    elif cfg.rebalance_freq == "daily":
        rebal_dates = list(all_dates)
    else:  # monthly
        rebal_dates = [d for d in all_dates
                       if d.month != (d - pd.Timedelta(days=1)).month]

    print(f"\nBacktest setup:")
    print(f"  Period:        {all_dates[0].date()} to {all_dates[-1].date()}")
    print(f"  Trading days:  {len(all_dates)}")
    print(f"  Rebalance days:{len(rebal_dates)} ({cfg.rebalance_freq})")
    print(f"  Initial cap:   ${cfg.initial_capital:,.0f}")
    print(f"  Top N:         {cfg.top_n}")
    print(f"  Stop loss:     {cfg.stop_loss_pct*100:.1f}%")
    print(f"  Costs:         {(cfg.commission_pct + cfg.slippage_pct)*100:.2f}% per trade")
    print()

    # Initialize portfolio
    cash = cfg.initial_capital
    positions: Dict[str, Dict] = {}  # ticker -> {shares, entry_price, entry_date}
    nav_history = pd.Series(index=all_dates, dtype=float)
    holdings_log: List[Tuple[pd.Timestamp, List[str], str]] = []
    total_trades = 0
    total_costs = 0.0

    for d in all_dates:
        # Mark-to-market
        position_value = sum(
            pos["shares"] * prices.loc[d, t] if t in prices.columns and not pd.isna(prices.loc[d, t]) else 0
            for t, pos in positions.items()
        )
        nav = cash + position_value
        nav_history.loc[d] = nav

        # Daily stop-loss check
        for t in list(positions.keys()):
            if t not in prices.columns or pd.isna(prices.loc[d, t]):
                continue
            cur_price = prices.loc[d, t]
            entry_price = positions[t]["entry_price"]
            if (cur_price / entry_price - 1) <= cfg.stop_loss_pct:
                # Stop-out
                proceeds = positions[t]["shares"] * cur_price * (1 - cfg.commission_pct - cfg.slippage_pct)
                cost = positions[t]["shares"] * cur_price * (cfg.commission_pct + cfg.slippage_pct)
                cash += proceeds
                total_costs += cost
                total_trades += 1
                del positions[t]

        # Rebalance
        if d in rebal_dates:
            regime = regime_state(qqq, vix, d, cfg)
            momentum_scores = compute_momentum_signals(prices, d, cfg)

            if regime == "defensive":
                target = [t for t in DEFENSIVE_BASKET if t in prices.columns][:7]
            elif regime == "risk_off":
                # 50% cash, 50% in top 10 momentum
                target = momentum_scores.head(cfg.top_n).index.tolist()
            else:  # risk_on
                target = momentum_scores.head(cfg.top_n).index.tolist()

            target = [t for t in target if t in prices.columns and not pd.isna(prices.loc[d, t])]

            # Sell anything not in target (with hold buffer for risk_on)
            if regime == "risk_on":
                hold_universe = momentum_scores.head(cfg.top_n + cfg.hold_buffer).index.tolist()
            else:
                hold_universe = target

            for t in list(positions.keys()):
                if t not in hold_universe and t in prices.columns:
                    cur_price = prices.loc[d, t]
                    if pd.notna(cur_price):
                        proceeds = positions[t]["shares"] * cur_price * (1 - cfg.commission_pct - cfg.slippage_pct)
                        cost = positions[t]["shares"] * cur_price * (cfg.commission_pct + cfg.slippage_pct)
                        cash += proceeds
                        total_costs += cost
                        total_trades += 1
                        del positions[t]

            # Buy missing target names
            equity_pct = 1.0 if regime == "risk_on" else (0.5 if regime == "risk_off" else 1.0)
            target_capital = (cash + position_value) * equity_pct
            per_position = target_capital / len(target) if target else 0
            for t in target:
                if t not in positions and t in prices.columns:
                    cur_price = prices.loc[d, t]
                    if pd.notna(cur_price) and cur_price > 0:
                        shares = (per_position / cur_price)
                        cost_total = shares * cur_price * (1 + cfg.commission_pct + cfg.slippage_pct)
                        if cost_total > cash:
                            shares = cash / (cur_price * (1 + cfg.commission_pct + cfg.slippage_pct))
                            cost_total = shares * cur_price * (1 + cfg.commission_pct + cfg.slippage_pct)
                        if shares > 0:
                            cash -= cost_total
                            total_costs += shares * cur_price * (cfg.commission_pct + cfg.slippage_pct)
                            total_trades += 1
                            positions[t] = {
                                "shares": shares,
                                "entry_price": cur_price,
                                "entry_date": d,
                            }

            holdings_log.append((d, list(positions.keys()), regime))

    return BacktestResult(
        nav_history=nav_history.dropna(),
        holdings_history=holdings_log,
        total_trades=total_trades,
        total_costs=total_costs,
    )


# -------------------------------------------------------------------
# Performance Metrics
# -------------------------------------------------------------------

def compute_metrics(nav: pd.Series, rf: float = 0.045) -> Dict[str, float]:
    """Compute total return, CAGR, vol, MDD, Sharpe."""
    initial = nav.iloc[0]
    final = nav.iloc[-1]
    total_ret = (final / initial - 1) * 100
    years = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr = ((final / initial) ** (1 / years) - 1) * 100 if years > 0 else 0

    daily_returns = nav.pct_change().dropna()
    vol = daily_returns.std() * np.sqrt(252) * 100

    cummax = nav.cummax()
    drawdown = (nav / cummax - 1) * 100
    mdd = drawdown.min()

    sharpe = (cagr / 100 - rf) / (vol / 100) if vol > 0 else 0

    return {
        "total_return_pct": total_ret,
        "cagr_pct": cagr,
        "vol_annualized_pct": vol,
        "max_drawdown_pct": mdd,
        "sharpe_ratio": sharpe,
        "final_nav": final,
    }


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Momentum Quant Strategy Backtest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--start", type=str, default="2024-01-02")
    parser.add_argument("--end", type=str, default="2026-04-30")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--rebalance", type=str, default="weekly",
                        choices=["weekly", "daily", "monthly"])
    parser.add_argument("--no-regime-filter", action="store_true")
    parser.add_argument("--initial", type=float, default=100_000.0)
    parser.add_argument("--output", type=str, default="amqs_backtest_results.csv")
    args = parser.parse_args()

    cfg = BacktestConfig(
        start_date=args.start,
        end_date=args.end,
        top_n=args.top_n,
        rebalance_freq=args.rebalance,
        enable_regime_filter=not args.no_regime_filter,
        initial_capital=args.initial,
    )

    print("=" * 78)
    print(f"  Adaptive Momentum Quant Strategy (AMQS) Backtest")
    print(f"  Run: {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 78)

    # Fetch data
    prices = fetch_price_history(AMQS_UNIVERSE, args.start, args.end)
    benchmarks = fetch_benchmarks(args.start, args.end)

    # Run backtest
    result = run_backtest(prices, benchmarks, cfg)

    # Compute metrics for strategy and benchmarks
    strategy_metrics = compute_metrics(result.nav_history)
    qqq_nav = (benchmarks["QQQ"] / benchmarks["QQQ"].iloc[0]) * cfg.initial_capital
    soxx_nav = (benchmarks["SOXX"] / benchmarks["SOXX"].iloc[0]) * cfg.initial_capital
    aisemi_nav = (benchmarks["AISEMI"] / benchmarks["AISEMI"].iloc[0]) * cfg.initial_capital

    qqq_metrics = compute_metrics(qqq_nav.reindex(result.nav_history.index).dropna())
    soxx_metrics = compute_metrics(soxx_nav.reindex(result.nav_history.index).dropna())
    aisemi_metrics = compute_metrics(aisemi_nav.reindex(result.nav_history.index).dropna())

    print("\n" + "=" * 78)
    print("  Backtest Results")
    print("=" * 78)
    print(f"\n{'Series':<15} {'Total Ret':>10} {'CAGR':>8} {'Vol':>7} {'MDD':>8} {'Sharpe':>7}")
    print("-" * 64)
    for label, m in [("AMQS Strategy", strategy_metrics),
                     ("QQQ", qqq_metrics),
                     ("SOXX (PHLX Semi)", soxx_metrics),
                     ("AI Semi Basket", aisemi_metrics)]:
        print(f"{label:<15} {m['total_return_pct']:>9.2f}% {m['cagr_pct']:>7.2f}% "
              f"{m['vol_annualized_pct']:>6.1f}% {m['max_drawdown_pct']:>7.1f}% "
              f"{m['sharpe_ratio']:>7.2f}")

    print(f"\nTotal trades:    {result.total_trades}")
    print(f"Total costs:     ${result.total_costs:,.2f}")
    print(f"Annual turnover: {result.total_trades / 2 / ((result.nav_history.index[-1] - result.nav_history.index[0]).days / 365.25):.0f}%")

    # Save NAV CSV
    out_df = pd.DataFrame({
        "date": result.nav_history.index.strftime("%Y-%m-%d"),
        "AMQS_nav": result.nav_history.values,
        "QQQ_nav": qqq_nav.reindex(result.nav_history.index).values,
        "SOXX_nav": soxx_nav.reindex(result.nav_history.index).values,
        "AISEMI_nav": aisemi_nav.reindex(result.nav_history.index).values,
    })
    out_df.to_csv(args.output, index=False)
    print(f"\n✓ Backtest results saved to: {args.output}")


if __name__ == "__main__":
    main()
