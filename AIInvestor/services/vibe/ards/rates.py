# -*- coding: utf-8 -*-
"""
ARDS-X — Rate Stress 서브컴포지트 + 하락유형 라벨 (v1.1)
========================================================
ARDS-X 2축(거시 침체 × 가격 스트레스)의 사각지대를 메운다:
"침체 Composite 는 낮은데(예: 32) 왜 주가가 빠지나?" → 금리 쇼크.

침체형 하락과 금리형 하락은 처방이 정반대다:
  • 침체형(disinflation) → 금리 인하 → TLT/IEF 가 헤지
  • 금리형(sticky inflation/rate shock) → TLT/IEF 는 주식과 동반 하락하는 '추가 익스포저'

Rate Stress (0~100) 구성:
  R1 10Y 금리 20일 변화(bp)        35%   — 장기금리 급등
  R2 2Y(또는 5Y) 금리 20일 변화    25%   — 정책경로 재가격
  R3 5Y 브레이크이븐 20일 변화     20%   — 기대인플레 재가속
  R4 MOVE(또는 10Y 실현변동성)     20%   — 채권 변동성

FRED(DGS2/T5YIE) 가 막히면 yfinance(^TNX/^FVX) 변화율 + 실현변동성으로 대체한다.
"""

import numpy as np

from . import config


def _clip01(x):
    return max(0.0, min(100.0, float(x)))


def _lin(x, lo, hi):
    if hi == lo:
        return 50.0
    return _clip01((x - lo) / (hi - lo) * 100.0)


def _chg_bp(series, days=20):
    """금리 시리즈(%)의 days일 변화 → bp."""
    s = series.dropna()
    if len(s) <= days:
        return None
    return float(s.iloc[-1] - s.iloc[-days - 1]) * 100.0   # %p → bp


def rate_stress(px, fred):
    """Rate Stress 서브컴포지트 + 성분 상세를 반환."""
    R = config.RATE
    parts, detail = {}, {}
    status = {}

    # R1: 10Y 금리 속도 (^TNX, yfinance)
    if "^TNX" in px:
        bp = _chg_bp(px["^TNX"], 20)
        if bp is not None:
            detail["us10y_20d_bp"] = round(bp, 1)
            parts["R1_long_yield_vel"] = _lin(bp, 0.0, R["yield_vel_bp_hi"])
            status["R1_long_yield_vel"] = "live"

    # R2: 정책경로 — 2Y(FRED DGS2) 우선, 없으면 5Y(^FVX)
    s2 = fred.get("DGS2")
    if s2 is not None:
        bp = _chg_bp(s2, 20)
        if bp is not None:
            detail["us2y_20d_bp"] = round(bp, 1)
            parts["R2_rate_path"] = _lin(bp, 0.0, R["path_vel_bp_hi"])
            status["R2_rate_path"] = "live"
    elif "^FVX" in px:
        bp = _chg_bp(px["^FVX"], 20)
        if bp is not None:
            detail["us5y_20d_bp(mkt)"] = round(bp, 1)
            parts["R2_rate_path"] = _lin(bp, 0.0, R["path_vel_bp_hi"])
            status["R2_rate_path"] = "proxy"

    # R3: 5Y 브레이크이븐 (FRED T5YIE)
    bei = fred.get("T5YIE")
    if bei is not None:
        bp = _chg_bp(bei, 20)
        if bp is not None:
            detail["bei5y_20d_bp"] = round(bp, 1)
            detail["bei5y_level"] = round(float(bei.dropna().iloc[-1]), 2)
            parts["R3_breakeven"] = _lin(bp, 0.0, R["bei_vel_bp_hi"])
            status["R3_breakeven"] = "live"

    # R4: 채권 변동성 — MOVE 우선, 없으면 10Y 실현변동성 백분위
    if "^MOVE" in px:
        s = px["^MOVE"].dropna()
        if len(s) > 130:
            pct = float((s.iloc[-252:] <= s.iloc[-1]).mean() * 100) if len(s) >= 252 \
                else float((s <= s.iloc[-1]).mean() * 100)
            detail["move_level"] = round(float(s.iloc[-1]), 1)
            detail["move_pctile_1y"] = round(pct, 0)
            parts["R4_bond_vol"] = pct
            status["R4_bond_vol"] = "live"
    if "R4_bond_vol" not in parts and "^TNX" in px:
        s = px["^TNX"].dropna()
        if len(s) > 130:
            rv = s.pct_change().rolling(20).std() * np.sqrt(252) * 100
            rv = rv.dropna()
            if len(rv) > 130:
                pct = float((rv.iloc[-252:] <= rv.iloc[-1]).mean() * 100) if len(rv) >= 252 \
                    else float((rv <= rv.iloc[-1]).mean() * 100)
                detail["us10y_realvol_pctile_1y(mkt)"] = round(pct, 0)
                parts["R4_bond_vol"] = pct
                status["R4_bond_vol"] = "proxy"

    if not parts:
        return {"score": None, "components": {}, "detail": {},
                "n_live": 0, "n_proxy": 0, "n_missing": 4}

    wsum = sum(config.RATE_WEIGHTS[k] for k in parts) or 1.0
    score = sum(config.RATE_WEIGHTS[k] * v for k, v in parts.items()) / wsum

    labels = {"R1_long_yield_vel": "10Y 금리속도", "R2_rate_path": "정책경로(2Y/5Y)",
              "R3_breakeven": "기대인플레", "R4_bond_vol": "채권변동성"}
    components = {}
    for k in config.RATE_WEIGHTS:
        components[k] = {
            "label": labels[k], "weight": config.RATE_WEIGHTS[k],
            "score": round(parts[k], 1) if k in parts else None,
            "status": status.get(k, "no data"),
        }
    return {
        "score": round(score, 1), "components": components, "detail": detail,
        "n_live": sum(1 for v in status.values() if v == "live"),
        "n_proxy": sum(1 for v in status.values() if v == "proxy"),
        "n_missing": 4 - len(parts),
    }


# ---------------------------------------------------------------------------
# 하락유형 라벨
# ---------------------------------------------------------------------------
DECLINE_TYPES = {
    "RECESSION_DRIVEN": ("침체형", "TLT/IEF 듀레이션 = 헤지 (금리 인하 수혜). ARDS Tier 2 장기국채 비중 활성화 OK."),
    "RATE_DRIVEN":      ("금리형", "⚠️ TLT/IEF = 추가 익스포저 (주식과 동반 하락). ARDS Tier 2 장기국채 축소 → 단기채(BIL/SHV)·금(GLD) 대체."),
    "VALUATION_DRIVEN": ("밸류에이션형", "금리·침체 무관한 멀티플 압축/크라우딩 청산. TLT 헤지 효과 제한적, 현금·인버스(SH/PSQ)가 더 적합."),
    "NONE":             ("해당없음", "유의미한 하락 스트레스 없음."),
}


def decline_type(macro_composite, rate_score, price_stress):
    """가격 스트레스가 의미있을 때만 하락의 '원인'을 라벨링."""
    R = config.RATE
    D = config.DECISION
    if price_stress < R["label_min_stress"]:
        code = "NONE"
    elif macro_composite >= D["macro_recession"]:
        code = "RECESSION_DRIVEN"
    elif rate_score is not None and rate_score >= R["stress_high"]:
        code = "RATE_DRIVEN"
    else:
        code = "VALUATION_DRIVEN"
    kr, guidance = DECLINE_TYPES[code]
    return {"code": code, "kr": kr, "tlt_guidance": guidance}
