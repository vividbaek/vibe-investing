#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mu_hynix_pairs_full.py  (FULL VERSION)
======================================
Micron (MU) x SK hynix (000660.KS) 페어 분석 / 백테스트 / 가치 평가.

기본 스크립트(mu_hynix_pairs.py) 대비 추가된 것
------------------------------------------------
+ 거래비용(bps) 반영 순수익률
+ 백테스트 로그 CSV 3종 출력
    - backtest_daily.csv   : 날짜별 가격/수익률/z/포지션/전략 일수익률/에쿼티
    - trades.csv           : 평균회귀 전략의 트레이드 단위 로그
    - summary_metrics.csv  : 전략별 성과 + 통계적 유의성 + 판정
+ 통계적 유의성 평가
    - 연율 Sharpe
    - Newey-West(HAC) 보정 t-통계량  (자기상관 보정)
    - 블록 부트스트랩 Sharpe p-value (엣지가 진짜인지)
    - 바이앤홀드 대비 정보비율
    - 판정: 유의미 / 한계적 / 무의미

판정 기준
---------
  t_HAC >= 2.0  AND  Sharpe >= 1.0  AND  boot_p < 0.05  -> "유의미"
  t_HAC >= 1.5                                           -> "한계적"
  그 외                                                  -> "무의미"

사용 예
-------
    python mu_hynix_pairs_full.py --years 3 --cost-bps 5 --outdir out
    python mu_hynix_pairs_full.py --mock --outdir out        # 오프라인 검증
    python mu_hynix_pairs_full.py --years 3 --plot

면책: 통계적 관계 기반의 연구·교육용 보조 도구이며 투자 권유가 아니다.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint

warnings.filterwarnings("ignore")

TRADING_DAYS = 252


# --------------------------------------------------------------------------- #
# 데이터
# --------------------------------------------------------------------------- #
def load_prices(years: int) -> pd.DataFrame:
    import yfinance as yf
    tickers = {"MU": "MU", "HYNIX_KRW": "000660.KS", "USDKRW": "KRW=X"}
    series = {}
    for name, tk in tickers.items():
        df = yf.download(tk, period=f"{years}y", auto_adjust=True, progress=False)
        if df is None or df.empty:
            raise RuntimeError(f"데이터를 받지 못했습니다: {tk}")
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        series[name] = close
    px = pd.concat(series, axis=1)
    px.columns = list(tickers.keys())
    px = px.dropna()
    if len(px) < 120:
        raise RuntimeError(f"공통 거래일이 너무 적습니다: {len(px)}일")
    return px


def make_mock(years: int = 3, seed: int = 7, leadlag: bool = True) -> pd.DataFrame:
    """검증용 합성 데이터. leadlag=True면 MU가 하루 선행하는 구조를 주입."""
    rng = np.random.default_rng(seed)
    n = years * TRADING_DAYS
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    common = rng.normal(0, 0.018, n)
    mu_ret = 0.0004 + 0.9 * common + rng.normal(0, 0.012, n)
    # 하이닉스는 당일 공통충격 + (선행 옵션) 전일 MU 충격의 일부를 따라감
    hy_ret = 0.0002 + 0.55 * common + rng.normal(0, 0.013, n)
    if leadlag:
        hy_ret[1:] += 0.35 * mu_ret[:-1]      # MU(t-1) -> Hynix(t)
    fx_ret = rng.normal(0, 0.004, n)
    mu = 80 * np.exp(np.cumsum(mu_ret))
    hy = 90000 * np.exp(np.cumsum(hy_ret))
    fx = 1330 * np.exp(np.cumsum(fx_ret))
    return pd.DataFrame({"MU": mu, "HYNIX_KRW": hy, "USDKRW": fx}, index=idx)


def to_usd_logprices(px: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=px.index)
    out["MU"] = px["MU"]
    out["HYNIX_USD"] = px["HYNIX_KRW"] / px["USDKRW"]
    out["USDKRW"] = px["USDKRW"]
    out["lMU"] = np.log(out["MU"])
    out["lHY"] = np.log(out["HYNIX_USD"])
    out["rMU"] = out["lMU"].diff()
    out["rHY"] = out["lHY"].diff()
    out["rFX"] = np.log(out["USDKRW"]).diff()
    return out.dropna()


# --------------------------------------------------------------------------- #
# 상관 / 공적분 / 스프레드
# --------------------------------------------------------------------------- #
def leadlag_table(d: pd.DataFrame, max_lag: int = 3) -> pd.DataFrame:
    rows = []
    for k in range(-max_lag, max_lag + 1):
        pair = pd.concat([d["rMU"].shift(k), d["rHY"]], axis=1).dropna()
        r, p = stats.pearsonr(pair.iloc[:, 0], pair.iloc[:, 1])
        rows.append({"lag_MU_lead": k, "corr": round(r, 4),
                     "p_value": round(p, 4), "n": len(pair),
                     "sig5pct": "O" if p < 0.05 else "X"})
    return pd.DataFrame(rows)


@dataclass
class Cointegration:
    beta: float; const: float; adf_stat: float
    adf_p: float; eg_p: float; valid: bool


def cointegration_test(d: pd.DataFrame) -> Cointegration:
    X = sm.add_constant(d["lMU"])
    ols = sm.OLS(d["lHY"], X).fit()
    const, beta = ols.params["const"], ols.params["lMU"]
    adf_stat, adf_p = adfuller(ols.resid, autolag="AIC")[:2]
    eg_p = coint(d["lHY"], d["lMU"])[1]
    return Cointegration(beta, const, adf_stat, adf_p, eg_p,
                         (adf_p < 0.05) or (eg_p < 0.05))


def spread_zscore(d, beta, const, window=60) -> pd.Series:
    spread = d["lHY"] - (const + beta * d["lMU"])
    return (spread - spread.rolling(window).mean()) / spread.rolling(window).std()


# --------------------------------------------------------------------------- #
# 통계적 유의성
# --------------------------------------------------------------------------- #
def hac_tstat(ret: pd.Series, maxlags: int = 5) -> float:
    """평균 일수익률 != 0 에 대한 Newey-West 보정 t-통계량."""
    ret = ret.dropna()
    if len(ret) < 30 or ret.std() == 0:
        return 0.0
    X = np.ones((len(ret), 1))
    m = sm.OLS(ret.values, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return float(m.tvalues[0])


def sharpe_annual(ret: pd.Series) -> float:
    ret = ret.dropna()
    if len(ret) == 0 or ret.std() == 0:
        return 0.0
    return float(ret.mean() / ret.std() * np.sqrt(TRADING_DAYS))


def bootstrap_sharpe_p(ret: pd.Series, block: int = 20, n_boot: int = 1000,
                       seed: int = 0) -> float:
    """이동블록 부트스트랩으로 Sharpe<=0 일 확률(단측 p-value)."""
    ret = ret.dropna().values
    n = len(ret)
    if n < block * 3 or ret.std() == 0:
        return 1.0
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts_max = n - block
    sharpes = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, starts_max + 1, n_blocks)
        sample = np.concatenate([ret[s:s + block] for s in starts])[:n]
        sd = sample.std()
        sharpes[b] = 0.0 if sd == 0 else sample.mean() / sd * np.sqrt(TRADING_DAYS)
    return float((sharpes <= 0).mean())


def verdict(t_hac: float, sharpe: float, boot_p: float) -> str:
    if t_hac >= 2.0 and sharpe >= 1.0 and boot_p < 0.05:
        return "유의미 (edge likely real)"
    if t_hac >= 1.5:
        return "한계적 (marginal)"
    return "무의미 (no evidence)"


def evaluate(name: str, ret: pd.Series, bh: pd.Series | None = None,
             n_trades=None) -> dict:
    ret = ret.dropna()
    eq = (1 + ret).cumprod()
    yrs = max(len(ret) / TRADING_DAYS, 1e-9)
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if len(eq) else 0.0
    ann_vol = ret.std() * np.sqrt(TRADING_DAYS) if len(ret) else 0.0
    sharpe = sharpe_annual(ret)
    dd = (eq / eq.cummax() - 1).min() if len(eq) else 0.0
    active = ret[ret != 0]
    hit = float((active > 0).mean()) if len(active) else 0.0
    t_hac = hac_tstat(ret)
    boot_p = bootstrap_sharpe_p(ret)
    # 바이앤홀드 대비 정보비율
    info_ratio = np.nan
    if bh is not None:
        ex = (ret - bh.reindex(ret.index).fillna(0))
        if ex.std() > 0:
            info_ratio = float(ex.mean() / ex.std() * np.sqrt(TRADING_DAYS))
    return {
        "strategy": name,
        "CAGR": round(cagr, 4),
        "AnnVol": round(ann_vol, 4),
        "Sharpe": round(sharpe, 3),
        "MaxDD": round(dd, 4),
        "HitRate": round(hit, 4),
        "t_HAC": round(t_hac, 3),
        "boot_p_sharpe": round(boot_p, 4),
        "InfoRatio_vs_BH": (round(info_ratio, 3) if not np.isnan(info_ratio) else ""),
        "Trades": (n_trades if n_trades is not None else ""),
        "Days": len(ret),
        "Verdict": verdict(t_hac, sharpe, boot_p),
    }


# --------------------------------------------------------------------------- #
# 백테스트 (포지션 + 일수익률 시계열 반환)
# --------------------------------------------------------------------------- #
def bt_leadlag(d, mu_thr, cost_bps):
    """MU(t) -> Hynix(t+1). 롱숏/롱플랫 두 변형. 비용 반영."""
    sig = pd.Series(0, index=d.index)
    sig[d["rMU"] >= mu_thr] = 1
    sig[d["rMU"] <= -mu_thr] = -1
    pos_ls = sig.shift(1).fillna(0)
    pos_lf = pos_ls.clip(lower=0)
    c = cost_bps / 1e4
    ls_cost = pos_ls.diff().abs().fillna(0) * c           # 1레그(하이닉스)
    lf_cost = pos_lf.diff().abs().fillna(0) * c
    ls = pos_ls * d["rHY"] - ls_cost
    lf = pos_lf * d["rHY"] - lf_cost
    return {"pos_ls": pos_ls, "pos_lf": pos_lf,
            "ret_ls": ls, "ret_lf": lf, "ret_bh": d["rHY"]}


def bt_meanrev(d, z, beta, cost_bps, entry=2.0, exit_=0.5, stop=3.0):
    """z 기반 스프레드 매매. 트레이드 로그 동반."""
    pos = pd.Series(0.0, index=d.index)
    trades, state, entry_i = [], 0, None
    for i in range(len(z)):
        zi = z.iloc[i]
        if np.isnan(zi):
            pos.iloc[i] = state
            continue
        if state == 0:
            if entry < zi < stop:
                state, entry_i = -1, i
            elif -stop < zi < -entry:
                state, entry_i = +1, i
        else:
            if abs(zi) < exit_ or abs(zi) > stop:
                trades.append((entry_i, i, state,
                               "stop" if abs(zi) > stop else "exit"))
                state, entry_i = 0, None
        pos.iloc[i] = state
    if state != 0 and entry_i is not None:                # 미청산 강제 마감
        trades.append((entry_i, len(z) - 1, state, "open_end"))

    pair_ret = d["rHY"] - beta * d["rMU"]
    held = pos.shift(1).fillna(0)
    c = cost_bps / 1e4
    cost = held.diff().abs().fillna(0) * c * 2            # 2레그(하이닉스+MU)
    strat = held * pair_ret - cost

    # 트레이드 단위 로그
    rows = []
    for (a, b, side, reason) in trades:
        dates = d.index[a:b + 1]
        seg = strat.loc[dates]
        pnl = (1 + seg).prod() - 1
        rows.append({
            "entry_date": str(d.index[a].date()),
            "exit_date": str(d.index[b].date()),
            "side": "long_spread" if side > 0 else "short_spread",
            "entry_z": round(float(z.iloc[a]), 3),
            "exit_z": round(float(z.iloc[b]), 3),
            "holding_days": int(b - a),
            "trade_pnl": round(float(pnl), 5),
            "exit_reason": reason,
        })
    return {"pos": pos, "ret": strat, "n_trades": len(trades),
            "trades": pd.DataFrame(rows)}


# --------------------------------------------------------------------------- #
# 출력
# --------------------------------------------------------------------------- #
def hr(title="", ch="=", width=72):
    if not title:
        return ch * width
    pad = max(1, (width - len(title) - 2) // 2)
    return f"{ch*pad} {title} {ch*pad}"


def print_table(title, data):
    print(hr(title, "-"))
    klen = max(len(str(k)) for k in data)
    for k, v in data.items():
        print(f"  {str(k):<{klen}} : {v}")


def maybe_plot(d, z, eqs, outdir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("[plot] matplotlib 미설치 — 차트 생략"); return
    fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    (d["lHY"] - d["lHY"].iloc[0]).plot(ax=ax[0], label="Hynix(USD)")
    (d["lMU"] - d["lMU"].iloc[0]).plot(ax=ax[0], label="MU")
    ax[0].legend(); ax[0].set_title("Cumulative log return (USD)")
    z.plot(ax=ax[1], color="black", lw=0.9)
    for lv, c in [(2, "r"), (-2, "r"), (3, "gray"), (-3, "gray"), (0, "g")]:
        ax[1].axhline(lv, color=c, ls="--", lw=0.7)
    ax[1].set_title("Spread z-score (60d)")
    for name, e in eqs.items():
        e.plot(ax=ax[2], label=name)
    ax[2].legend(); ax[2].set_title("Strategy equity (net of costs)")
    fn = os.path.join(outdir, "mu_hynix_charts.png")
    fig.tight_layout(); fig.savefig(fn, dpi=120)
    print(f"[plot] 저장: {fn}")


# --------------------------------------------------------------------------- #
def parse_args():
    ap = argparse.ArgumentParser(description="MU x SK하이닉스 풀 버전 페어 평가")
    ap.add_argument("--years", type=int, default=3)
    ap.add_argument("--zwin", type=int, default=60)
    ap.add_argument("--cost-bps", type=float, default=5.0, help="레그당 편도 거래비용(bps)")
    ap.add_argument("--outdir", type=str, default="out")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--mock-no-leadlag", action="store_true",
                    help="mock에서 리드-래그 구조 제거(귀무 검증용)")
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--mu-earnings", type=str, default="")
    return ap.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    if args.mock:
        px = make_mock(args.years, leadlag=not args.mock_no_leadlag)
    else:
        px = load_prices(args.years)
    d = to_usd_logprices(px)

    mu_thr = d["rMU"].std()
    ll = leadlag_table(d)
    co = cointegration_test(d)
    z = spread_zscore(d, co.beta, co.const, window=args.zwin)

    # 백테스트
    A = bt_leadlag(d, mu_thr, args.cost_bps)
    B = bt_meanrev(d, z, co.beta, args.cost_bps)

    # 평가
    bh = A["ret_bh"]
    evals = [
        evaluate("LeadLag_LongShort", A["ret_ls"], bh=bh),
        evaluate("LeadLag_LongFlat",  A["ret_lf"], bh=bh),
        evaluate("BuyHold_Hynix",     bh),
        evaluate("MeanReversion_pair", B["ret"], n_trades=B["n_trades"]),
    ]
    summary = pd.DataFrame(evals)

    # ---- CSV 로그 ----
    daily = pd.DataFrame({
        "date": d.index,
        "MU": d["MU"].values, "HYNIX_USD": d["HYNIX_USD"].values,
        "USDKRW": d["USDKRW"].values,
        "rMU": d["rMU"].values, "rHY": d["rHY"].values, "z": z.values,
        "pos_leadlag_ls": A["pos_ls"].values,
        "pos_leadlag_lf": A["pos_lf"].values,
        "pos_meanrev": B["pos"].values,
        "ret_leadlag_ls": A["ret_ls"].values,
        "ret_leadlag_lf": A["ret_lf"].values,
        "ret_meanrev": B["ret"].values,
        "ret_buyhold": bh.values,
    })
    for col, src in [("eq_leadlag_ls", "ret_leadlag_ls"),
                     ("eq_leadlag_lf", "ret_leadlag_lf"),
                     ("eq_meanrev", "ret_meanrev"),
                     ("eq_buyhold", "ret_buyhold")]:
        daily[col] = (1 + daily[src].fillna(0)).cumprod()

    p_daily = os.path.join(args.outdir, "backtest_daily.csv")
    p_trades = os.path.join(args.outdir, "trades.csv")
    p_summary = os.path.join(args.outdir, "summary_metrics.csv")
    p_ll = os.path.join(args.outdir, "leadlag_corr.csv")
    daily.to_csv(p_daily, index=False)
    B["trades"].to_csv(p_trades, index=False)
    summary.to_csv(p_summary, index=False)
    ll.to_csv(p_ll, index=False)

    # ---- 콘솔 ----
    print(hr(f"MU x SK하이닉스 FULL  ({'MOCK' if args.mock else '실데이터'}, cost={args.cost_bps}bps)"))
    print(f"  표본: {d.index[0].date()} ~ {d.index[-1].date()} ({len(d)}일)")
    print("\n" + hr("리드-래그 교차상관표 (k>0=MU선행)", "-"))
    print(ll.to_string(index=False))
    print("\n" + hr("공적분", "-"))
    print(f"  beta={co.beta:.4f}  ADF p={co.adf_p:.4f}  EG p={co.eg_p:.4f}  "
          f"valid={'O' if co.valid else 'X'}")
    print(f"  현재 z-score = {z.iloc[-1]:.3f}")

    print("\n" + hr("전략 평가 (순수익률, 비용 반영)", "-"))
    show = summary[["strategy", "CAGR", "Sharpe", "MaxDD", "t_HAC",
                    "boot_p_sharpe", "InfoRatio_vs_BH", "Trades", "Verdict"]]
    print(show.to_string(index=False))

    if args.plot:
        eqs = {"LeadLag_LS": daily.set_index("date")["eq_leadlag_ls"],
               "MeanRev": daily.set_index("date")["eq_meanrev"],
               "BuyHold": daily.set_index("date")["eq_buyhold"]}
        print(); maybe_plot(d, z, eqs, args.outdir)

    print("\n" + hr("CSV 출력", "-"))
    for p in (p_daily, p_trades, p_summary, p_ll):
        print(f"  {p}")
    print("\n" + hr())
    print("  판정 기준: t_HAC>=2 & Sharpe>=1 & boot_p<0.05 → 유의미 / t_HAC>=1.5 → 한계적 / 그외 무의미")
    print("  통계적 관계 기반 보조 지표이며 투자 권유가 아님. 임계치는 워크포워드로 보정할 것.")
    print(hr())


if __name__ == "__main__":
    sys.exit(main())
