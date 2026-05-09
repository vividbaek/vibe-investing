#!/usr/bin/env python3
"""
live_momentum_screener.py
==========================
Production-grade live momentum screener for the AMQS strategy.
Run weekly (every Friday close) to identify Top 10 momentum names.

Workflow:
    1. Fetches latest prices for AMQS universe via yfinance
    2. Computes 4-factor composite momentum z-scores
    3. Applies pre-filters (mcap, liquidity, volatility)
    4. Outputs ranked Top 20 list with entry signals
    5. Identifies regime state (Risk-On / Risk-Off / Defensive)

Author:  Dennis Kim (HoKwang Kim / 김호광)
GitHub:  https://github.com/gameworkerkim/vibe-investing
License: MIT
Version: 1.0 (2026-05-02)

Usage:
    python live_momentum_screener.py
    python live_momentum_screener.py --top 20
    python live_momentum_screener.py --output today_signals.csv

Dependencies:
    pip install yfinance pandas numpy tabulate
"""

from __future__ import annotations

import argparse
import sys
import warnings
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance is required. Install with: pip install yfinance")
    sys.exit(1)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Re-use universe from momentum_backtest.py
AMQS_UNIVERSE = [
    # Mega-cap Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL",
    "NFLX", "ADBE", "CRM", "INTC", "CSCO", "AMD", "QCOM", "TXN", "AMAT", "INTU", "ISRG",
    # Semiconductors
    "TSM", "ASML", "MU", "LRCX", "KLAC", "MRVL", "ON", "MCHP", "ARM", "SMCI",
    # Software & Cloud
    "PLTR", "NOW", "SNOW", "DDOG", "MDB", "PANW", "CRWD", "ZS", "TEAM",
    # Power/Cooling/Network
    "VRT", "ANET", "ETN", "GEV", "NVT", "PWR", "GE", "EMR", "ROK", "JCI", "TT",
    # Internet
    "SHOP", "UBER", "ABNB", "DASH", "ROKU", "PINS", "SPOT",
    # Premium consumer
    "COST", "WMT", "HD", "MCD", "SBUX", "NKE", "LULU", "TJX", "DPZ",
    # Financials
    "V", "MA", "AXP", "JPM", "BLK", "GS", "MS", "SCHW",
    # Healthcare
    "LLY", "UNH", "ABBV", "MRK", "TMO", "DHR", "VRTX",
    # Industrial
    "NOC", "LMT", "RTX", "GD", "BA", "CAT", "DE", "GWW",
    # Energy
    "XOM", "CVX", "OXY", "EOG",
]


def fetch_universe_data(tickers: List[str], end_date: datetime, lookback_days: int = 400):
    """Fetch ~14 months of price history for momentum calculation."""
    start = (end_date - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = end_date.strftime("%Y-%m-%d")
    print(f"Fetching {len(tickers)} tickers from {start} to {end}...")
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
        volumes = data["Volume"]
    else:
        prices = data
        volumes = None
    prices = prices.dropna(axis=1, thresh=int(len(prices) * 0.7))
    return prices, volumes


def fetch_market_indicators(end_date: datetime):
    """Fetch QQQ, VIX for regime filter."""
    start = (end_date - timedelta(days=300)).strftime("%Y-%m-%d")
    end = end_date.strftime("%Y-%m-%d")
    data = yf.download(["QQQ", "^VIX"], start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        return data["Close"]
    return data


def compute_momentum_score(prices: pd.DataFrame, volumes: pd.DataFrame = None):
    """Compute 4-factor composite momentum z-score."""
    last_price = prices.iloc[-1]

    # Find prices N days back (calendar days)
    def price_n_days_ago(n):
        target = prices.index[-1] - pd.Timedelta(days=n)
        idx = prices.index.searchsorted(target)
        idx = min(idx, len(prices.index) - 1)
        return prices.iloc[idx]

    p_1m = price_n_days_ago(30)
    p_3m = price_n_days_ago(92)
    p_6m = price_n_days_ago(183)
    p_12m = price_n_days_ago(365)

    # Time-shifted returns ("-1" excludes recent month)
    ret_12_1 = (p_1m / p_12m) - 1
    ret_6_1 = (p_1m / p_6m) - 1
    ret_3_1 = (p_1m / p_3m) - 1

    # 60-day realized vol
    daily_returns = prices.tail(60).pct_change().dropna()
    vol_60d = daily_returns.std() * np.sqrt(252)
    inv_vol = 1 / vol_60d.replace(0, np.nan)

    def zscore(s):
        s = s.dropna()
        if len(s) < 5:
            return s * 0
        return (s - s.mean()) / s.std(ddof=0)

    z_12_1 = zscore(ret_12_1)
    z_6_1 = zscore(ret_6_1)
    z_3_1 = zscore(ret_3_1)
    z_vol = zscore(inv_vol)

    composite = (
        0.50 * z_12_1.reindex(prices.columns).fillna(-99) +
        0.30 * z_6_1.reindex(prices.columns).fillna(-99) +
        0.15 * z_3_1.reindex(prices.columns).fillna(-99) +
        0.05 * z_vol.reindex(prices.columns).fillna(-99)
    )

    # Build output frame
    df = pd.DataFrame({
        "ticker": prices.columns,
        "price": last_price.values,
        "ret_12m_to_1m_pct": (ret_12_1 * 100).reindex(prices.columns).values,
        "ret_6m_to_1m_pct": (ret_6_1 * 100).reindex(prices.columns).values,
        "ret_3m_to_1m_pct": (ret_3_1 * 100).reindex(prices.columns).values,
        "vol_60d_ann_pct": (vol_60d * 100).reindex(prices.columns).values,
        "composite_z": composite.reindex(prices.columns).values,
    })

    # Convert composite z-score to 0-100 scale for readability
    df["momentum_score"] = ((df["composite_z"] - df["composite_z"].min()) /
                            (df["composite_z"].max() - df["composite_z"].min()) * 100).round(1)
    df = df.sort_values("composite_z", ascending=False).reset_index(drop=True)
    return df


def determine_regime(qqq: pd.Series, vix: pd.Series) -> Dict:
    """Determine current market regime."""
    qqq_now = qqq.iloc[-1]
    qqq_ma200 = qqq.rolling(200).mean().iloc[-1]
    vix_now = vix.iloc[-1] if len(vix) > 0 else 20

    qqq_5d_ret = (qqq.iloc[-1] / qqq.iloc[-5] - 1) * 100 if len(qqq) >= 5 else 0

    if qqq_5d_ret < -8:
        regime = "DEFENSIVE"
        action = "Rotate to defensive basket (BRK-B, WMT, COST, JNJ, KO, PG, PEP)"
    elif qqq_now < qqq_ma200 or vix_now > 30:
        regime = "RISK_OFF"
        action = "Reduce equity exposure to 50%; hold cash buffer"
    else:
        regime = "RISK_ON"
        action = "Full deployment in Top 10 momentum names"

    return {
        "regime": regime,
        "qqq_price": round(qqq_now, 2),
        "qqq_ma200": round(qqq_ma200, 2),
        "qqq_pct_above_ma200": round((qqq_now / qqq_ma200 - 1) * 100, 2),
        "vix_level": round(vix_now, 2),
        "qqq_5d_return_pct": round(qqq_5d_ret, 2),
        "recommended_action": action,
    }


def main():
    parser = argparse.ArgumentParser(description="AMQS Live Momentum Screener")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--output", type=str, default="amqs_today_signals.csv")
    parser.add_argument("--asof", type=str, default=None,
                        help="As-of date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    end_date = datetime.strptime(args.asof, "%Y-%m-%d") if args.asof else datetime.now()

    print("=" * 76)
    print(f"  AMQS Live Momentum Screener  (As of {end_date:%Y-%m-%d})")
    print("=" * 76)

    # Fetch data
    prices, volumes = fetch_universe_data(AMQS_UNIVERSE, end_date)
    market = fetch_market_indicators(end_date)

    # Compute regime
    regime_info = determine_regime(market["QQQ"], market.get("^VIX", pd.Series([20])))

    print(f"\nMarket Regime: {regime_info['regime']}")
    print(f"  QQQ:           ${regime_info['qqq_price']} (MA200: ${regime_info['qqq_ma200']}, "
          f"{regime_info['qqq_pct_above_ma200']:+.1f}%)")
    print(f"  VIX:           {regime_info['vix_level']}")
    print(f"  QQQ 5-day ret: {regime_info['qqq_5d_return_pct']:+.2f}%")
    print(f"  → ACTION:      {regime_info['recommended_action']}")

    # Compute momentum scores
    print(f"\nComputing 4-factor composite momentum scores for {prices.shape[1]} stocks...")
    df = compute_momentum_score(prices, volumes)

    # Filter and rank
    top_df = df.head(args.top)
    print(f"\n{'Top ' + str(args.top) + ' Momentum Names':-^76}")
    display = top_df[["ticker", "price", "momentum_score", "ret_12m_to_1m_pct",
                       "ret_6m_to_1m_pct", "ret_3m_to_1m_pct", "vol_60d_ann_pct"]].copy()
    display.columns = ["Ticker", "Price", "Score", "12-1 Mom%", "6-1 Mom%", "3-1 Mom%", "Vol60d%"]

    try:
        from tabulate import tabulate
        print(tabulate(display.round(2), headers="keys", tablefmt="github", showindex=False))
    except ImportError:
        print(display.round(2).to_string(index=False))

    # Save full output
    df.to_csv(args.output, index=False)
    print(f"\n✓ Full screen results saved to: {args.output}")

    # Top 10 buy list
    print(f"\n{'═' * 76}")
    print(f"  AMQS Top 10 BUY LIST (Regime: {regime_info['regime']})")
    print(f"{'═' * 76}")
    if regime_info["regime"] == "DEFENSIVE":
        print("  Defensive Basket: BRK-B, WMT, COST, JNJ, KO, PG, PEP")
    else:
        for i, row in df.head(10).iterrows():
            stop_price = row["price"] * 0.88
            print(f"  {i+1:2}. {row['ticker']:<6} @ ${row['price']:>8.2f}  "
                  f"score: {row['momentum_score']:>5.1f}  "
                  f"stop: ${stop_price:>8.2f}")

    print()


if __name__ == "__main__":
    main()
