# -*- coding: utf-8 -*-
"""
ARDS-X — Runner
===============
전체 파이프라인을 실행하고 대시보드용 JSON 을 생성한다.

    python run.py                 # 기본 실행 → ../dashboard/data/latest.json
    python run.py --print         # 결과를 콘솔에도 요약 출력
    python run.py --out path.json # 출력 경로 지정

데이터는 전부 무료(yfinance + FRED CSV). 네트워크가 없으면 캐시로 폴백한다.
"""

import argparse
import datetime as dt
import json
import os
import sys

from . import config
from . import datafeed
from . import macro as macro_mod
from . import technical
from . import classifier
from . import rates


# ─── Azure 적응: 상태 I/O 를 외부 callback 으로 우회 가능하게 ─────────────────
# Runner 가 Blob 에서 읽어온 dict 을 주입하고, build() 가 끝난 뒤 다시 회수.
# 기본값(None) 이면 원본대로 로컬 파일 사용 — CLI 호환성 유지.
_state_loader = None  # type: ignore[var-annotated]
_state_saver = None   # type: ignore[var-annotated]


def configure_state_io(loader=None, saver=None):
    """ARDS-X 의 _load_state / _save_state 를 외부 함수로 대체.

    loader: () -> dict      (Blob에서 읽어온 히스테리시스 상태)
    saver:  (dict) -> None  (변경된 상태를 받아 메모리에 보관, runner가 이후 Blob에 flush)
    """
    global _state_loader, _state_saver
    _state_loader = loader
    _state_saver = saver


def _load_state():
    if _state_loader is not None:
        return _state_loader()
    path = os.path.join(os.path.dirname(__file__), config.STATE_JSON)
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"committed": None, "since": None, "candidate": None, "count": 0}


def _save_state(state):
    if _state_saver is not None:
        _state_saver(state)
        return
    path = os.path.join(os.path.dirname(__file__), config.STATE_JSON)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _apply_hysteresis(raw, state, today):
    """N일 확인 상태머신 → 공식 committed 레짐 결정."""
    H = config.HYSTERESIS
    committed = state.get("committed")
    if committed is None:                       # 최초 실행
        committed = raw
        state.update(committed=committed, since=today, candidate=None, count=0)
        return committed, {"raw": raw, "committed": committed, "pending": False,
                           "candidate": None, "count": 0, "confirm_days": H["confirm_days"],
                           "since": today}
    if raw == committed:                        # 안정
        state.update(candidate=None, count=0)
        pending = False
    else:
        if raw == state.get("candidate"):
            state["count"] = state.get("count", 0) + 1
        else:
            state["candidate"] = raw
            state["count"] = 1
        if state["count"] >= H["confirm_days"]:  # 확인 완료 → 전환
            committed = raw
            state.update(committed=committed, since=today, candidate=None, count=0)
            pending = False
        else:
            pending = True
    return committed, {"raw": raw, "committed": committed, "pending": pending,
                       "candidate": state.get("candidate"), "count": state.get("count", 0),
                       "confirm_days": H["confirm_days"], "since": state.get("since")}


def build():
    # 1) 가격: 지수 + 복합체 + 거시/금리 시장 프록시
    all_tickers = list(dict.fromkeys(
        list(config.INDICES) + list(config.COMPLEX)
        + config.MACRO_MARKET + config.RATE_MARKET))
    px = datafeed.prices(all_tickers, config.LOOKBACK_DAYS)

    # 2) 거시 (FRED) + 금리 (FRED 2Y/브레이크이븐)
    fred = datafeed.fred_many(list(config.FRED_SERIES) + list(config.RATE_FRED))
    macro = macro_mod.recession_composite(fred, px)
    rate = rates.rate_stress(px, fred)

    # 3) 가격구조
    name_group = {**{t: (n, None) for t, n in config.INDICES.items()},
                  **{t: (n, g) for t, (n, g) in config.COMPLEX.items()}}
    index_px = {t: px[t] for t in config.INDICES if t in px}
    complex_px = {t: px[t] for t in config.COMPLEX if t in px}

    index_rows = technical.analyze_universe(index_px, name_group)
    complex_rows = technical.analyze_universe(complex_px, name_group)
    complex_agg = technical.aggregate(complex_rows)

    # 그룹별 집계
    groups = {}
    for g in config.GROUP_KR:
        gr = [r for r in complex_rows if r["group"] == g]
        if gr:
            groups[g] = {"label": config.GROUP_KR[g], **technical.aggregate(gr)}

    # 4) 분류 + 히스테리시스
    asof_dt = dt.datetime.now().astimezone()
    today = asof_dt.date().isoformat()
    m = classifier._measure(macro, index_rows, complex_agg)
    state = _load_state()
    raw = classifier.raw_classify(macro["composite"], m, state.get("committed"))
    committed, confirm = _apply_hysteresis(raw, state, today)
    _save_state(state)
    verdict = classifier.build_verdict(committed, raw, confirm, macro, m, rate, today)

    # 5) 직렬화
    asof = asof_dt.isoformat(timespec="seconds")
    out = {
        "asof": asof,
        "title": "ARDS-X Regime Classifier",
        "subtitle": "미국 빅테크·AI 인프라 + S&P500·Nasdaq100 — 조정 / 과매도 / 하락 / 침체 판별",
        "verdict": verdict,
        "macro": macro,
        "rate": rate,
        "indices": sorted(index_rows, key=lambda r: r["ticker"]),
        "complex": sorted(complex_rows, key=lambda r: r["decline_score"], reverse=True),
        "complex_aggregate": complex_agg,
        "groups": groups,
        "data_quality": {
            "macro_live": macro["n_live"],
            "macro_proxy": macro["n_proxy"],
            "macro_missing": macro["n_missing"],
            "rate_live": rate["n_live"],
            "rate_proxy": rate["n_proxy"],
            "rate_missing": rate["n_missing"],
            "n_prices": len(px),
            "n_expected": len(all_tickers),
        },
        "disclaimer": ("교육·연구용. 투자 권유 아님. 신호(레짐/Phase)만 참고하고 "
                       "실제 매매는 본인 판단·전문가 상담 필수. 방어 전략은 강세장에서 "
                       "기회비용을, 헤지는 잘못된 신호에서 휩쏘 손실을 낼 수 있다."),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--print", action="store_true", dest="do_print")
    args = ap.parse_args()

    out = build()

    out_path = args.out or os.path.join(os.path.dirname(__file__), config.OUTPUT_JSON)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    v = out["verdict"]
    cf = v["hysteresis"]
    pend = f"  [전환대기 {cf['raw']} {cf['count']}/{cf['confirm_days']}]" if cf.get("pending") else ""
    print(f"[ARDS-X] {out['asof']}")
    print(f"  레짐: {v['state']}  ({v['state_kr']})   신뢰도 {v['confidence']}%{pend}")
    print(f"  하락유형: {v['decline_type']['kr']} ({v['decline_type']['code']})")
    print(f"  거시 Composite: {out['macro']['composite']} / Phase {out['macro']['phase']} "
          f"[live {out['macro']['n_live']} · proxy {out['macro']['n_proxy']} · 결측 {out['macro']['n_missing']}]"
          f"   | Rate Stress: {out['rate']['score']} "
          f"[live {out['rate']['n_live']} · proxy {out['rate']['n_proxy']} · 결측 {out['rate']['n_missing']}]")
    print(f"  가격 스트레스: {v['axes']['price_stress']} | 테이프 DD {v['evidence']['tape_drawdown']}% "
          f"| 200일선 위 {v['evidence']['breadth_above_200dma']}%")
    print(f"  → {v['headline']}")
    print(f"  → {v['handoff']}")
    print(f"  저장: {out_path}")

    if args.do_print:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
