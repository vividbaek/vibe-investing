#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mu_hynix_pairs.py
=================
Micron (MU) x SK hynix (000660.KS) 페어 분석 / 백테스트 도구.

기능
----
1. 상관 분석     : 동시점 롤링 상관(20/60/120일) + 리드-래그 교차상관표(-3~+3일)
2. 공적분 검정   : Engle-Granger (OLS 헤지비율 beta + 잔차 ADF)  -> 페어 유효성
3. 스프레드/z    : USD 환산 로그가격 스프레드의 60일 롤링 z-score
4. 현재 신호     : (A) 리드-래그 모멘텀 (MU 선행) / (B) 스프레드 평균회귀
5. 백테스트      : (A) 리드-래그 모멘텀 / (B) 평균회귀 페어 -> 성과지표

핵심 가정
---------
- 미국장은 한국장 마감 이후에 열린다. 따라서 MU의 t일 종가 정보는
  하이닉스 t+1 거래일에 반영된다. => 신호 A는 MU(t) -> Hynix(t+1) 구조.
- 가격 레벨 비교는 통화를 맞춰야 하므로 하이닉스(KRW)를 USD/KRW로 나눠
  USD 환산 후 로그가격으로 공적분/스프레드를 계산한다.
- 임계치(모멘텀 +/-, z=±2, ADF 0.05)는 출발점이며 백테스트로 보정 대상이다.

사용 예
-------
    python mu_hynix_pairs.py --years 3                 # 실데이터 (yfinance)
    python mu_hynix_pairs.py --years 3 --plot          # 차트 저장
    python mu_hynix_pairs.py --mock                    # 합성데이터로 동작 검증
    python mu_hynix_pairs.py --mu-earnings 2025-03-20,2025-06-25

면책: 통계적 관계 기반의 보조 도구이며 투자 권유가 아니다.
"""

from __future__ import annotations

import argparse
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
# 데이터 로드
# --------------------------------------------------------------------------- #
def load_prices(years: int) -> pd.DataFrame:
    """yfinance로 MU / 하이닉스 / USDKRW 일봉 수정종가를 받아 정렬한다."""
    import yfinance as yf

    period = f"{years}y"
    tickers = {"MU": "MU", "HYNIX_KRW": "000660.KS", "USDKRW": "KRW=X"}
    series = {}
    for name, tk in tickers.items():
        df = yf.download(tk, period=period, auto_adjust=True, progress=False)
        if df is None or df.empty:
            raise RuntimeError(f"데이터를 받지 못했습니다: {tk}")
        close = df["Close"]
        if isinstance(close, pd.DataFrame):  # yfinance가 MultiIndex로 줄 때 방어
            close = close.iloc[:, 0]
        series[name] = close

    px = pd.concat(series, axis=1)
    px.columns = list(tickers.keys())
    px = px.dropna()  # 세 시장 공통 거래일만 사용 (휴장일 정렬)
    if len(px) < 120:
        raise RuntimeError(f"공통 거래일이 너무 적습니다: {len(px)}일")
    return px


def make_mock(years: int = 3, seed: int = 7) -> pd.DataFrame:
    """검증용 합성 데이터: 공통 메모리 사이클 충격 + 종목 고유 노이즈."""
    rng = np.random.default_rng(seed)
    n = years * TRADING_DAYS
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)

    common = rng.normal(0, 0.018, n)          # 공통 사이클 충격
    mu_ret = 0.0003 + 0.9 * common + rng.normal(0, 0.012, n)
    hy_ret = 0.0002 + 0.85 * common + rng.normal(0, 0.013, n)
    fx_ret = rng.normal(0, 0.004, n)          # USD/KRW 변동

    mu = 80 * np.exp(np.cumsum(mu_ret))
    hy = 90000 * np.exp(np.cumsum(hy_ret))    # KRW
    fx = 1330 * np.exp(np.cumsum(fx_ret))     # KRW per USD

    return pd.DataFrame(
        {"MU": mu, "HYNIX_KRW": hy, "USDKRW": fx}, index=idx
    )


def to_usd_logprices(px: pd.DataFrame) -> pd.DataFrame:
    """하이닉스를 USD로 환산하고 로그가격/로그수익률을 만든다."""
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
# 상관 분석
# --------------------------------------------------------------------------- #
def rolling_correlations(d: pd.DataFrame) -> dict:
    res = {}
    for w in (20, 60, 120):
        res[w] = d["rMU"].rolling(w).corr(d["rHY"])
    return res


def leadlag_table(d: pd.DataFrame, max_lag: int = 3) -> pd.DataFrame:
    """corr(rMU[t-k], rHY[t]) : k>0 이면 MU가 k일 선행."""
    rows = []
    for k in range(-max_lag, max_lag + 1):
        mu_shift = d["rMU"].shift(k)
        pair = pd.concat([mu_shift, d["rHY"]], axis=1).dropna()
        r, p = stats.pearsonr(pair.iloc[:, 0], pair.iloc[:, 1])
        rows.append(
            {"lag(MU선행+)": k, "corr": round(r, 4),
             "p_value": round(p, 4), "n": len(pair),
             "유의(5%)": "O" if p < 0.05 else "X"}
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 공적분 & 스프레드
# --------------------------------------------------------------------------- #
@dataclass
class Cointegration:
    beta: float
    const: float
    adf_stat: float
    adf_p: float
    eg_p: float           # statsmodels coint() p-value
    valid: bool


def cointegration_test(d: pd.DataFrame) -> Cointegration:
    """Engle-Granger: lHY = const + beta*lMU + e, e 에 ADF."""
    X = sm.add_constant(d["lMU"])
    ols = sm.OLS(d["lHY"], X).fit()
    const, beta = ols.params["const"], ols.params["lMU"]
    resid = ols.resid
    adf_stat, adf_p = adfuller(resid, autolag="AIC")[:2]
    eg_p = coint(d["lHY"], d["lMU"])[1]
    valid = (adf_p < 0.05) or (eg_p < 0.05)
    return Cointegration(beta, const, adf_stat, adf_p, eg_p, valid)


def spread_zscore(d: pd.DataFrame, beta: float, const: float,
                  window: int = 60) -> pd.DataFrame:
    out = pd.DataFrame(index=d.index)
    out["spread"] = d["lHY"] - (const + beta * d["lMU"])
    out["mu_roll"] = out["spread"].rolling(window).mean()
    out["sd_roll"] = out["spread"].rolling(window).std()
    out["z"] = (out["spread"] - out["mu_roll"]) / out["sd_roll"]
    return out


# --------------------------------------------------------------------------- #
# 현재 신호 스냅샷
# --------------------------------------------------------------------------- #
def current_signals(d: pd.DataFrame, ll: pd.DataFrame, co: Cointegration,
                    z: pd.Series, mu_thr: float, fx_guard: float = 0.015,
                    blocked_today: bool = False) -> dict:
    last = d.index[-1]
    r_mu_prev = d["rMU"].iloc[-1]          # 직전 미국장(=하이닉스 익일 신호 재료)
    z_now = z.iloc[-1]
    r_fx = d["rFX"].iloc[-1]

    ll_pos = ll.loc[ll["lag(MU선행+)"] == 1].iloc[0]
    ll_sig_ok = (ll_pos["corr"] > 0) and (ll_pos["p_value"] < 0.05)

    # 신호 A: 리드-래그 모멘텀
    if blocked_today:
        sig_a = "관망(실적 ±3일 차단)"
    elif not ll_sig_ok:
        sig_a = "관망(리드-래그 무의미)"
    elif abs(z_now) > 2:
        sig_a = "관망(스프레드 극단)"
    elif r_mu_prev >= mu_thr:
        sig_a = "하이닉스 익일 매수"
    elif r_mu_prev <= -mu_thr:
        sig_a = "하이닉스 익일 매도/관망"
    else:
        sig_a = "관망(임계치 미달)"

    # 신호 B: 평균회귀 (공적분 유효 시)
    if not co.valid:
        sig_b = "없음(공적분 무효)"
    elif abs(z_now) > 3:
        sig_b = "진입금지(관계붕괴 의심)"
    elif z_now > 2:
        sig_b = "스프레드 매도(하이닉스 매도+MU 매수)"
    elif z_now < -2:
        sig_b = "스프레드 매수(하이닉스 매수+MU 매도)"
    elif abs(z_now) < 0.5:
        sig_b = "청산"
    else:
        sig_b = "보유/관망"

    conf = "하" if (not ll_sig_ok and not co.valid) else (
        "중" if abs(r_fx) > fx_guard else "상")
    if abs(r_fx) > fx_guard:
        conf_note = f"USD/KRW 일변동 {r_fx*100:.2f}% (>±{fx_guard*100:.1f}%) → 신호A 신뢰도 하향"
    else:
        conf_note = "환율 정상 범위"

    return {
        "데이터 기준일": str(last.date()),
        "60일 동시점 상관": round(d["rMU"].rolling(60).corr(d["rHY"]).iloc[-1], 4),
        "리드-래그 상관(MU→Hynix,+1일)": ll_pos["corr"],
        "공적분 ADF p-value": round(co.adf_p, 4),
        "공적분 EG p-value": round(co.eg_p, 4),
        "현재 헤지비율 beta": round(co.beta, 4),
        "현재 z-score": round(z_now, 3),
        "MU 직전일 수익률": f"{r_mu_prev*100:.2f}%",
        "모멘텀 임계치(±1σ)": f"{mu_thr*100:.2f}%",
        "신호 A (모멘텀)": sig_a,
        "신호 B (평균회귀)": sig_b,
        "신뢰도": conf,
        "신뢰도 근거": conf_note,
    }


# --------------------------------------------------------------------------- #
# 백테스트
# --------------------------------------------------------------------------- #
def perf_stats(daily_ret: pd.Series, n_trades=None) -> dict:
    daily_ret = daily_ret.dropna()
    if len(daily_ret) == 0 or daily_ret.std() == 0:
        return {"CAGR": 0, "AnnVol": 0, "Sharpe": 0, "MaxDD": 0,
                "HitRate": 0, "Trades": n_trades or 0, "Days": len(daily_ret)}
    eq = (1 + daily_ret).cumprod()
    yrs = len(daily_ret) / TRADING_DAYS
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    ann_vol = daily_ret.std() * np.sqrt(TRADING_DAYS)
    sharpe = (daily_ret.mean() * TRADING_DAYS) / ann_vol
    dd = (eq / eq.cummax() - 1).min()
    active = daily_ret[daily_ret != 0]
    hit = (active > 0).mean() if len(active) else 0.0
    return {"CAGR": round(cagr, 4), "AnnVol": round(ann_vol, 4),
            "Sharpe": round(sharpe, 3), "MaxDD": round(dd, 4),
            "HitRate": round(hit, 4),
            "Trades": n_trades if n_trades is not None else "-",
            "Days": len(daily_ret)}


def backtest_leadlag(d: pd.DataFrame, mu_thr: float) -> dict:
    """MU(t) 신호 -> 하이닉스(t+1) 포지션. 장중 진입 불가 가정 위해 shift."""
    sig = pd.Series(0, index=d.index)
    sig[d["rMU"] >= mu_thr] = 1
    sig[d["rMU"] <= -mu_thr] = -1
    pos = sig.shift(1).fillna(0)               # 익일 진입
    ls_ret = pos * d["rHY"]                     # 롱/숏
    lf_ret = pos.clip(lower=0) * d["rHY"]       # 롱/플랫
    bh = d["rHY"]                               # 바이앤홀드
    return {
        "LongShort": perf_stats(ls_ret),
        "LongFlat": perf_stats(lf_ret),
        "BuyHold_Hynix": perf_stats(bh),
    }


def backtest_meanreversion(d: pd.DataFrame, z: pd.Series, beta: float,
                           entry: float = 2.0, exit_: float = 0.5,
                           stop: float = 3.0) -> dict:
    """z 기반 스프레드 매매. 다음날 체결 가정(shift)."""
    pos = pd.Series(0.0, index=d.index)
    state = 0
    n_trades = 0
    for i in range(len(z)):
        zi = z.iloc[i]
        if np.isnan(zi):
            pos.iloc[i] = 0
            continue
        if state == 0:
            if entry < zi < stop:
                state = -1; n_trades += 1   # 스프레드 매도
            elif -stop < zi < -entry:
                state = +1; n_trades += 1   # 스프레드 매수
        else:
            if abs(zi) < exit_ or abs(zi) > stop:
                state = 0                    # 청산 또는 손절
        pos.iloc[i] = state

    # 스프레드 1단위 = 롱 하이닉스 - beta*MU (달러중립 근사)
    pair_ret = d["rHY"] - beta * d["rMU"]
    strat = pos.shift(1).fillna(0) * pair_ret
    return {"MeanReversion": perf_stats(strat, n_trades=n_trades)}


# --------------------------------------------------------------------------- #
# 출력
# --------------------------------------------------------------------------- #
def hr(title: str = "", ch: str = "=", width: int = 66) -> str:
    if not title:
        return ch * width
    pad = max(1, (width - len(title) - 2) // 2)
    return f"{ch*pad} {title} {ch*pad}"


def print_table(title: str, data: dict):
    print(hr(title, "-"))
    klen = max(len(str(k)) for k in data)
    for k, v in data.items():
        print(f"  {str(k):<{klen}} : {v}")


def maybe_plot(d, z, fname="mu_hynix_spread.png"):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("[plot] matplotlib 미설치 — 차트 생략")
        return
    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    (d["lHY"] - d["lHY"].iloc[0]).plot(ax=ax[0], label="Hynix(USD)")
    (d["lMU"] - d["lMU"].iloc[0]).plot(ax=ax[0], label="MU")
    ax[0].legend(); ax[0].set_title("Cumulative log return (USD)")
    z.plot(ax=ax[1], color="black", lw=0.9)
    for lv, c in [(2, "r"), (-2, "r"), (3, "gray"), (-3, "gray"), (0, "g")]:
        ax[1].axhline(lv, color=c, ls="--", lw=0.7)
    ax[1].set_title("Spread z-score (60d)")
    fig.tight_layout(); fig.savefig(fname, dpi=120)
    print(f"[plot] 저장: {fname}")


# --------------------------------------------------------------------------- #
def parse_args():
    ap = argparse.ArgumentParser(description="MU x SK하이닉스 페어 분석/백테스트")
    ap.add_argument("--years", type=int, default=3, help="조회 연수 (기본 3)")
    ap.add_argument("--zwin", type=int, default=60, help="z-score 롤링 윈도우")
    ap.add_argument("--mock", action="store_true", help="합성데이터로 동작 검증")
    ap.add_argument("--plot", action="store_true", help="스프레드 차트 저장")
    ap.add_argument("--mu-earnings", type=str, default="",
                    help="MU 실적발표일(YYYY-MM-DD,쉼표구분) ±3거래일 진입차단")
    return ap.parse_args()


def main():
    args = parse_args()
    px = make_mock(args.years) if args.mock else load_prices(args.years)
    d = to_usd_logprices(px)

    # 실적 차단 여부 (오늘 기준 ±3거래일 근처)
    blocked_today = False
    if args.mu_earnings.strip():
        dates = [pd.Timestamp(x.strip()) for x in args.mu_earnings.split(",") if x.strip()]
        for e in dates:
            window = d.index[(d.index >= e - pd.Timedelta(days=5)) &
                             (d.index <= e + pd.Timedelta(days=5))]
            if len(window) and d.index[-1] in window:
                blocked_today = True

    mu_thr = d["rMU"].std()                 # 모멘텀 임계치 = MU 일수익률 1σ
    ll = leadlag_table(d)
    co = cointegration_test(d)
    zdf = spread_zscore(d, co.beta, co.const, window=args.zwin)
    z = zdf["z"]

    print(hr(f"MU x SK하이닉스 페어 분석  ({'MOCK' if args.mock else '실데이터'})"))
    print(f"  표본기간: {d.index[0].date()} ~ {d.index[-1].date()}  ({len(d)}일)")

    print("\n" + hr("리드-래그 교차상관표  (k>0 = MU 선행)", "-"))
    print(ll.to_string(index=False))

    snap = current_signals(d, ll, co, z, mu_thr, blocked_today=blocked_today)
    print()
    print_table("현재 신호 스냅샷", snap)

    print("\n" + hr("백테스트 A: 리드-래그 모멘텀 (MU→Hynix t+1)", "-"))
    for k, v in backtest_leadlag(d, mu_thr).items():
        print_table(k, v)

    print("\n" + hr("백테스트 B: 스프레드 평균회귀 (z=±2/청산0.5/손절3)", "-"))
    for k, v in backtest_meanreversion(d, z, co.beta).items():
        print_table(k, v)

    if args.plot:
        print()
        maybe_plot(d, z)

    print("\n" + hr())
    print("  주의: 통계적 관계 기반 보조 지표이며 투자 권유가 아님.")
    print("       임계치(±1σ, z=±2, ADF 0.05)는 반드시 백테스트로 보정할 것.")
    print(hr())


if __name__ == "__main__":
    sys.exit(main())
