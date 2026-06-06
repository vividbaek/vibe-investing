# -*- coding: utf-8 -*-
"""
ARDS-X — Regime Classifier (핵심 의사결정 엔진, v1.1)
=====================================================
2-축 레짐 맵 + 금리 축 라벨 + 히스테리시스로 현재 국면을 분류한다.

  X축 = 거시 침체 축 (Macro)   : 5-Factor Recession Composite (실데이터)  0~100
  Y축 = 가격 구조 축 (Price)    : 드로다운 깊이 + 추세 붕괴 정도            0~100
  오버레이1 = 단기 과매도        : RSI / Bollinger / ATR 이탈              0~100
  오버레이2 = Rate Stress (v1.1) : 금리속도/기대인플레/채권변동성 → 하락유형 라벨

판정 우선순위:
  1. RECESSION_REBALANCE (침체 리밸런싱)  — 거시 ≥ 55 AND (DD ≤ -5% OR 추세 붕괴)
  2. DOWNTREND_DISTRIBUTION (하락/분배)   — 추세 붕괴 AND DD ≤ -12%, 거시 < 55
  3. OVERSOLD_BOUNCE (단기 과매도)        — 과매도 AND 추세 유지
  4. CORRECTION (조정)                    — DD -5%~-12%, 추세 유지, 거시 양호
  5. UPTREND_HEALTHY (정상 상승)

v1.1 추가:
  • 히스테리시스: 진입/이탈 임계값 분리(밴드) + N일 확인 후에만 공식 전환 (휩쏘 방지)
  • 하락유형 라벨(침체형/금리형/밸류형) + ARDS Tier2 TLT/IEF 조건부 핸드오프
"""

from . import config
from . import rates


STATE_KR = {
    "UPTREND_HEALTHY": "정상 상승추세", "CORRECTION": "조정",
    "OVERSOLD_BOUNCE": "단기 과매도 (반등 후보)", "DOWNTREND_DISTRIBUTION": "하락 / 분배",
    "RECESSION_REBALANCE": "자산 리밸런싱 (침체)",
}
STATE_ACTION = {
    "UPTREND_HEALTHY": "RISK_ON", "CORRECTION": "HOLD_ACCUMULATE",
    "OVERSOLD_BOUNCE": "BUY_DIP_TACTICAL", "DOWNTREND_DISTRIBUTION": "REDUCE",
    "RECESSION_REBALANCE": "DEFENSIVE_ARDS",
}
DECLINE_STATES = {"CORRECTION", "OVERSOLD_BOUNCE", "DOWNTREND_DISTRIBUTION", "RECESSION_REBALANCE"}


def _measure(macro, index_rows, complex_agg):
    """분류에 필요한 대표 가격 지표를 뽑아낸다."""
    T = config.TECH
    by_t = {r["ticker"]: r for r in index_rows}
    idx_list = [by_t[t] for t in ("^GSPC", "^NDX") if t in by_t]
    tech_ref = by_t.get("^NDX") or by_t.get("^GSPC")

    tape_dd = min([r["dd_from_high"] for r in idx_list]) if idx_list else 0.0
    breadth = complex_agg.get("breadth_above_200dma", 100.0)
    complex_dd = complex_agg.get("avg_dd_from_high", 0.0)

    idx_below_200 = any(not r["above_200dma"] for r in idx_list)
    idx_deadcross = any(not r["golden_cross"] for r in idx_list)
    breadth_weak = breadth < T["breadth_weak"]
    trend_broken = idx_below_200 or idx_deadcross or breadth_weak

    decline_score = max(complex_agg.get("avg_decline_score", 0.0),
                        tech_ref["decline_score"] if tech_ref else 0.0)
    oversold_score = max(complex_agg.get("avg_oversold_score", 0.0),
                         tech_ref["oversold_score"] if tech_ref else 0.0)
    idx_rsi = min([r["rsi14"] for r in idx_list]) if idx_list else 50.0
    price_stress = round(min(100.0, 0.6 * decline_score +
                             0.4 * min(100, -tape_dd / T["dd_bear"] * 100)), 1)
    return {
        "tape_dd": tape_dd, "breadth": breadth, "complex_dd": complex_dd,
        "trend_broken": trend_broken, "idx_below_200": idx_below_200,
        "idx_deadcross": idx_deadcross, "breadth_weak": breadth_weak,
        "decline_score": decline_score, "oversold_score": oversold_score,
        "idx_rsi": idx_rsi, "price_stress": price_stress,
    }


def raw_classify(M, m, prev_state):
    """히스테리시스 밴드를 적용해 raw 레짐을 결정 (prev_state 에 따라 임계값이 달라짐)."""
    H = config.HYSTERESIS
    # 진입/이탈 밴드: 현재 그 레짐이면 '이탈(느슨)' 임계, 아니면 '진입(엄격)' 임계
    rec_thr = H["macro_rec_exit"] if prev_state == "RECESSION_REBALANCE" else H["macro_rec_enter"]
    dd_corr = H["dd_corr_exit"] if prev_state in ("CORRECTION", "OVERSOLD_BOUNCE") else H["dd_corr_enter"]
    dd_deep = H["dd_deep_exit"] if prev_state == "DOWNTREND_DISTRIBUTION" else H["dd_deep_enter"]
    rsi_thr = H["rsi_exit"] if prev_state == "OVERSOLD_BOUNCE" else H["rsi_enter"]

    dd = m["tape_dd"]
    is_os = (m["oversold_score"] >= 55) or (m["idx_rsi"] < rsi_thr)

    if M >= rec_thr and (dd <= -dd_corr or m["trend_broken"]):
        return "RECESSION_REBALANCE"
    if m["trend_broken"] and dd <= -dd_deep:
        return "DOWNTREND_DISTRIBUTION"
    if dd <= -dd_corr:
        return "OVERSOLD_BOUNCE" if is_os else "CORRECTION"
    if is_os:
        return "OVERSOLD_BOUNCE"
    return "UPTREND_HEALTHY"


def build_verdict(state, raw_state, confirm, macro, m, rate, asof_date):
    """공식 레짐(state) 기준으로 최종 verdict dict 를 구성."""
    M = macro["composite"]
    R = rate.get("score")
    dtype = rates.decline_type(M, R, m["price_stress"]) if state in DECLINE_STATES \
        else {"code": "NONE", "kr": "해당없음", "tlt_guidance": "유의미한 하락 스트레스 없음."}

    headline, handoff = _narrative(state, M, macro, m, R, dtype)

    # 신뢰도: 거시-가격 합치 + 신호 극단성 − 결측 − 전환대기
    macro_high = M >= config.DECISION["macro_recession"]
    price_high = m["price_stress"] >= 50
    conf = 55
    conf += 18 if (macro_high == price_high) else -5
    conf += min(15, abs(M - 50) / 50 * 15)
    conf += min(12, abs(m["price_stress"] - 40) / 60 * 12)
    if macro["n_missing"] >= 2:
        conf -= 12
    if rate.get("score") is None:
        conf -= 6
    if confirm.get("pending"):
        conf -= 10                      # 전환 확인 중이면 신뢰도 하향
    conf = int(max(20, min(95, conf)))

    return {
        "state": state,
        "state_kr": STATE_KR[state],
        "action": STATE_ACTION[state],
        "confidence": conf,
        "headline": headline,
        "handoff": handoff,
        "decline_type": dtype,
        "hysteresis": confirm,
        "axes": {
            "macro": M, "macro_phase": macro["phase"], "macro_phase_kr": macro["phase_kr"],
            "price_stress": m["price_stress"],
            "rate_stress": R,
            "decline_score": round(m["decline_score"], 1),
            "oversold_score": round(m["oversold_score"], 1),
        },
        "evidence": {
            "tape_drawdown": round(m["tape_dd"], 1),
            "complex_avg_drawdown": round(m["complex_dd"], 1),
            "breadth_above_200dma": m["breadth"],
            "index_min_rsi14": round(m["idx_rsi"], 1),
            "trend_broken": m["trend_broken"],
            "idx_below_200dma": m["idx_below_200"],
            "idx_deadcross": m["idx_deadcross"],
            "breadth_weak": m["breadth_weak"],
        },
    }


def _narrative(state, M, macro, m, R, dtype):
    p = macro["phase_kr"]
    dd = m["tape_dd"]
    br = m["breadth"]
    rtxt = "" if R is None else f" · Rate Stress {R:.0f}"
    if state == "RECESSION_REBALANCE":
        h = (f"거시 침체 신호(Composite {M:.0f}, {p}{rtxt})가 가격 하락을 주도. "
             f"지수 고점 대비 {dd:.1f}%, 200일선 위 {br:.0f}%. **자산 리밸런싱(침체) 국면**.")
        ho = "➡️ ARDS / ARDS-Defense 방어 포트폴리오로 전환. 자본보존 우선."
    elif state == "DOWNTREND_DISTRIBUTION":
        h = (f"추세 붕괴 + 고점 대비 {dd:.1f}%. 거시(Composite {M:.0f}{rtxt})는 아직 침체 미만이나 "
             f"**구조적 하락/분배**.")
        ho = "➡️ '조정'으로 보지 말 것. 신규 저점매수 보류, 리스크 축소·헤지."
    elif state == "OVERSOLD_BOUNCE":
        h = (f"단기 과매도(과매도 {m['oversold_score']:.0f}, 지수 RSI {m['idx_rsi']:.0f}{rtxt}). "
             f"고점 대비 {dd:.1f}%이나 추세 유지 → **기술적 반등 후보**.")
        ho = "➡️ AMQS DIP_BUY 영역. 전술적·소규모 분할매수 + 타이트한 손절."
    elif state == "CORRECTION":
        h = (f"상승추세 내 건강한 눌림(고점 대비 {dd:.1f}%, 200일선 위 {br:.0f}%, "
             f"거시 Composite {M:.0f}{rtxt}) → **조정**.")
        ho = "➡️ 보유 유지 + 우량 빅테크/AI 인프라 분할매수."
    else:  # UPTREND_HEALTHY
        h = (f"정상 상승추세(고점 대비 {dd:.1f}%, 200일선 위 {br:.0f}%, "
             f"거시 Composite {M:.0f}/{p}{rtxt}). 하락·침체 신호 없음.")
        ho = "➡️ 리스크온 유지. AMQS 모멘텀 전략 비중 정상."

    # 하락유형 라벨 + TLT 조건부 가이던스 (하락 국면일 때)
    if dtype["code"] != "NONE":
        h += f"  하락유형: **{dtype['kr']}**."
        ho += f"  〔{dtype['kr']}〕 {dtype['tlt_guidance']}"
    return h, ho
