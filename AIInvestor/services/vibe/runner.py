"""§Vibe — ARDS-X · AMQS 오케스트레이터.

Azure Functions timer 가 호출:
  - build_ards(account_name) → ARDS-X regime JSON, Blob 에 영속화
  - build_amqs(account_name) → AMQS-AI-Infra 시그널 JSON, Blob 에 영속화

원본 Python 캐노니컬 코드는 services/vibe/{ards,amqs}/ 에 vendored.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from . import blob_state
from .ards import run as ards_run

logger = logging.getLogger(__name__)

# Blob layout
ARDS_STATE_PATH = "state/ards_regime.json"
ARDS_SIGNALS_PATH = "signals/ards-latest.json"
AMQS_STATE_PATH = "state/amqs.json"
AMQS_SIGNALS_PATH = "signals/amqs-latest.json"
COMBINED_SIGNALS_PATH = "signals/latest.json"   # dashboard.ts 가 읽던 키와 동일

ARDS_LOOKBACK_DAYS = 420


async def build_ards(account_name: str) -> dict[str, Any]:
    """ARDS-X 한 번 실행. 히스테리시스 상태는 Blob 에 자동 영속화."""
    state_holder: dict[str, Any] = {
        "data": await blob_state.load_json(
            account_name, ARDS_STATE_PATH,
            default={"committed": None, "since": None, "candidate": None, "count": 0},
        ),
    }

    def _loader() -> dict[str, Any]:
        return state_holder["data"]

    def _saver(new_state: dict[str, Any]) -> None:
        state_holder["data"] = dict(new_state)

    ards_run.configure_state_io(loader=_loader, saver=_saver)
    try:
        # ARDS-X build() 는 동기 — yfinance/FRED 가 ThreadPoolExecutor 내부에서
        # blocking I/O 를 수행. 이벤트 루프 차단을 막기 위해 to_thread 로 격리.
        payload = await asyncio.to_thread(ards_run.build)
    finally:
        ards_run.configure_state_io(loader=None, saver=None)

    # 상태 + 산출물 Blob 에 flush
    await blob_state.save_json(account_name, ARDS_STATE_PATH, state_holder["data"])
    await blob_state.save_json(account_name, ARDS_SIGNALS_PATH, payload)
    return payload


def _amqs_build_sync(market_caps: dict[str, float] | None = None) -> dict[str, Any]:
    """동기 AMQS 빌드 — to_thread 로 호출."""
    import pandas as pd
    import yfinance as yf

    from .amqs import strategy as amqs

    tickers = list(amqs.AI_INFRA_TICKERS)
    macro_qqq = amqs.MACRO_TICKERS["QQQ"]
    macro_vix = amqs.MACRO_TICKERS["VIX"]
    all_syms = tickers + [macro_qqq, macro_vix]

    raw = yf.download(
        tickers=all_syms, period="2y", interval="1d",
        auto_adjust=True, progress=False, group_by="ticker", threads=True,
    )

    # multi-index unpack
    if isinstance(raw.columns, pd.MultiIndex):
        lvl0 = raw.columns.get_level_values(0)
        closes = pd.concat({t: raw[t]["Close"] for t in all_syms if t in lvl0}, axis=1)
    else:
        closes = raw[["Close"]]
        if len(all_syms) == 1:
            closes.columns = all_syms

    closes = closes.dropna(how="all")
    qqq = closes[macro_qqq] if macro_qqq in closes else None
    vix = closes[macro_vix] if macro_vix in closes else None
    prices_df = closes[[c for c in closes.columns if c in tickers]]

    df, regime = amqs.run_amqs_ai_infra(
        prices=prices_df, qqq=qqq, vix=vix,
        market_caps=market_caps,
    )

    return {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": "AMQS-AI-Infra",
        "regime": {
            "label": regime.label,
            "tradeable": regime.tradeable,
            "vix_level": round(float(regime.vix_level), 2),
            "qqq_drawdown": round(float(regime.qqq_drawdown), 4),
            "reason": regime.reason,
        },
        "metrics": df.to_dict(orient="records"),
    }


async def build_amqs(account_name: str,
                     market_caps: dict[str, float] | None = None) -> dict[str, Any]:
    """AMQS-AI-Infra 한 번 실행. 산출물 Blob 에 영속화."""
    payload = await asyncio.to_thread(_amqs_build_sync, market_caps)
    await blob_state.save_json(account_name, AMQS_SIGNALS_PATH, payload)
    return payload


async def build_combined_signals(account_name: str) -> dict[str, Any]:
    """ARDS-X + AMQS 를 순차 실행하고 combined signals/latest.json 으로 결합 저장.

    실패해도 가능한 쪽은 살림 — partial 결과 가능.
    """
    out: dict[str, Any] = {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ards": None,
        "amqs": None,
        "errors": [],
    }
    try:
        out["ards"] = await build_ards(account_name)
    except Exception as exc:
        logger.exception("vibe.runner: ARDS build failed")
        out["errors"].append({"engine": "ards", "msg": str(exc)[:200]})

    try:
        out["amqs"] = await build_amqs(account_name)
    except Exception as exc:
        logger.exception("vibe.runner: AMQS build failed")
        out["errors"].append({"engine": "amqs", "msg": str(exc)[:200]})

    await blob_state.save_json(account_name, COMBINED_SIGNALS_PATH, out)
    return out
