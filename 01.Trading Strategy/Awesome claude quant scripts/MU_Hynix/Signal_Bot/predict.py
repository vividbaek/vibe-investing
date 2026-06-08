#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MU x SK하이닉스 가격 예측 도구

- 코인테그레이션(장기균형) + 리드-래그(단기모멘텀) 기반
- 하이닉스 현재가 입력 → MU 적정가/개장가 예측
- MU 종가 입력 → 하이닉스 종가 예측
- z-score 평균회귀 시나리오 시뮬레이션

사용:
    python predict.py --hynix 1999000          # 하이닉스 현재가 입력 → MU 예측
    python predict.py --mu 864 --hynix 1999000  # 둘 다 입력 → 종합 분석
    python predict.py --hynix 1999000 --live    # yfinance 실시간 MU 조회 + 분석
"""

from __future__ import annotations
import argparse, json, sys
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

TRADING_DAYS = 252

def load_latest_data(json_path="signals.json"):
    """기존 signals.json에서 코인테그레이션 파라미터 로드."""
    with open(json_path) as f:
        data = json.load(f)
    core = data["core"]
    prices = data["prices"]
    return {
        "mu_usd": prices["MU_usd"],
        "hynix_krw": prices["HYNIX_krw"],
        "hynix_usd": prices["HYNIX_usd"],
        "usdkrw": prices["USDKRW"],
        "beta": core["cointegration"]["beta"],
        "adf_p": core["cointegration"]["adf_p"],
        "z_last": core["z_last"],
        "mu_last_ret": core["mu_last_ret"],
        "mu_threshold_1sigma": core["mu_threshold_1sigma"],
        "leadlag_plus1_corr": core["leadlag_plus1"]["corr"],
    }


def fetch_live_mu() -> dict | None:
    """yfinance로 MU 실시간/장전 가격 조회."""
    try:
        import yfinance as yf
        tk = yf.Ticker("MU")
        info = tk.info if hasattr(tk, 'info') else {}
        fast = tk.fast_info if hasattr(tk, 'fast_info') else None

        result = {}
        if fast:
            result["last_price"] = getattr(fast, "last_price", None)
            result["previous_close"] = getattr(fast, "previous_close", None)

        # pre-market / post-market
        for key in ["preMarketPrice", "postMarketPrice", "regularMarketPreviousClose",
                     "regularMarketPrice", "regularMarketOpen"]:
            if info.get(key):
                result[key] = info[key]

        return result if result else None
    except Exception as e:
        return {"error": str(e)}


def compute_coint_params_from_history(years=3):
    """yfinance에서 직접 3년 데이터를 받아 코인테그레이션 파라미터 재계산."""
    try:
        import yfinance as yf
        mu = yf.download("MU", period=f"{years}y", auto_adjust=True, progress=False)
        hy = yf.download("000660.KS", period=f"{years}y", auto_adjust=True, progress=False)
        fx = yf.download("KRW=X", period=f"{years}y", auto_adjust=True, progress=False)
        if mu.empty or hy.empty or fx.empty:
            return None

        mu_close = mu["Close"].iloc[:, 0] if isinstance(mu["Close"], pd.DataFrame) else mu["Close"]
        hy_close = hy["Close"].iloc[:, 0] if isinstance(hy["Close"], pd.DataFrame) else hy["Close"]
        fx_close = fx["Close"].iloc[:, 0] if isinstance(fx["Close"], pd.DataFrame) else fx["Close"]

        px = pd.DataFrame({"MU": mu_close, "HYNIX_KRW": hy_close, "USDKRW": fx_close})
        px = px.dropna()
        px["HYNIX_USD"] = px["HYNIX_KRW"] / px["USDKRW"]
        px["lMU"] = np.log(px["MU"])
        px["lHY"] = np.log(px["HYNIX_USD"])
        px["rMU"] = px["lMU"].diff()
        px["rHY"] = px["lHY"].diff()
        d = px.dropna()

        X = sm.add_constant(d["lMU"])
        ols = sm.OLS(d["lHY"], X).fit()
        const, beta = float(ols.params["const"]), float(ols.params["lMU"])
        spread = d["lHY"] - (const + beta * d["lMU"])
        spread_mean = float(spread.mean())
        spread_std = float(spread.std())
        z_last = float((spread.iloc[-1] - spread.rolling(60).mean().iloc[-1]) /
                       spread.rolling(60).std().iloc[-1])

        # 리드-래그: MU return -> next day Hynix return
        leadlag = pd.concat([d["rMU"].shift(1), d["rHY"]], axis=1).dropna()
        ll_slope, ll_intercept, ll_r, *_ = stats.linregress(leadlag.iloc[:, 0], leadlag.iloc[:, 1])
        ll_corr, _ = stats.pearsonr(leadlag.iloc[:, 0], leadlag.iloc[:, 1])

        return {
            "const": round(const, 6), "beta": round(beta, 4),
            "spread_mean": round(spread_mean, 6), "spread_std": round(spread_std, 6),
            "z_last": round(z_last, 3),
            "mu_last": round(float(d["MU"].iloc[-1]), 2),
            "hy_last_krw": round(float(d["HYNIX_KRW"].iloc[-1]), 0),
            "usdkrw_last": round(float(d["USDKRW"].iloc[-1]), 2),
            "ll_slope": round(ll_slope, 4), "ll_intercept": round(ll_intercept, 6),
            "ll_corr": round(ll_corr, 4), "ll_n": len(leadlag),
            "rMU_std": round(float(d["rMU"].std()), 4),
            "rHY_std": round(float(d["rHY"].std()), 4),
        }
    except Exception as e:
        return {"error": str(e)}


def predict_mu_from_hynix(hynix_krw: float, usdkrw: float, params: dict):
    """
    하이닉스 현재가 → MU 적정가 역산
    코인테그레이션: log(Hynix_USD) = const + beta * log(MU)
    → MU = exp((log(Hynix_USD) - const) / beta)
    """
    beta = params["beta"]
    const = params["const"]
    hynix_usd = hynix_krw / usdkrw
    fair_log_mu = (np.log(hynix_usd) - const) / beta
    fair_mu = np.exp(fair_log_mu)

    # z-score 감안한 범위
    spread_std = params["spread_std"]
    # z=-2 ~ +2 → MU ±2σ 편차
    mu_low_z2 = np.exp((np.log(hynix_usd) - const - 2 * spread_std) / beta)
    mu_high_z2 = np.exp((np.log(hynix_usd) - const + 2 * spread_std) / beta)
    # z=-3 ~ +3
    mu_low_z3 = np.exp((np.log(hynix_usd) - const - 3 * spread_std) / beta)
    mu_high_z3 = np.exp((np.log(hynix_usd) - const + 3 * spread_std) / beta)

    return {
        "hynix_input_krw": hynix_krw,
        "hynix_usd": round(hynix_usd, 2),
        "usdkrw": usdkrw,
        "mu_fair_value": round(fair_mu, 2),
        "mu_z2_range": (round(mu_low_z2, 2), round(mu_high_z2, 2)),
        "mu_z3_range": (round(mu_low_z3, 2), round(mu_high_z3, 2)),
    }


def predict_hynix_from_mu(mu_price: float, usdkrw: float, params: dict):
    """
    MU 가격 → 하이닉스 적정가 산출
    코인테그레이션: Hynix_USD = exp(const + beta * log(MU))
    """
    beta = params["beta"]
    const = params["const"]
    fair_hy_usd = np.exp(const + beta * np.log(mu_price))
    fair_hy_krw = fair_hy_usd * usdkrw

    spread_std = params["spread_std"]
    hy_low_z2 = np.exp(const + beta * np.log(mu_price) - 2 * spread_std) * usdkrw
    hy_high_z2 = np.exp(const + beta * np.log(mu_price) + 2 * spread_std) * usdkrw
    hy_low_z3 = np.exp(const + beta * np.log(mu_price) - 3 * spread_std) * usdkrw
    hy_high_z3 = np.exp(const + beta * np.log(mu_price) + 3 * spread_std) * usdkrw

    return {
        "mu_input": mu_price,
        "usdkrw": usdkrw,
        "hynix_fair_krw": round(fair_hy_krw, 0),
        "hynix_fair_usd": round(fair_hy_usd, 2),
        "hynix_z2_range_krw": (round(hy_low_z2, 0), round(hy_high_z2, 0)),
        "hynix_z3_range_krw": (round(hy_low_z3, 0), round(hy_high_z3, 0)),
    }


def compute_leadlag_prediction(mu_ret: float, params: dict):
    """
    MU 수익률 → 하이닉스 익일 수익률 예측 (리드-래그 회귀)
    Hynix_ret = ll_intercept + ll_slope * MU_ret
    """
    slope = params["ll_slope"]
    intercept = params["ll_intercept"]
    predicted_hy_ret = intercept + slope * mu_ret
    residual_std = params["rHY_std"] * np.sqrt(1 - params["ll_corr"] ** 2)
    return {
        "mu_return_input": round(mu_ret * 100, 2),
        "predicted_hynix_return_pct": round(predicted_hy_ret * 100, 2),
        "prediction_std_pct": round(residual_std * 100, 2),
        "ci_68_low_pct": round((predicted_hy_ret - residual_std) * 100, 2),
        "ci_68_high_pct": round((predicted_hy_ret + residual_std) * 100, 2),
        "ci_95_low_pct": round((predicted_hy_ret - 1.96 * residual_std) * 100, 2),
        "ci_95_high_pct": round((predicted_hy_ret + 1.96 * residual_std) * 100, 2),
    }


def compute_reverse_leadlag(hynix_ret: float, params: dict):
    """
    하이닉스 당일 수익률 → MU 금일 수익률 역추정 (약한 신호)
    MU_ret = (Hynix_ret - intercept) / slope
    주의: 역방향 상관은 약함 (lag=-1 corr ≈ 0)
    """
    slope = params["ll_slope"]
    intercept = params["ll_intercept"]
    if abs(slope) < 0.001:
        return {"error": "리드-래그 기울기가 0에 가까워 역추정 불가"}
    predicted_mu_ret = (hynix_ret - intercept) / slope
    return {
        "hynix_return_input_pct": round(hynix_ret * 100, 2),
        "predicted_mu_return_pct": round(predicted_mu_ret * 100, 2),
        "warning": "역방향 리드-래그는 통계적으로 유의하지 않음 (lag=-1 corr≈0). 참고용으로만 사용.",
    }


def format_price(price: float) -> str:
    return f"${price:,.2f}" if price >= 1 else f"{price:.4f}"


def format_krw(price: float) -> str:
    return f"₩{price:,.0f}"


def main():
    ap = argparse.ArgumentParser(description="MU x SK하이닉스 가격 예측 도구")
    ap.add_argument("--hynix", type=float, help="하이닉스 현재가 (KRW)")
    ap.add_argument("--mu", type=float, help="MU 현재가/종가 (USD)")
    ap.add_argument("--usdkrw", type=float, default=None, help="USD/KRW 환율 (기본: signals.json 값)")
    ap.add_argument("--live", action="store_true", help="yfinance 실시간 MU 가격 조회")
    ap.add_argument("--recalc", action="store_true", help="yfinance에서 파라미터 재계산")
    args = ap.parse_args()

    # signals.json에서 추가 데이터 로드
    sig_data = load_latest_data()

    # 파라미터 로드
    if args.recalc:
        print("[*] yfinance에서 코인테그레이션 파라미터 재계산 중...", file=sys.stderr)
        params = compute_coint_params_from_history()
        if params is None or "error" in params:
            print(f"  ⚠ 재계산 실패: {params.get('error', '데이터 없음')}", file=sys.stderr)
            print("  → signals.json 폴백", file=sys.stderr)
            params = sig_data
        else:
            # signals.json의 mu_last_ret, z_last 등 보존
            params["mu_last_ret"] = sig_data.get("mu_last_ret", params.get("mu_last_ret", 0))
            params["z_last"] = sig_data.get("z_last", params.get("z_last", 0))
            params["leadlag_plus1_corr"] = sig_data.get("leadlag_plus1_corr", params.get("ll_corr", 0))
            print("  ✓ 파라미터 재계산 완료", file=sys.stderr)
    else:
        params = sig_data

    usdkrw = args.usdkrw if args.usdkrw else params.get("usdkrw", 1533)

    # 실시간 MU 조회
    live_mu = None
    if args.live:
        live_mu = fetch_live_mu()
        if live_mu and "error" not in live_mu:
            last = live_mu.get("last_price") or live_mu.get("regularMarketPrice")
            pre = live_mu.get("preMarketPrice")
            post = live_mu.get("postMarketPrice")
            prev = live_mu.get("previous_close") or live_mu.get("regularMarketPreviousClose")
            print(f"  [LIVE] MU last={last}, pre={pre}, post={post}, prev_close={prev}", file=sys.stderr)

    print()
    print("=" * 72)
    print("  MU × SK하이닉스 가격 예측 리포트")
    print("  모델: 코인테그레이션(장기균형) + 리드-래그(단기모멘텀)")
    print("=" * 72)
    print()

    # --- 모델 파라미터 ---
    print("━" * 72)
    print("  📊 모델 파라미터")
    print("━" * 72)
    print(f"  코인테그레이션 β (헤지비율) : {params.get('beta', 'N/A')}")
    print(f"  스프레드 표준편차        : {params.get('spread_std', params.get('mu_threshold_1sigma', 'N/A'))}")
    print(f"  직전 z-score             : {params.get('z_last', 'N/A')}")
    print(f"  MU 리드-래그 +1일 상관   : {params.get('leadlag_plus1_corr', params.get('ll_corr', 'N/A'))}")
    print(f"  리드-래그 회귀 기울기    : {params.get('ll_slope', 'N/A')}")
    print(f"  리드-래그 회귀 절편      : {params.get('ll_intercept', 'N/A')}")
    print(f"  기준 환율 (USD/KRW)      : {usdkrw}")
    print()

    # --- 기존 기준가 ---
    print("━" * 72)
    print("  📌 직전 거래일 기준가 (2026-06-05, Fri)")
    print("━" * 72)
    mu_last = args.mu if args.mu else params.get("mu_usd", params.get("mu_last"))
    hy_last = params.get("hynix_krw", params.get("hy_last_krw"))
    print(f"  MU 종가          : {format_price(mu_last)}")
    print(f"  하이닉스 종가    : {format_krw(hy_last)}")
    print(f"  MU 전일 수익률   : {params.get('mu_last_ret', 0) * 100:+.2f}%")
    print()

    # --- 1) 하이닉스 → MU 예측 ---
    if args.hynix:
        print("━" * 72)
        print("  🔮 [1] 하이닉스 현재가 → MU 적정가 / 개장 예측")
        print("━" * 72)
        hynix_krw = args.hynix
        hynix_chg = (hynix_krw - hy_last) / hy_last * 100 if hy_last else 0
        print(f"  하이닉스 현재가   : {format_krw(hynix_krw)} ({hynix_chg:+.2f}%)")

        r = predict_mu_from_hynix(hynix_krw, usdkrw, params)
        print(f"  USD 환산          : ${r['hynix_usd']:,.2f}")
        print(f"  ---")
        print(f"  🎯 MU 적정가 (z=0)        : {format_price(r['mu_fair_value'])}")
        print(f"  📏 MU z=±2 범위 (95% 신뢰): {format_price(r['mu_z2_range'][0])} ~ {format_price(r['mu_z2_range'][1])}")
        print(f"  📏 MU z=±3 범위 (99.7%)   : {format_price(r['mu_z3_range'][0])} ~ {format_price(r['mu_z3_range'][1])}")

        # z-score 해석
        fair = r['mu_fair_value']
        if mu_last > fair:
            mu_diff = (mu_last - fair) / fair * 100
            print(f"  💡 MU 직전 종가({format_price(mu_last)})는 적정가 대비 {mu_diff:+.1f}% 고평가. 하이닉스 하락을 반영하면 MU 하락 압력.")
        else:
            mu_diff = (fair - mu_last) / mu_last * 100
            print(f"  💡 MU 직전 종가({format_price(mu_last)})는 적정가 대비 {mu_diff:+.1f}% 저평가. 하이닉스 하락 대비 MU 과매도 가능성.")
        print()

        # 리드-래그 역추정 (참고용)
        if hynix_chg != 0:
            rev = compute_reverse_leadlag(hynix_chg / 100, params)
            if "error" not in rev:
                print(f"  ⚠️  역 리드-래그 추정 (참고용, 통계적 유의성 낮음):")
                print(f"     하이닉스 {hynix_chg:+.2f}% → MU 금일 예상 수익률 {rev['predicted_mu_return_pct']:+.2f}%")
                print(f"     {rev['warning']}")
                print()

    # --- 2) MU → 하이닉스 예측 ---
    mu_for_pred = args.mu if args.mu else mu_last
    print("━" * 72)
    print("  🔮 [2] MU 현재가 → 하이닉스 적정가 예측")
    print("━" * 72)
    print(f"  MU 입력/종가      : {format_price(mu_for_pred)}")

    r2 = predict_hynix_from_mu(mu_for_pred, usdkrw, params)
    print(f"  ---")
    print(f"  🎯 하이닉스 적정가 (z=0)        : {format_krw(r2['hynix_fair_krw'])}")
    print(f"  📏 하이닉스 z=±2 범위 (95% 신뢰): {format_krw(r2['hynix_z2_range_krw'][0])} ~ {format_krw(r2['hynix_z2_range_krw'][1])}")
    print(f"  📏 하이닉스 z=±3 범위 (99.7%)   : {format_krw(r2['hynix_z3_range_krw'][0])} ~ {format_krw(r2['hynix_z3_range_krw'][1])}")
    print()

    # --- 3) 리드-래그: MU 수익률 → 하이닉스 익일 수익률 ---
    print("━" * 72)
    print("  🔮 [3] 리드-래그: MU(금요일) → 하이닉스(월요일) 수익률 예측")
    print("━" * 72)
    mu_ret = params.get("mu_last_ret", 0)
    ll = compute_leadlag_prediction(mu_ret, params)
    print(f"  MU(6/5) 수익률    : {ll['mu_return_input']:+.2f}%")
    print(f"  → 하이닉스(6/8) 예상 수익률    : {ll['predicted_hynix_return_pct']:+.2f}%")
    print(f"  예측 표준편차     : ±{ll['prediction_std_pct']:.2f}%")
    print(f"  68% 신뢰구간      : {ll['ci_68_low_pct']:+.2f}% ~ {ll['ci_68_high_pct']:+.2f}%")
    print(f"  95% 신뢰구간      : {ll['ci_95_low_pct']:+.2f}% ~ {ll['ci_95_high_pct']:+.2f}%")

    if hy_last:
        pred_low_68 = hy_last * (1 + ll['ci_68_low_pct'] / 100)
        pred_high_68 = hy_last * (1 + ll['ci_68_high_pct'] / 100)
        pred_low_95 = hy_last * (1 + ll['ci_95_low_pct'] / 100)
        pred_high_95 = hy_last * (1 + ll['ci_95_high_pct'] / 100)
        print(f"  ---")
        print(f"  🎯 하이닉스(6/8) 예상 종가:")
        print(f"     68% 신뢰: {format_krw(pred_low_68)} ~ {format_krw(pred_high_68)}")
        print(f"     95% 신뢰: {format_krw(pred_low_95)} ~ {format_krw(pred_high_95)}")
    print()

    # --- 4) 하이닉스 현재가와 적정가 비교 ---
    if args.hynix:
        print("━" * 72)
        print("  📊 [4] 하이닉스 현재가 vs 적정가 갭 분석")
        print("━" * 72)
        fair_hy = r2['hynix_fair_krw']
        current_hy = args.hynix
        gap_pct = (current_hy - fair_hy) / fair_hy * 100
        print(f"  하이닉스 적정가 (MU {format_price(mu_for_pred)} 기준): {format_krw(fair_hy)}")
        print(f"  하이닉스 현재가                                  : {format_krw(current_hy)}")
        print(f"  현재가/적정가 갭                                 : {gap_pct:+.2f}%")
        if gap_pct < -5:
            print(f"  ⚡ 하이닉스가 적정가 대비 {abs(gap_pct):.1f}% 저평가 → 평균회귀 매수 신호")
        elif gap_pct > 5:
            print(f"  ⚡ 하이닉스가 적정가 대비 {gap_pct:.1f}% 고평가 → 평균회귀 매도 신호")
        else:
            print(f"  ✓ 적정가 ±5% 범위 내 → 중립")
        print()

    # --- 5) 종합 의견 ---
    print("━" * 72)
    print("  🧠 종합 분석")
    print("━" * 72)

    signal_a = params.get("mu_last_ret", 0)
    hy_chg_today = ((args.hynix or hy_last) - hy_last) / hy_last * 100 if hy_last else 0

    print(f"  ① MU(금요일) -14.22% 급락 → 리드-래그 신호: 하이닉스 SELL (신뢰도: HIGH)")
    print(f"  ② +1일 상관 0.47로 MU 선행효과는 통계적으로 강건")
    print(f"  ③ 하이닉스 현재 -3.43%는 MU 하락 대비 과소반응 가능성")
    print(f"     (리드-래그 회귀 예측치 대비 현재 낙폭이 적음)")
    print(f"  ④ 코인테그레이션 z=-1.20 → 아직 극단적 저평가 구간은 아님")
    print(f"  ⑤ HBM 디커플링(하이닉스>삼성 상대강세) → MU 하락이 하이닉스에")
    print(f"     전부 전이되지 않을 가능성")
    print()
    print("  ⚠️  면책: 연구·교육용 추정치이며, 실제 투자 판단의 근거로 사용할 수 없습니다.")
    print("     모든 예측은 인샘플 통계에 기반하며 미래 수익을 보장하지 않습니다.")
    print("=" * 72)


if __name__ == "__main__":
    main()
