# -*- coding: utf-8 -*-
"""
ARDS-X — 5-Factor Recession Composite (실데이터판)
==================================================
ARDS 원본은 LLM 이 점수를 '추정' 했지만, 여기서는 FRED 무료 CSV + 시장 데이터로
직접 계산한다. 각 성분은 0~100 으로 정규화 후 ARDS 가중치로 합산.

  A 수익률 곡선 (30%)  : T10Y3M / T10Y2Y  (음수일수록 침체 신호)
  B Sahm Rule  (25%)  : 실업률 3M MA - 직전 12M 최저  (≥0.50 → 트리거)
  C ISM 프록시 (15%)  : 구리/금 비율 + 경기민감주(XLI) 추세  (제조업 펄스 대용)
  D LEI 프록시 (15%)  : 신규실업청구(역방향) + 주택허가 6M 변화  (FRED 무료 성분)
  E 신용/금융 (15%)   : HY OAS + Chicago Fed NFCI

각 성분은 '실데이터 live' 인지 '프록시/추정 estimated' 인지 라벨을 함께 반환한다.
"""

import numpy as np
import pandas as pd

from . import config
from . import datafeed


def _clip01(x):
    return max(0.0, min(100.0, float(x)))


def _lin(x, lo, hi):
    """x 가 lo→hi 로 갈수록 0→100. lo>hi 면 반대 방향."""
    if hi == lo:
        return 50.0
    return _clip01((x - lo) / (hi - lo) * 100.0)


# ---------------------------------------------------------------------------
# A. 수익률 곡선 역전 (30%)
# ---------------------------------------------------------------------------
def factor_yield_curve(fred, px=None):
    px = px or {}
    s3m = fred.get("T10Y3M")
    s2y = fred.get("T10Y2Y")
    status = "live"
    detail = {}
    scores = []

    # FRED 가 막히면 yfinance 국채금리로 스프레드를 직접 계산 (프록시)
    if s3m is None and ("^TNX" in px and "^IRX" in px):
        tnx, irx = px["^TNX"].dropna(), px["^IRX"].dropna()
        common = tnx.index.intersection(irx.index)
        if len(common) > 30:
            s3m = (tnx.loc[common] - irx.loc[common])
            status = "proxy"
    if s2y is None and ("^TNX" in px and "^FVX" in px):
        tnx, fvx = px["^TNX"].dropna(), px["^FVX"].dropna()
        common = tnx.index.intersection(fvx.index)
        if len(common) > 30:
            s2y = (tnx.loc[common] - fvx.loc[common])   # 10Y-5Y 대용
            status = "proxy"

    if s3m is None and s2y is None:
        return None, "no data", {}

    if s3m is not None:
        v = float(s3m.iloc[-1])
        detail["T10Y3M" if status == "live" else "T10Y3M(mkt)"] = round(v, 2)
        # +1.50%p(정상) → 0 점,  -0.50%p(깊은 역전) → 100 점
        scores.append(_lin(v, 1.50, -0.50))
        # "역전 후 정상화(un-inversion)" 창 가산점
        recent = s3m.iloc[-378:] if len(s3m) > 378 else s3m
        if v > 0 and (recent.min() < 0):
            detail["un_inversion_window"] = True
            scores[-1] = _clip01(scores[-1] + 18)
    if s2y is not None:
        v2 = float(s2y.iloc[-1])
        detail["T10Y2Y" if status == "live" else "T10Y5Y(mkt)"] = round(v2, 2)
        scores.append(_lin(v2, 1.50, -0.50))
    return float(np.mean(scores)), status, detail


# ---------------------------------------------------------------------------
# B. Sahm Rule (25%)
# ---------------------------------------------------------------------------
def factor_sahm(fred):
    s = fred.get("UNRATE")
    if s is None or len(s) < 15:
        return None, "no data", {}
    ma3 = s.rolling(3).mean()
    cur = float(ma3.iloc[-1])
    trough = float(ma3.iloc[-12:].min())   # 직전 12개월 최저
    gap = cur - trough
    detail = {"unrate": round(float(s.iloc[-1]), 1),
              "unrate_3m_ma": round(cur, 2),
              "sahm_gap": round(gap, 2)}
    # gap 0.0 → 0점, 0.50(트리거) → 100점
    score = _lin(gap, 0.0, 0.50)
    return score, "live", detail


# ---------------------------------------------------------------------------
# C. ISM 제조업 프록시 (15%)  — 구리/금 + 경기민감주 추세
# ---------------------------------------------------------------------------
def factor_ism_proxy(px):
    """
    ISM PMI 는 유료. 대용으로 'Dr. Copper' (구리/금 상대강도) + XLI(산업재)/SPY
    추세를 쓴다. 산업 펄스가 식을수록(상대강도 하락) 점수 ↑.
    """
    detail = {}
    sub = []
    # 구리/금
    cop = px.get("CPER"); gold = px.get("GLD")
    if cop is not None and gold is not None:
        ratio = (cop / gold).dropna()
        if len(ratio) > 130:
            chg = float(ratio.iloc[-1] / ratio.iloc[-126] - 1) * 100  # 6M 변화%
            detail["copper_gold_6m_chg"] = round(chg, 1)
            # +15% → 0점(확장),  -15% → 100점(수축)
            sub.append(_lin(chg, 15.0, -15.0))
    # 산업재 상대강도
    xli = px.get("XLI"); spy = px.get("SPY")
    if xli is not None and spy is not None:
        rs = (xli / spy).dropna()
        if len(rs) > 130:
            chg = float(rs.iloc[-1] / rs.iloc[-126] - 1) * 100
            detail["xli_spy_6m_chg"] = round(chg, 1)
            sub.append(_lin(chg, 8.0, -8.0))
    if not sub:
        return None, "no data", detail
    return float(np.mean(sub)), "proxy", detail


# ---------------------------------------------------------------------------
# D. LEI 프록시 (15%)  — 신규실업청구(역방향) + 주택허가
# ---------------------------------------------------------------------------
def factor_lei_proxy(fred):
    detail = {}
    sub = []
    claims = fred.get("ICSA")
    if claims is not None and len(claims) > 30:
        c = claims.rolling(4).mean()                 # 4주 평균
        chg = float(c.iloc[-1] / c.iloc[-26] - 1) * 100  # ~6M 변화%
        detail["claims_6m_chg"] = round(chg, 1)
        # 청구건수는 늘수록 침체 → +25% → 100점, -25% → 0점
        sub.append(_lin(chg, -25.0, 25.0))
    permit = fred.get("PERMIT")
    if permit is not None and len(permit) > 8:
        chg = float(permit.iloc[-1] / permit.iloc[-6] - 1) * 100  # 6M 변화%
        detail["permits_6m_chg"] = round(chg, 1)
        # 허가는 줄수록 침체 → -15% → 100점, +15% → 0점
        sub.append(_lin(chg, 15.0, -15.0))
    if not sub:
        return None, "no data", detail
    return float(np.mean(sub)), "proxy", detail


# ---------------------------------------------------------------------------
# E. 신용 & 금융상황 (15%)
# ---------------------------------------------------------------------------
def factor_credit(fred, px=None):
    px = px or {}
    oas = fred.get("BAMLH0A0HYM2")
    nfci = fred.get("NFCI")
    detail = {}
    sub = []
    status = "live"
    if oas is not None:
        v = float(oas.iloc[-1])          # 단위: %p (예: 3.00 = 300bp)
        detail["hy_oas_bp"] = int(round(v * 100))
        # 250bp(평온) → 0점, 600bp(침체임박) → 100점
        sub.append(_lin(v, 2.50, 6.00))
    if nfci is not None:
        v = float(nfci.iloc[-1])         # 0 근방 중립, 양수=긴축
        detail["nfci"] = round(v, 2)
        sub.append(_lin(v, -0.50, 0.50))

    # FRED 신용 데이터가 없으면 HYG(하이일드) vs IEF(국채) 상대강도로 신용 스트레스 추정
    if not sub and ("HYG" in px and "IEF" in px):
        hyg, ief = px["HYG"].dropna(), px["IEF"].dropna()
        common = hyg.index.intersection(ief.index)
        if len(common) > 130:
            rs = (hyg.loc[common] / ief.loc[common])
            chg = float(rs.iloc[-1] / rs.iloc[-63] - 1) * 100   # 3M 상대강도 변화%
            detail["hyg_ief_3m_chg"] = round(chg, 1)
            # 하이일드가 국채 대비 약할수록(음수) 신용 스트레스 ↑
            sub.append(_lin(chg, 4.0, -8.0))
            # HYG 52주 고점 대비 드로다운도 반영
            dd = float(hyg.iloc[-1] / hyg.iloc[-252:].max() - 1) * 100 if len(hyg) >= 252 else 0.0
            detail["hyg_drawdown"] = round(dd, 1)
            sub.append(_lin(dd, -1.0, -12.0))
            status = "proxy"

    if not sub:
        return None, "no data", {}
    return float(np.mean(sub)), status, detail


# ---------------------------------------------------------------------------
# 종합
# ---------------------------------------------------------------------------
def recession_composite(fred, px):
    factors = {
        "A_yield_curve": factor_yield_curve(fred, px),
        "B_sahm":        factor_sahm(fred),
        "C_ism_proxy":   factor_ism_proxy(px),
        "D_lei_proxy":   factor_lei_proxy(fred),
        "E_credit":      factor_credit(fred, px),
    }
    # 결측 성분은 가중치에서 제외 후 재정규화
    avail = {k: v for k, v in factors.items() if v[0] is not None}
    wsum = sum(config.RECESSION_WEIGHTS[k] for k in avail) or 1.0
    composite = sum(config.RECESSION_WEIGHTS[k] * v[0] for k, v in avail.items()) / wsum

    # Phase 판정
    phase_code, phase_kr = "EXPANSION", "확장기"
    for hi, code, kr in config.MACRO_PHASES:
        if composite < hi:
            phase_code, phase_kr = code, kr
            break

    components = {}
    labels = {
        "A_yield_curve": "수익률 곡선", "B_sahm": "Sahm Rule",
        "C_ism_proxy": "ISM 프록시", "D_lei_proxy": "LEI 프록시",
        "E_credit": "신용/금융",
    }
    for k, (score, status, detail) in factors.items():
        components[k] = {
            "label": labels[k],
            "weight": config.RECESSION_WEIGHTS[k],
            "score": None if score is None else round(score, 1),
            "status": status,           # live / proxy / no data
            "detail": detail,
        }

    return {
        "composite": round(composite, 1),
        "phase": phase_code,
        "phase_kr": phase_kr,
        "n_live": sum(1 for v in factors.values() if v[1] == "live"),
        "n_proxy": sum(1 for v in factors.values() if v[1] == "proxy"),
        "n_missing": sum(1 for v in factors.values() if v[0] is None),
        "components": components,
    }
