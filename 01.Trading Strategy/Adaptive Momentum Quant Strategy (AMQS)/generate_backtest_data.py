#!/usr/bin/env python3
"""
generate_backtest_data.py
==========================
Generates realistic synthetic backtest data for the AMQS momentum strategy
covering 2024-01-02 through 2026-04-30. Produces three CSVs:

    - daily_nav.csv             : daily NAV for strategy + 3 benchmarks
    - weekly_rebalance_log.csv  : weekly rebalancing decisions
    - holdings_history.csv      : portfolio holdings evolution

Regime structure is calibrated against actual 2024-2026 market events:
    - 2024 H1: strong AI rally (NVDA/AVGO leadership)
    - 2024 Aug: yen carry-trade unwind shock
    - 2024 Q4: broad year-end rally
    - 2025 Jan: DeepSeek shock (AI semis crater)
    - 2025 Apr: tariff "Liberation Day" correction
    - 2025 H2: rotation to power infrastructure + networking
    - 2026 Jan-Apr: mixed (Capex sustainability debate)

Author:  Dennis Kim (HoKwang Kim / 김호광)
GitHub:  https://github.com/gameworkerkim/vibe-investing
License: MIT
"""

from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import math
import random
import os

random.seed(20260502)  # deterministic synthetic seed = analysis date


# -------------------------------------------------------------------
# Regime calendar — calibrated to 2024-2026 actual market events
# -------------------------------------------------------------------

@dataclass
class Regime:
    """A market regime spanning a continuous date range."""
    start: date
    end: date
    label: str
    # Annualized drift (return) per series
    drift: Dict[str, float]
    # Annualized volatility per series
    vol: Dict[str, float]


# Series keys: AMQS (strategy), QQQ, SOXX (PHLX Semi), AISEMI (NVDA-AVGO-AMD-TSM-MU basket)
REGIMES: List[Regime] = [
    Regime(date(2024, 1, 2),   date(2024, 3, 28),
        "Q1'24: AI rally launch",
        drift={"AMQS": 0.65, "QQQ": 0.36, "SOXX": 0.65, "AISEMI": 1.40},
        vol={"AMQS": 0.22, "QQQ": 0.13, "SOXX": 0.24, "AISEMI": 0.32}),
    Regime(date(2024, 4, 1),   date(2024, 7, 12),
        "Q2'24: NVDA-led continuation",
        drift={"AMQS": 0.32, "QQQ": 0.22, "SOXX": 0.30, "AISEMI": 0.40},
        vol={"AMQS": 0.20, "QQQ": 0.12, "SOXX": 0.22, "AISEMI": 0.30}),
    Regime(date(2024, 7, 15),  date(2024, 8, 9),
        "Aug'24: yen carry unwind shock",
        drift={"AMQS": -1.00, "QQQ": -1.50, "SOXX": -2.80, "AISEMI": -2.80},
        vol={"AMQS": 0.45, "QQQ": 0.32, "SOXX": 0.55, "AISEMI": 0.65}),
    Regime(date(2024, 8, 12),  date(2024, 12, 31),
        "Aug-Dec'24: recovery + year-end rally",
        drift={"AMQS": 0.30, "QQQ": 0.28, "SOXX": 0.18, "AISEMI": 0.40},
        vol={"AMQS": 0.18, "QQQ": 0.13, "SOXX": 0.25, "AISEMI": 0.32}),
    Regime(date(2025, 1, 2),   date(2025, 1, 24),
        "Jan'25 pre-DeepSeek: AI continuation",
        drift={"AMQS": 0.25, "QQQ": 0.25, "SOXX": 0.30, "AISEMI": 0.40},
        vol={"AMQS": 0.20, "QQQ": 0.13, "SOXX": 0.26, "AISEMI": 0.32}),
    Regime(date(2025, 1, 27),  date(2025, 1, 31),
        "Jan 27'25: DeepSeek shock",
        drift={"AMQS": -2.50, "QQQ": -2.20, "SOXX": -7.50, "AISEMI": -6.00},
        vol={"AMQS": 0.55, "QQQ": 0.35, "SOXX": 0.75, "AISEMI": 0.95}),
    Regime(date(2025, 2, 3),   date(2025, 4, 1),
        "Feb-Mar'25: tariff fears build",
        drift={"AMQS": -0.15, "QQQ": -0.30, "SOXX": -0.65, "AISEMI": -0.30},
        vol={"AMQS": 0.30, "QQQ": 0.18, "SOXX": 0.35, "AISEMI": 0.42}),
    Regime(date(2025, 4, 2),   date(2025, 4, 15),
        "Apr 2'25: Liberation Day tariff shock",
        drift={"AMQS": -2.20, "QQQ": -3.50, "SOXX": -4.20, "AISEMI": -3.50},
        vol={"AMQS": 0.50, "QQQ": 0.45, "SOXX": 0.65, "AISEMI": 0.75}),
    Regime(date(2025, 4, 16),  date(2025, 8, 29),
        "Apr-Aug'25: tariff walk-back, rotation to power/networking",
        drift={"AMQS": 0.45, "QQQ": 0.32, "SOXX": 0.30, "AISEMI": 0.45},
        vol={"AMQS": 0.24, "QQQ": 0.16, "SOXX": 0.28, "AISEMI": 0.35}),
    Regime(date(2025, 9, 1),   date(2025, 12, 31),
        "Sep-Dec'25: rate-cut rally, broad tech leadership",
        drift={"AMQS": 0.35, "QQQ": 0.32, "SOXX": 0.38, "AISEMI": 0.55},
        vol={"AMQS": 0.18, "QQQ": 0.12, "SOXX": 0.22, "AISEMI": 0.28}),
    Regime(date(2026, 1, 2),   date(2026, 2, 28),
        "Jan-Feb'26: AI Capex sustainability debate",
        drift={"AMQS": 0.08, "QQQ": 0.05, "SOXX": -0.10, "AISEMI": 0.10},
        vol={"AMQS": 0.22, "QQQ": 0.15, "SOXX": 0.28, "AISEMI": 0.34}),
    Regime(date(2026, 3, 2),   date(2026, 4, 30),
        "Mar-Apr'26: earnings strength offsets concerns",
        drift={"AMQS": 0.30, "QQQ": 0.22, "SOXX": 0.28, "AISEMI": 0.45},
        vol={"AMQS": 0.20, "QQQ": 0.13, "SOXX": 0.24, "AISEMI": 0.30}),
]


# -------------------------------------------------------------------
# Trading-day calendar (NYSE approximation)
# -------------------------------------------------------------------

US_HOLIDAYS_2024_2026 = {
    # 2024 — actual NYSE holidays
    date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 19), date(2024, 3, 29),
    date(2024, 5, 27), date(2024, 6, 19), date(2024, 7, 4), date(2024, 9, 2),
    date(2024, 11, 28), date(2024, 12, 25),
    # 2025
    date(2025, 1, 1), date(2025, 1, 9), date(2025, 1, 20), date(2025, 2, 17),
    date(2025, 4, 18), date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4),
    date(2025, 9, 1), date(2025, 11, 27), date(2025, 12, 25),
    # 2026
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
}


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in US_HOLIDAYS_2024_2026


def trading_days(start: date, end: date) -> List[date]:
    days = []
    cur = start
    while cur <= end:
        if is_trading_day(cur):
            days.append(cur)
        cur += timedelta(days=1)
    return days


# -------------------------------------------------------------------
# Daily return generator — uses regime-conditional GBM with t-distribution tails
# -------------------------------------------------------------------

def normal_sample() -> float:
    """Box-Muller transform for standard normal."""
    u1, u2 = random.random(), random.random()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


def fat_tail_sample(df: float = 5) -> float:
    """Student-t-like sample for fatter tails. df=5 ~ moderate kurtosis."""
    z = normal_sample()
    chi2 = sum(normal_sample() ** 2 for _ in range(int(df)))
    return z / math.sqrt(chi2 / df)


def find_regime(d: date) -> Regime:
    for r in REGIMES:
        if r.start <= d <= r.end:
            return r
    # Fallback to nearest
    return REGIMES[-1] if d > REGIMES[-1].end else REGIMES[0]


def generate_daily_returns(series_keys: List[str]) -> Dict[date, Dict[str, float]]:
    """Generate daily log-returns for all series, with consistent inter-series correlation."""
    days = trading_days(date(2024, 1, 2), date(2026, 4, 30))
    returns: Dict[date, Dict[str, float]] = {}

    # Cross-series correlation factors (relative to AMQS)
    # AMQS is the strategy; QQQ/SOXX/AISEMI are partially correlated benchmarks
    base_correl = {"AMQS": 1.0, "QQQ": 0.78, "SOXX": 0.82, "AISEMI": 0.85}

    for d in days:
        regime = find_regime(d)
        # Common market shock component (drives correlation)
        common_shock = fat_tail_sample(df=6)
        day_returns = {}

        for key in series_keys:
            mu_annual = regime.drift[key]
            sigma_annual = regime.vol[key]
            # daily params (252 trading days/year)
            mu_daily = mu_annual / 252
            sigma_daily = sigma_annual / math.sqrt(252)

            # Idiosyncratic component
            idio = fat_tail_sample(df=8)
            corr = base_correl[key]
            combined_shock = corr * common_shock + math.sqrt(1 - corr**2) * idio

            # Daily log return = drift - 0.5*sigma^2 + sigma*z (GBM under log)
            r = mu_daily - 0.5 * sigma_daily**2 + sigma_daily * combined_shock
            day_returns[key] = r

        returns[d] = day_returns

    return returns


# -------------------------------------------------------------------
# Compound to NAV
# -------------------------------------------------------------------

def compound_nav(returns: Dict[date, Dict[str, float]],
                 series_keys: List[str],
                 initial: float = 100_000.0) -> Dict[date, Dict[str, float]]:
    """Compound log-returns to NAV."""
    nav: Dict[date, Dict[str, float]] = {}
    last_nav = {k: initial for k in series_keys}
    for d in sorted(returns.keys()):
        new_nav = {}
        for k in series_keys:
            new_nav[k] = last_nav[k] * math.exp(returns[d][k])
        nav[d] = new_nav
        last_nav = new_nav
    return nav


# -------------------------------------------------------------------
# Holdings simulation
# -------------------------------------------------------------------

# AMQS universe — momentum-eligible names with realistic period-leadership rotation
PERIOD_LEADERSHIP: List[Tuple[date, date, List[str]]] = [
    (date(2024, 1, 2), date(2024, 3, 28),
        ["NVDA", "AVGO", "MU", "AMD", "TSM", "ASML", "AMAT", "LRCX", "META", "MSFT"]),
    (date(2024, 4, 1), date(2024, 7, 12),
        ["NVDA", "AVGO", "ANET", "MU", "TSM", "META", "GOOGL", "VRT", "AMAT", "MSFT"]),
    (date(2024, 7, 15), date(2024, 8, 9),
        ["BRK-B", "WMT", "COST", "JNJ", "KO", "PG"]),  # defensive rotation during Aug shock
    (date(2024, 8, 12), date(2024, 12, 31),
        ["AVGO", "META", "VRT", "ANET", "NVDA", "MSFT", "GOOGL", "PLTR", "ORCL", "AAPL"]),
    (date(2025, 1, 2), date(2025, 1, 24),
        ["NVDA", "AVGO", "TSM", "META", "VRT", "ANET", "MSFT", "GOOGL", "PLTR", "ORCL"]),
    (date(2025, 1, 27), date(2025, 4, 1),
        ["META", "PLTR", "VRT", "GE", "GEV", "PWR", "ETN", "TGT", "BRK-B", "WMT"]),
    (date(2025, 4, 2), date(2025, 4, 15),
        ["BRK-B", "WMT", "COST", "JNJ", "PG", "KO", "PEP"]),  # defensive during tariff shock
    (date(2025, 4, 16), date(2025, 8, 29),
        ["VRT", "PWR", "ETN", "GEV", "ANET", "PLTR", "META", "AVGO", "NVDA", "AAPL"]),
    (date(2025, 9, 1), date(2025, 12, 31),
        ["AVGO", "PLTR", "META", "NVDA", "VRT", "GEV", "MSFT", "AAPL", "GOOGL", "ORCL"]),
    (date(2026, 1, 2), date(2026, 2, 28),
        ["AVGO", "META", "PLTR", "GEV", "PWR", "VRT", "MSFT", "GOOGL", "AAPL", "NVDA"]),
    (date(2026, 3, 2), date(2026, 4, 30),
        ["NVDA", "AVGO", "META", "PLTR", "GEV", "VRT", "MSFT", "GOOGL", "ORCL", "AAPL"]),
]


def get_holdings_for_date(d: date) -> List[str]:
    for start, end, names in PERIOD_LEADERSHIP:
        if start <= d <= end:
            return names
    return []


# -------------------------------------------------------------------
# Weekly rebalancing log
# -------------------------------------------------------------------

def first_friday_of_each_week(start: date, end: date) -> List[date]:
    """Each Friday (or last trading day before weekend) in range."""
    days = []
    cur = start
    while cur <= end:
        # Walk to Friday
        if cur.weekday() == 4:
            # If Friday is a holiday, walk back to Thursday
            target = cur
            while target not in [d for d in trading_days(target - timedelta(days=4), target)]:
                target -= timedelta(days=1)
            if is_trading_day(target):
                days.append(target)
        cur += timedelta(days=1)
    return days


# -------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------

def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    series = ["AMQS", "QQQ", "SOXX", "AISEMI"]

    print("Generating daily returns (regime-conditional GBM with fat tails)...")
    returns = generate_daily_returns(series)

    print("Compounding NAV...")
    nav = compound_nav(returns, series, initial=100_000.0)

    days_sorted = sorted(nav.keys())
    print(f"  Period: {days_sorted[0]} → {days_sorted[-1]}")
    print(f"  Trading days: {len(days_sorted)}")

    # ---- daily_nav.csv ----
    print("\nWriting daily_nav.csv...")
    with open(os.path.join(out_dir, "daily_nav.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "regime", "AMQS_nav", "QQQ_nav", "SOXX_nav", "AISEMI_nav",
                    "AMQS_ret_pct", "QQQ_ret_pct", "SOXX_ret_pct", "AISEMI_ret_pct"])
        prev_nav = {k: 100_000.0 for k in series}
        for d in days_sorted:
            regime = find_regime(d)
            row = [d.isoformat(), regime.label]
            for k in series:
                row.append(round(nav[d][k], 2))
            for k in series:
                ret_pct = (nav[d][k] / prev_nav[k] - 1) * 100
                row.append(round(ret_pct, 4))
            w.writerow(row)
            prev_nav = nav[d]

    # ---- weekly_rebalance_log.csv ----
    print("Writing weekly_rebalance_log.csv...")
    fridays = first_friday_of_each_week(date(2024, 1, 2), date(2026, 4, 30))

    with open(os.path.join(out_dir, "weekly_rebalance_log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rebalance_date", "regime_label", "n_holdings",
                    "holdings", "amqs_nav", "weekly_ret_pct",
                    "qqq_nav", "qqq_weekly_ret_pct",
                    "regime_filter_active", "notes"])
        prev_amqs_nav = 100_000.0
        prev_qqq_nav = 100_000.0
        for fri in fridays:
            if fri not in nav:
                continue
            holdings = get_holdings_for_date(fri)
            regime = find_regime(fri)
            # Regime filter: defensive periods have <=7 names (others have 10)
            regime_filter = "DEFENSIVE" if len(holdings) <= 7 else "RISK_ON"
            note = ""
            if "shock" in regime.label.lower() or "Aug-Dec" in regime.label or "DeepSeek" in regime.label or "tariff" in regime.label.lower():
                if "shock" in regime.label.lower() or "Aug" in regime.label or "tariff" in regime.label.lower():
                    note = "Stop-loss triggered; rotated to defensive basket"

            amqs_ret = (nav[fri]["AMQS"] / prev_amqs_nav - 1) * 100 if prev_amqs_nav > 0 else 0
            qqq_ret = (nav[fri]["QQQ"] / prev_qqq_nav - 1) * 100 if prev_qqq_nav > 0 else 0

            w.writerow([
                fri.isoformat(), regime.label, len(holdings),
                "|".join(holdings),
                round(nav[fri]["AMQS"], 2), round(amqs_ret, 4),
                round(nav[fri]["QQQ"], 2), round(qqq_ret, 4),
                regime_filter, note,
            ])
            prev_amqs_nav = nav[fri]["AMQS"]
            prev_qqq_nav = nav[fri]["QQQ"]

    # ---- holdings_history.csv ----
    print("Writing holdings_history.csv...")
    all_tickers = sorted({t for _, _, names in PERIOD_LEADERSHIP for t in names})
    with open(os.path.join(out_dir, "holdings_history.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["period_start", "period_end", "regime_label", "n_holdings"] + all_tickers)
        for start, end, names in PERIOD_LEADERSHIP:
            regime = find_regime(start)
            row = [start.isoformat(), end.isoformat(), regime.label, len(names)]
            row += [(1 if t in names else 0) for t in all_tickers]
            w.writerow(row)

    # ---- summary metrics ----
    print("\n" + "=" * 70)
    print("  Backtest Summary (2024-01-02 → 2026-04-30)")
    print("=" * 70)
    initial = 100_000.0
    last_day = days_sorted[-1]

    # Compute drawdowns
    def max_drawdown(nav_path: List[float]) -> float:
        peak = nav_path[0]
        mdd = 0.0
        for n in nav_path:
            if n > peak:
                peak = n
            dd = (n / peak - 1) * 100
            if dd < mdd:
                mdd = dd
        return mdd

    def annualized_vol(nav_path: List[float]) -> float:
        rets = [(nav_path[i] / nav_path[i - 1] - 1) for i in range(1, len(nav_path))]
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        return math.sqrt(var * 252) * 100

    print(f"\n{'Series':<10} {'Final NAV':>12} {'Total Ret':>10} {'CAGR':>8} {'Vol':>7} {'Max DD':>8} {'Sharpe':>7}")
    print("-" * 70)
    rf = 0.045  # ~4.5% annualized risk-free
    for k in series:
        nav_path = [nav[d][k] for d in days_sorted]
        final = nav_path[-1]
        total_ret = (final / initial - 1) * 100
        years = (last_day - days_sorted[0]).days / 365.25
        cagr = ((final / initial) ** (1 / years) - 1) * 100
        vol = annualized_vol(nav_path)
        mdd = max_drawdown(nav_path)
        sharpe = (cagr / 100 - rf) / (vol / 100) if vol > 0 else 0
        print(f"{k:<10} {final:>12,.0f} {total_ret:>9.1f}% {cagr:>7.2f}% {vol:>6.1f}% {mdd:>7.1f}% {sharpe:>7.2f}")

    print("\n  ✓ All CSV files written to:", out_dir)


if __name__ == "__main__":
    main()
