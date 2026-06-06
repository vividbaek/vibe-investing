# -*- coding: utf-8 -*-
"""
ARDS-X — Technical / 가격구조 엔진
==================================
각 종목·지수에 대해 '조정 vs 하락 vs 과매도' 판정을 위한 원자 지표를 계산한다.

핵심 3축:
  • 드로다운(Drawdown)   — 52주 고점 대비 하락폭 → "얼마나 빠졌나"
  • 추세 무결성(Trend)    — 200/50일선, 골든/데드크로스, 200DMA 기울기 → "추세가 깨졌나"
  • 과매도(Oversold)      — RSI(14), Bollinger %B, 20일선 ATR 이탈 → "단기 반등 여지"

복합체(빅테크+AI인프라) 전체에 대해서는 '폭(breadth)' = 200일선 위 종목 비중도 계산.
"""

import numpy as np
import pandas as pd

from . import config


# ---- 지표 ------------------------------------------------------------------
def rsi(series, period=14):
    d = series.diff()
    up = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def bollinger_pctb(series, period=20, k=2):
    ma = series.rolling(period).mean()
    sd = series.rolling(period).std()
    upper, lower = ma + k * sd, ma - k * sd
    rng = (upper - lower).replace(0, np.nan)
    return ((series - lower) / rng)


def atr_proxy(series, period=14):
    """종가만 있으므로 일간 변화의 절대값 EWMA 를 ATR 프록시로 사용."""
    return series.diff().abs().ewm(alpha=1 / period, adjust=False).mean()


def metrics_for(series):
    """단일 가격 시계열 → 지표 dict."""
    s = series.dropna()
    if len(s) < 60:
        return None
    last = float(s.iloc[-1])
    hi_252 = float(s.iloc[-252:].max()) if len(s) >= 252 else float(s.max())
    dd = (last / hi_252 - 1) * 100.0                       # 52주 고점 대비, 음수

    ma20 = float(s.rolling(20).mean().iloc[-1])
    ma50 = float(s.rolling(50).mean().iloc[-1])
    ma200 = float(s.rolling(200).mean().iloc[-1]) if len(s) >= 200 else float(s.rolling(min(len(s), 150)).mean().iloc[-1])

    # 200일선 기울기 (최근 21거래일 변화%)
    ma200_series = s.rolling(200 if len(s) >= 200 else min(len(s), 150)).mean().dropna()
    slope = float(ma200_series.iloc[-1] / ma200_series.iloc[-21] - 1) * 100 if len(ma200_series) > 22 else 0.0

    r = float(rsi(s).iloc[-1])
    pctb = bollinger_pctb(s).iloc[-1]
    pctb = float(pctb) if pd.notna(pctb) else 0.5
    atr = float(atr_proxy(s).iloc[-1]) or 1e-9
    atr_stretch = (ma20 - last) / atr                     # 20일선 아래로 ATR 몇 배

    # 6개월 모멘텀
    mom6 = float(last / s.iloc[-126] - 1) * 100 if len(s) >= 126 else float(last / s.iloc[0] - 1) * 100

    # 연속 음봉
    diffs = s.diff().iloc[-10:]
    down_streak = 0
    for x in reversed(diffs.tolist()):
        if x < 0:
            down_streak += 1
        else:
            break

    return {
        "last": round(last, 2),
        "dd_from_high": round(dd, 1),
        "pct_vs_50dma": round((last / ma50 - 1) * 100, 1),
        "pct_vs_200dma": round((last / ma200 - 1) * 100, 1),
        "above_200dma": last > ma200,
        "golden_cross": ma50 > ma200,             # False = 데드크로스
        "ma200_slope": round(slope, 1),
        "rsi14": round(r, 1),
        "bb_pctb": round(pctb, 2),
        "atr_stretch": round(atr_stretch, 1),
        "mom6m": round(mom6, 1),
        "down_streak": down_streak,
    }


# ---- 점수화 ----------------------------------------------------------------
def _decline_score(m):
    """0~100. 높을수록 '구조적 하락' 성격이 강함 (드로다운 깊이 + 추세 붕괴)."""
    t = config.TECH
    score = 0.0
    dd = -m["dd_from_high"]                       # 양수화
    # 드로다운 깊이 (최대 45점)
    score += min(45, dd / t["dd_bear"] * 45)
    # 200일선 이탈 (15)
    if not m["above_200dma"]:
        score += 15
    # 데드크로스 (12)
    if not m["golden_cross"]:
        score += 12
    # 200일선 하락 기울기 (최대 15)
    if m["ma200_slope"] < 0:
        score += min(15, -m["ma200_slope"] * 5)
    # 6개월 모멘텀 음수 (최대 13)
    if m["mom6m"] < 0:
        score += min(13, -m["mom6m"] / 20 * 13)
    return min(100.0, score)


def _oversold_score(m):
    """0~100. 높을수록 단기 과매도(반등 여지)."""
    t = config.TECH
    score = 0.0
    # RSI (최대 45)
    if m["rsi14"] < t["rsi_oversold"]:
        score += min(45, (t["rsi_oversold"] - m["rsi14"]) / (t["rsi_oversold"] - 10) * 45)
    # Bollinger 하단 이탈 (25)
    if m["bb_pctb"] < t["bb_oversold"]:
        score += 25
    elif m["bb_pctb"] < 0.2:
        score += 12
    # 20일선 ATR 이탈 (최대 20)
    if m["atr_stretch"] > 0:
        score += min(20, m["atr_stretch"] / t["atr_stretch"] * 20)
    # 연속 음봉 (최대 10)
    score += min(10, m["down_streak"] * 2.5)
    return min(100.0, score)


def analyze_universe(price_map, name_group):
    """
    price_map: {ticker: Series}
    name_group: {ticker: (name, group)}  (지수는 그룹 None)
    반환: per-ticker 지표+점수 리스트, 그리고 복합체 집계.
    """
    rows = []
    for t, s in price_map.items():
        m = metrics_for(s)
        if m is None:
            continue
        name, group = name_group.get(t, (t, None))
        m.update({
            "ticker": t, "name": name, "group": group,
            "decline_score": round(_decline_score(m), 1),
            "oversold_score": round(_oversold_score(m), 1),
        })
        rows.append(m)
    return rows


def aggregate(rows):
    """복합체(개별 종목들) 집계 지표."""
    if not rows:
        return {}
    n = len(rows)
    above200 = sum(1 for r in rows if r["above_200dma"])
    golden = sum(1 for r in rows if r["golden_cross"])
    return {
        "n": n,
        "breadth_above_200dma": round(above200 / n * 100, 0),
        "breadth_golden_cross": round(golden / n * 100, 0),
        "avg_dd_from_high": round(np.mean([r["dd_from_high"] for r in rows]), 1),
        "median_dd_from_high": round(float(np.median([r["dd_from_high"] for r in rows])), 1),
        "avg_rsi14": round(np.mean([r["rsi14"] for r in rows]), 1),
        "avg_decline_score": round(np.mean([r["decline_score"] for r in rows]), 1),
        "avg_oversold_score": round(np.mean([r["oversold_score"] for r in rows]), 1),
        "n_oversold": sum(1 for r in rows if r["rsi14"] < config.TECH["rsi_oversold"]),
        "n_below_200dma": n - above200,
    }
