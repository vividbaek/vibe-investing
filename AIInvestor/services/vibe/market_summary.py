"""§Vibe — DeepSeek 기반 시장 요약 (2 회/일).

흐름:
  1) 최신 market/latest.json 스냅샷 로드 (지수·섹터·VIX·movers·risk gauge)
  2) DeepSeek 1 회 호출 (한국어 2~3 문장, 사실 기반, 투자조언 금지)
  3) Blob market-summary/latest.json 에 저장 (ts, summary_ko, regime, kind)
  4) vibe_news endpoint 가 같이 읽어 market_summary.summary_ko 로 노출

cron 스케줄:
  - 시장 시작:  UTC 13:30 (≈ NYSE 09:30 EST) 평일
  - 시장 마감:  UTC 21:00 (= NYSE 16:00 EST) 평일
  → NCRONTAB "0 30 13 * * 1-5" + "0 0 21 * * 1-5" (2개 별도 timer)

비용 가드:
  - 입력 토큰 작음 (스냅샷 요약만 전달, 종목 리스트 cap 5)
  - max_tokens=200, temperature=0.3
  - 1 회/실행 (재시도 없음)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

SUMMARY_BLOB_PATH = "market-summary/latest.json"
MARKET_BLOB_PATH = "market/latest.json"

SYSTEM_PROMPT = (
    "당신은 미국 증시 시장 요약 작성자입니다. "
    "한국어 사실 기반으로만 작성하고, 투자 조언·예측·전망·매수/매도 권유를 "
    "일체 생성하지 마세요. 종목 추천 금지. 숫자는 제공된 값에서만 인용하세요."
)


def _build_user_prompt(snap: dict[str, Any], kind: str) -> str:
    """kind: 'open' (시장 시작) | 'close' (시장 마감)."""
    indices = snap.get("indices") or []
    sectors = snap.get("sectors") or []
    movers = snap.get("movers") or {}
    gainers = movers.get("gainers") or []
    losers = movers.get("losers") or []
    vix = snap.get("vix")
    risk_score = snap.get("risk_score")
    risk_label = snap.get("risk_label", "")

    def _fmt_tile(t: dict) -> str:
        return f"{t.get('ticker') or t.get('name')} {t.get('chg_pct', 0):+.2f}%"

    sectors_sorted = sorted(sectors, key=lambda s: s.get("chg_pct", 0), reverse=True)
    top_sectors = ", ".join(_fmt_tile(s) for s in sectors_sorted[:3]) or "—"
    bot_sectors = ", ".join(_fmt_tile(s) for s in sectors_sorted[-3:]) or "—"
    idx_line = ", ".join(_fmt_tile(i) for i in indices) or "—"
    g_line = ", ".join(f"{m.get('ticker')} {m.get('chg_pct', 0):+.2f}%"
                       for m in gainers[:5]) or "—"
    l_line = ", ".join(f"{m.get('ticker')} {m.get('chg_pct', 0):+.2f}%"
                       for m in losers[:5]) or "—"

    kind_kr = "시장 시작 시점" if kind == "open" else "시장 마감 시점"
    return (
        f"다음은 미국 증시 {kind_kr} 스냅샷입니다. 한국어 2~3 문장으로 시장 상황을 요약하세요.\n\n"
        f"- 리스크 게이지: {risk_score}/100 ({risk_label})\n"
        f"- 주요 지수: {idx_line}\n"
        f"- VIX: {vix if vix is not None else '—'}\n"
        f"- 섹터 상위 3: {top_sectors}\n"
        f"- 섹터 하위 3: {bot_sectors}\n"
        f"- 급등 5: {g_line}\n"
        f"- 급락 5: {l_line}\n\n"
        f"규칙:\n"
        f"- 정확히 2~3 문장, 한국어로만\n"
        f"- 위 숫자만 인용, 다른 수치 만들지 말 것\n"
        f"- '내일/다음주' 같은 시간 예측 금지\n"
        f"- '~을 권한다 / 매수 / 매도' 금지\n"
        f"- 사실 기술 위주 (예: '기술주 ETF XLK 가 -6.66% 하락하며 …')\n"
    )


async def _call_deepseek(api_key: str, base_url: str, model: str,
                         user_prompt: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=200,
            timeout=20.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
    finally:
        await client.close()
    return (resp.choices[0].message.content or "").strip()


async def refresh_market_summary(config, kind: str = "auto") -> dict[str, Any]:
    """시장요약 1회 생성 + Blob 저장.

    kind:
      - 'open' / 'close': cron 호출
      - 'auto': admin/refresh 등 수동 호출. 현재 시각으로 open/close 추정.
    """
    from . import blob_state

    if kind == "auto":
        h = datetime.now(timezone.utc).hour
        kind = "open" if 12 <= h < 17 else "close"

    if not (config.deepseek_api_key and config.storage_account_name):
        return {"skipped": "missing-config"}

    snap = await blob_state.load_json(config.storage_account_name,
                                       MARKET_BLOB_PATH, default=None)
    if not snap:
        return {"skipped": "no-market-snapshot", "kind": kind}

    prompt = _build_user_prompt(snap, kind)
    try:
        summary_ko = await _call_deepseek(
            config.deepseek_api_key, config.deepseek_base_url,
            config.deepseek_model, prompt,
        )
    except Exception as exc:
        logger.exception("vibe.market_summary: DeepSeek call failed")
        return {"error": "deepseek-failed", "detail": str(exc)[:200], "kind": kind}

    summary_ko = (summary_ko or "").strip()
    if not summary_ko:
        return {"error": "empty-summary", "kind": kind}

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        "regime": snap.get("risk_label"),
        "risk_score": snap.get("risk_score"),
        "summary_ko": summary_ko,
        "source_ts": snap.get("ts"),
    }
    await blob_state.save_json(config.storage_account_name,
                                SUMMARY_BLOB_PATH, payload)
    return {
        "skipped": False, "kind": kind,
        "length": len(summary_ko),
        "regime": payload["regime"],
    }
