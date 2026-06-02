"""
AMQS-AI-Infra Backtest Engine
=============================
원본 AMQS 백테스트 방법론을 AI 인프라 universe 로 적용:

  * 주간 리밸런싱 (금요일 종가 신호 → 월요일 시초가 진입)
  * Top-N(기본 10) 선별 + 서브테마 분산 캡
  * -12% per-name 손절 (리밸런싱 진입가 기준)
  * 거시 레짐 필터 (Risk-On/Off/Defensive) → 투자 비중 조절
  * 거래비용 5bps + 슬리피지 10bps
  * 벤치마크: QQQ · SMH(반도체) · SOXX · AI-Infra 동가중 바스켓

Outputs (data/):
  * backtest_equity.csv    — 일별 equity curves
  * backtest_positions.csv — 주별 목표 비중 + regime
  * backtest_trades.csv    — 진입/청산/손절 로그
  * backtest_regimes.csv   — 레짐 전환 이력
  * backtest_summary.csv   — 성과 요약표
"""

from __future__ import annotations

import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    from .strategy import (
        AMQSConfig, AI_INFRA_TICKERS, MACRO_TICKERS,
        measure, apply_prefilter, score, allocate, detect_regime,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from script.strategy import (
        AMQSConfig, AI_INFRA_TICKERS, MACRO_TICKERS,
        measure, apply_prefilter, score, allocate, detect_regime,
    )


BENCH_ETFS = ["QQQ", "SMH", "SOXX"]


def _download(tickers, start, end):
    import yfinance as yf
    raw = yf.download(
        tickers=tickers, start=start, end=end,
        auto_adjust=True, progress=False, group_by="ticker", threads=True,
    )
    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = raw.columns.get_level_values(0)
        if tickers[0] in lvl0:
            return pd.concat(
                {t: raw[t]["Close"] for t in tickers if t in lvl0}, axis=1,
            )
        return raw["Close"]
    return raw[["Close"]].rename(columns={"Close": tickers[0]})


def _max_drawdown(curve: pd.Series) -> float:
    return float((curve / curve.cummax() - 1.0).min())


def _annualized_stats(daily: pd.Series) -> dict:
    r = daily.dropna()
    if r.empty:
        return {"total": 0.0, "cagr": 0.0, "vol": 0.0, "sharpe": 0.0}
    total = float((1 + r).prod() - 1)
    n = len(r)
    cagr = (1 + total) ** (252 / n) - 1 if n > 0 else 0.0
    vol = float(r.std() * math.sqrt(252))
    sharpe = (r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else 0.0
    return {"total": total, "cagr": cagr, "vol": vol, "sharpe": float(sharpe)}


def run_backtest(
    start: str = "2024-01-02",
    end: Optional[str] = None,
    config: Optional[AMQSConfig] = None,
    txn_cost_bps: Optional[float] = None,
    slippage_bps: Optional[float] = None,
    initial_capital: float = 100_000.0,
    out_dir: str = "data",
) -> pd.DataFrame:
    cfg = config or AMQSConfig()
    txn_bps = txn_cost_bps if txn_cost_bps is not None else cfg.txn_cost_bps
    slip_bps = slippage_bps if slippage_bps is not None else cfg.slippage_bps
    total_cost_per_side = (txn_bps + slip_bps) / 10_000

    end = end or dt.date.today().isoformat()
    warmup_start = (pd.Timestamp(start) - pd.Timedelta(days=420)).date().isoformat()

    print(f"데이터 다운로드 (warmup {warmup_start} -> {end})...")
    uni = _download(AI_INFRA_TICKERS, warmup_start, end)
    # 일부 종목은 상장 이력이 짧을 수 있음 → 가용 종목만 사용
    avail = [t for t in AI_INFRA_TICKERS if t in uni.columns and uni[t].dropna().shape[0] > 260]
    uni = uni[avail].ffill()
    dropped = [t for t in AI_INFRA_TICKERS if t not in avail]
    if dropped:
        print(f"  [경고] 데이터 부족으로 제외된 종목: {', '.join(dropped)}")

    macro = _download([MACRO_TICKERS["QQQ"], MACRO_TICKERS["VIX"]], warmup_start, end)
    qqq_full = macro[MACRO_TICKERS["QQQ"]] if MACRO_TICKERS["QQQ"] in macro else pd.Series(dtype=float)
    vix_full = macro[MACRO_TICKERS["VIX"]] if MACRO_TICKERS["VIX"] in macro else pd.Series(dtype=float)

    benches = _download(BENCH_ETFS, warmup_start, end)
    qqq_bench = benches["QQQ"]
    smh_bench = benches["SMH"] if "SMH" in benches else qqq_bench
    soxx_bench = benches["SOXX"] if "SOXX" in benches else qqq_bench
    ai_basket = uni  # AI-Infra 동가중 바스켓 = universe 전체 동가중

    if uni.empty:
        raise RuntimeError("가격 다운로드 실패")

    bt_dates = uni.loc[start:end].index
    all_dates = uni.index

    daily_uni = uni.pct_change().fillna(0.0)
    daily_qqq = qqq_bench.pct_change().fillna(0.0)
    daily_smh = smh_bench.pct_change().fillna(0.0)
    daily_soxx = soxx_bench.pct_change().fillna(0.0)
    daily_ai = ai_basket.pct_change().fillna(0.0).mean(axis=1)

    weights = pd.DataFrame(0.0, index=all_dates, columns=avail)
    current_weights = pd.Series(0.0, index=avail)
    entry_prices = pd.Series(np.nan, index=avail)
    txn_cost = pd.Series(0.0, index=all_dates)

    rebalance_log: list[dict] = []
    trade_log: list[dict] = []
    regime_log: list[dict] = []

    print(f"백테스트 진행 중 ({len(bt_dates)} 영업일, {len(avail)}종목)...")

    for i, today in enumerate(all_dates):
        if today < bt_dates[0]:
            continue

        past = uni.iloc[: i]
        past_qqq = qqq_full.iloc[: i]
        past_vix = vix_full.iloc[: i]
        if past.shape[0] < 260:
            continue

        # --- 손절 체크 (오늘 종가 기준) ---
        prices_today = uni.iloc[i]
        forced_exits: list[str] = []
        for t in avail:
            if current_weights[t] > 0 and not np.isnan(entry_prices[t]):
                change = prices_today[t] / entry_prices[t] - 1.0
                if change <= cfg.stop_loss_from_entry:
                    forced_exits.append(t)
                    trade_log.append({
                        "date": today.date().isoformat(), "ticker": t,
                        "action": "STOP_LOSS", "price": float(prices_today[t]),
                        "entry_price": float(entry_prices[t]),
                        "pnl_pct": round(change, 4),
                    })
        for t in forced_exits:
            current_weights[t] = 0.0
            entry_prices[t] = np.nan

        # --- 주간 리밸런싱? ---
        is_rebal = (today.weekday() == cfg.rebalance_dow) or (i == 0)
        if is_rebal:
            metrics = measure(past, market=past_qqq)
            apply_prefilter(metrics, cfg)
            score(metrics, cfg)
            regime = detect_regime(past_qqq, past_vix, cfg)
            allocate(metrics, cfg, regime=regime.label)

            target = pd.Series({m.ticker: m.weight for m in metrics}, index=avail).fillna(0.0)
            turnover = (target - current_weights).abs().sum()
            txn_cost.loc[today] = turnover * total_cost_per_side

            for t in avail:
                if target[t] > 0 and current_weights[t] == 0:
                    trade_log.append({
                        "date": today.date().isoformat(), "ticker": t,
                        "action": "BUY", "price": float(prices_today[t]),
                        "entry_price": float(prices_today[t]), "pnl_pct": None,
                    })
                    entry_prices[t] = prices_today[t]
                elif target[t] == 0 and current_weights[t] > 0:
                    trade_log.append({
                        "date": today.date().isoformat(), "ticker": t,
                        "action": "SELL", "price": float(prices_today[t]),
                        "entry_price": float(entry_prices[t]) if not np.isnan(entry_prices[t]) else None,
                        "pnl_pct": round(prices_today[t] / entry_prices[t] - 1.0, 4) if not np.isnan(entry_prices[t]) else None,
                    })
                    entry_prices[t] = np.nan

            current_weights = target.copy()
            rebalance_log.append({"date": today.date().isoformat(),
                                  "regime": regime.label,
                                  **{t: round(target[t], 4) for t in avail if target[t] > 0}})
            regime_log.append({"date": today.date().isoformat(),
                               "regime": regime.label, "vix": regime.vix_level,
                               "qqq_5d": regime.qqq_5d_return})

        weights.loc[today] = current_weights.values

    # --- equity curves ---
    port_daily = (weights.shift(1).fillna(0.0) * daily_uni).sum(axis=1) - txn_cost
    port_daily = port_daily.loc[bt_dates[0]: bt_dates[-1]]
    qqq_d = daily_qqq.loc[port_daily.index]
    smh_d = daily_smh.loc[port_daily.index]
    soxx_d = daily_soxx.loc[port_daily.index]
    ai_d = daily_ai.loc[port_daily.index]

    amqs_eq = initial_capital * (1 + port_daily).cumprod()
    qqq_eq = initial_capital * (1 + qqq_d).cumprod()
    smh_eq = initial_capital * (1 + smh_d).cumprod()
    soxx_eq = initial_capital * (1 + soxx_d).cumprod()
    ai_eq = initial_capital * (1 + ai_d).cumprod()

    amqs = _annualized_stats(port_daily); amqs["mdd"] = _max_drawdown(amqs_eq); amqs["final"] = float(amqs_eq.iloc[-1])
    qqq = _annualized_stats(qqq_d); qqq["mdd"] = _max_drawdown(qqq_eq); qqq["final"] = float(qqq_eq.iloc[-1])
    smh = _annualized_stats(smh_d); smh["mdd"] = _max_drawdown(smh_eq); smh["final"] = float(smh_eq.iloc[-1])
    soxx = _annualized_stats(soxx_d); soxx["mdd"] = _max_drawdown(soxx_eq); soxx["final"] = float(soxx_eq.iloc[-1])
    ai = _annualized_stats(ai_d); ai["mdd"] = _max_drawdown(ai_eq); ai["final"] = float(ai_eq.iloc[-1])

    weekly_to = sum(txn_cost) / total_cost_per_side if total_cost_per_side > 0 else 0
    years = len(port_daily) / 252
    annual_turnover = weekly_to / years if years > 0 else 0

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "date": port_daily.index,
        "amqs_ai_infra": amqs_eq.values, "qqq": qqq_eq.values,
        "smh": smh_eq.values, "soxx": soxx_eq.values,
        "ai_infra_basket": ai_eq.values,
        "amqs_daily": port_daily.values, "qqq_daily": qqq_d.values,
    }).to_csv(out / "backtest_equity.csv", index=False)
    pd.DataFrame(rebalance_log).to_csv(out / "backtest_positions.csv", index=False)
    pd.DataFrame(trade_log).to_csv(out / "backtest_trades.csv", index=False)
    pd.DataFrame(regime_log).to_csv(out / "backtest_regimes.csv", index=False)

    summary = pd.DataFrame([
        {"strategy": "AMQS-AI-Infra", **amqs},
        {"strategy": "QQQ", **qqq},
        {"strategy": "SMH", **smh},
        {"strategy": "SOXX", **soxx},
        {"strategy": "AI-Infra 동가중", **ai},
    ])
    summary.to_csv(out / "backtest_summary.csv", index=False)

    # --- report ---
    print()
    print("=" * 86)
    print(f"  AMQS-AI-Infra BACKTEST RESULTS  ({start} -> {end})")
    print("=" * 86)
    print(f"  {'Metric':<20}{'AMQS-AI-Infra':>16}{'QQQ':>12}{'SMH':>12}{'SOXX':>12}{'AI동가중':>12}")
    print(f"  {'-' * 84}")
    rows = [
        ("총수익률", "total", "{:>11.2%}"),
        ("CAGR", "cagr", "{:>11.2%}"),
        ("연환산 변동성", "vol", "{:>11.2%}"),
        ("Sharpe", "sharpe", "{:>12.2f}"),
        ("MDD", "mdd", "{:>11.2%}"),
        ("최종 자산", "final", "{:>12,.0f}"),
    ]
    for label, k, fmt in rows:
        amqs_fmt = ("{:>15.2%}".format(amqs[k]) if "%" in fmt else "{:>16,.0f}".format(amqs[k]) if k == "final" else "{:>16.2f}".format(amqs[k]))
        print(f"  {label:<20}{amqs_fmt}{fmt.format(qqq[k])}{fmt.format(smh[k])}{fmt.format(soxx[k])}{fmt.format(ai[k])}")
    print(f"  {'-' * 84}")
    print(f"  회전율(연환산) {annual_turnover:>.0%}  ·  리밸런싱 {len(rebalance_log)}회  ·  거래비용(왕복) {(txn_bps+slip_bps):.0f}bps")
    print(f"  vs QQQ 초과수익 {amqs['total'] - qqq['total']:+.2%}  ·  vs SMH {amqs['total'] - smh['total']:+.2%}")
    print("=" * 86)
    for f in ("backtest_equity.csv", "backtest_positions.csv", "backtest_trades.csv",
              "backtest_regimes.csv", "backtest_summary.csv"):
        print(f"  Output: {out / f}")
    print()

    return summary


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2024-01-02")
    p.add_argument("--end", default=None)
    p.add_argument("--txn-bps", type=float, default=None)
    p.add_argument("--slip-bps", type=float, default=None)
    args = p.parse_args()
    run_backtest(start=args.start, end=args.end,
                 txn_cost_bps=args.txn_bps, slippage_bps=args.slip_bps)
