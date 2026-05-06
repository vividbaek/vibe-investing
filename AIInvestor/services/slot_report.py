"""§report-generation-policy §2 — 6 KST time slots × 3 personas × 4 languages = 72 reports/day.

Each slot is a distinct framing of the *same* underlying yfinance market data —
the difference is which question the persona is answering at that hour.

Storage layout (Blob container "reports"):
    <YYYY-MM-DD>/<slot_id>/<persona>.<lang>.json

Slot generation runs from a Timer Trigger (one per slot, see function_app.py).
On weekends the timer skips to save LLM cost (§6).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Iterable

from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from .i18n import PERSONA_LANGUAGE_INSTRUCTION, t
from .market_report import _fetch_market_data, MarketReport
from .persona_engine import Persona, PersonaEngine, list_personas

logger = logging.getLogger(__name__)

CONTAINER = "reports"
SUPPORTED_LANGS = ("ko", "en", "ja", "zh")


# ────────────────────────────────────────────────────────────
# Slot definitions (§2.1)
# ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SlotDef:
    slot_id: str          # path-safe; used as folder name in blob
    kst_time: str         # human label e.g. "06:00"
    name_kr: str
    name_en: str
    framing: str          # English instruction injected into LLM prompt
    headline_emoji: str   # decorative


SLOTS: list[SlotDef] = [
    SlotDef(
        slot_id="06_us_close",
        kst_time="06:00",
        name_kr="🌅 미국 증시 마감 요약",
        name_en="🌅 U.S. close recap",
        headline_emoji="🌅",
        framing=(
            "It is now KST 06:00 — the U.S. session has just closed. "
            "Frame today's commentary as a recap of the U.S. market that ended a few hours ago. "
            "Lead with what mattered most in yesterday's NY session."
        ),
    ),
    SlotDef(
        slot_id="08_kr_pred",
        kst_time="08:00",
        name_kr="🇰🇷 한국 증시 개장 전 예측",
        name_en="🇰🇷 KRX pre-open outlook",
        headline_emoji="🇰🇷",
        framing=(
            "It is now KST 08:00 — the Korean market opens at 09:00. "
            "Frame today's commentary as a pre-open look — what the U.S. close + KRW + futures + "
            "macro events imply for the KOSPI/KOSDAQ open."
        ),
    ),
    SlotDef(
        slot_id="12_asia",
        kst_time="12:00",
        name_kr="🇰🇷🇨🇳🇯🇵 한국 오전 + 아시아 요약",
        name_en="🌏 Asia midday wrap",
        headline_emoji="🌏",
        framing=(
            "It is now KST 12:00 — the Korean market is on lunch break. "
            "Summarize the morning session in Korea + how Nikkei and Hang Seng are trading + "
            "any FX or commodity moves that matter."
        ),
    ),
    SlotDef(
        slot_id="15_30_kr_close",
        kst_time="15:30",
        name_kr="🇰🇷 한국 증시 마감 요약",
        name_en="🇰🇷 KRX close recap",
        headline_emoji="🇰🇷",
        framing=(
            "It is now KST 15:30 — KOSPI/KOSDAQ have just closed. "
            "Frame today's commentary as a Korean session close — top movers, foreigner/institution flow."
        ),
    ),
    SlotDef(
        slot_id="21_us_open",
        kst_time="21:00",
        name_kr="🇺🇸 미국 증시 개장 전 포인트",
        name_en="🇺🇸 U.S. pre-open setup",
        headline_emoji="🇺🇸",
        framing=(
            "It is now KST 21:00 — the U.S. market opens at 22:30. "
            "Frame today's commentary as a pre-open setup — earnings calendar, premarket movers, "
            "macro releases, what to watch in the first hour."
        ),
    ),
    SlotDef(
        slot_id="23_us_after",
        kst_time="23:00",
        name_kr="🇺🇸 미국 증시 개장 후 시황",
        name_en="🇺🇸 U.S. open tone",
        headline_emoji="🇺🇸",
        framing=(
            "It is now KST 23:00 — the U.S. market has been open ~30 minutes. "
            "Frame today's commentary as an early-session tone read — opening direction, hot tickers, "
            "what's driving the tape so far."
        ),
    ),
]

SLOTS_BY_ID = {s.slot_id: s for s in SLOTS}


# §4.2 가변 토큰 정책 — strong slots get richer commentary, weak slots get compact.
# Default 500 if not in table.
PERSONA_SLOT_TOKEN_BUDGET: dict[tuple[str, str], int] = {
    # Buffett — value, strongest at recap slots
    ("buffett", "06_us_close"): 800, ("buffett", "21_us_open"): 800,
    ("buffett", "08_kr_pred"):  500, ("buffett", "12_asia"):    400,
    ("buffett", "15_30_kr_close"): 500, ("buffett", "23_us_after"): 400,
    # Dalio — macro, strongest at predictive/macro slots
    ("dalio", "08_kr_pred"):  800, ("dalio", "12_asia"):    800,
    ("dalio", "21_us_open"):  800, ("dalio", "06_us_close"): 500,
    ("dalio", "15_30_kr_close"): 500, ("dalio", "23_us_after"): 500,
    # Wood — innovation, strongest at active-trading slots
    ("wood", "21_us_open"):  800, ("wood", "23_us_after"): 800,
    ("wood", "06_us_close"): 500, ("wood", "08_kr_pred"):  400,
    ("wood", "12_asia"):     400, ("wood", "15_30_kr_close"): 400,
}


def token_budget(persona_key: str, slot_id: str) -> int:
    return PERSONA_SLOT_TOKEN_BUDGET.get((persona_key, slot_id), 500)


def slot_blob_path(date_kst: str, slot_id: str, persona_key: str, language: str) -> str:
    return f"{date_kst}/{slot_id}/{persona_key}.{language}.json"


def kst_today_str() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()


def is_weekend_kst() -> bool:
    """Saturday/Sunday in KST → both markets idle. Skip slot generation."""
    kst = datetime.now(timezone.utc) + timedelta(hours=9)
    return kst.weekday() >= 5


# ────────────────────────────────────────────────────────────
# Slot rendering
# ────────────────────────────────────────────────────────────

def _slot_render(
    slot: SlotDef,
    base: MarketReport,
    persona: Persona,
    language: str,
    commentary: str,
) -> str:
    """Render the user-facing text for one slot report."""
    s = t(language)
    title = {
        "ko": slot.name_kr,
        "en": slot.name_en,
        "ja": slot.name_en,
        "zh": slot.name_en,
    }.get(language, slot.name_en)
    today_label = {"ko": "오늘", "en": "Today", "ja": "本日", "zh": "今日"}.get(language, "Today")

    lines = [
        f"{title} ({base.date} KST {slot.kst_time})",
        "",
    ]
    # Index summary (compact 1-line each)
    for label, close, chg in zip(
        ("S&P 500", "NASDAQ", "NDX"),
        (base.sp500_close, base.nasdaq_close, base.ndx_close),
        (base.sp500_change_pct, base.nasdaq_change_pct, base.ndx_change_pct),
    ):
        if close is None or chg is None:
            lines.append(f"• {label}: N/A")
        else:
            arrow = "▲" if chg >= 0 else "▼"
            lines.append(f"• {label}: {close:,.2f} {arrow} {chg:+.2f}%")
    lines.append("")
    if commentary:
        lines.append(f"💬 {persona.name(language)}")
        lines.append(commentary)
        lines.append("")
    lines.append(f"⚠ {s.disclaimer}")
    return "\n".join(lines)


class SlotReportService:
    """Build + persist slot reports. Reuses the same base market data for all
    persona/language combos so a single yfinance fetch covers 12 reports."""

    def __init__(self, persona_engine: PersonaEngine) -> None:
        self._engine = persona_engine

    async def _commentary(
        self,
        slot: SlotDef,
        persona: Persona,
        language: str,
        base: MarketReport,
    ) -> str:
        lang_instruction = PERSONA_LANGUAGE_INSTRUCTION.get(language, PERSONA_LANGUAGE_INSTRUCTION["en"])
        gainers = ", ".join(f"{m.ticker} {m.change_pct:+.1f}%" for m in base.top_gainers) or "(none)"
        losers = ", ".join(f"{m.ticker} {m.change_pct:+.1f}%" for m in base.top_losers) or "(none)"

        budget = token_budget(persona.key, slot.slot_id)
        depth = "deep" if budget >= 800 else ("medium" if budget >= 500 else "compact")
        depth_instruction = {
            "deep":    "Provide 5–7 sentences with concrete numbers and a prioritized takeaway.",
            "medium":  "Provide 3–4 sentences with at least one concrete number.",
            "compact": "Provide 2 tight sentences. No filler.",
        }[depth]

        user_prompt = (
            f"{slot.framing}\n\n"
            f"Reference market snapshot ({base.date}):\n"
            f"- S&P 500: {base.sp500_change_pct:+.2f}%, close {base.sp500_close}\n"
            f"- NASDAQ: {base.nasdaq_change_pct:+.2f}%, close {base.nasdaq_close}\n"
            f"- NDX: {base.ndx_change_pct:+.2f}%, close {base.ndx_close}\n"
            f"- Top NDX gainers: {gainers}\n"
            f"- Top NDX losers: {losers}\n\n"
            f"{depth_instruction}\n"
            f"Do not give buy/sell instructions. Do not invent figures. "
            f"Stay in the persona voice."
        )

        try:
            response = await self._engine._client.chat.completions.create(
                model=self._engine._model,
                temperature=0.5,
                max_tokens=budget,
                timeout=25.0,
                messages=[
                    {"role": "system", "content": f"{persona.system_prompt}\n\n{lang_instruction}"},
                    {"role": "user",   "content": user_prompt},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            logger.exception("slot commentary failed slot=%s persona=%s lang=%s",
                             slot.slot_id, persona.key, language)
            return ""

    async def build_and_upload_slot(
        self,
        slot: SlotDef,
        storage_account_name: str,
        credential=None,
    ) -> dict[str, str]:
        """Generate all 12 (persona × lang) reports for one slot. Return path → status."""
        if is_weekend_kst():
            logger.info("Weekend KST — skipping slot %s (saves LLM cost)", slot.slot_id)
            return {}

        # Single yfinance fetch for the whole slot (shared across 12 outputs)
        base = await asyncio.to_thread(_fetch_market_data)
        date_kst = kst_today_str()

        creds = credential or DefaultAzureCredential()
        results: dict[str, str] = {}
        sem = asyncio.Semaphore(4)  # limit DeepSeek concurrency

        async def _one(persona: Persona, lang: str) -> None:
            async with sem:
                try:
                    commentary = await self._commentary(slot, persona, lang, base)
                    rendered = _slot_render(slot, base, persona, lang, commentary)
                    path = slot_blob_path(date_kst, slot.slot_id, persona.key, lang)
                    body = json.dumps({
                        "date": date_kst,
                        "slot_id": slot.slot_id,
                        "kst_time": slot.kst_time,
                        "persona_key": persona.key,
                        "persona_name": persona.name(lang),
                        "language": lang,
                        "rendered_text": rendered,
                        "data": asdict(base),
                    }, ensure_ascii=False).encode("utf-8")
                    async with BlobServiceClient(
                        account_url=f"https://{storage_account_name}.blob.core.windows.net",
                        credential=creds,
                    ) as svc:
                        client = svc.get_blob_client(CONTAINER, path)
                        await client.upload_blob(
                            body, overwrite=True, content_type="application/json",
                        )
                    results[path] = "ok"
                except Exception as exc:
                    logger.exception("slot upload failed path=%s/%s/%s",
                                     slot.slot_id, persona.key, lang)
                    results[f"{slot.slot_id}/{persona.key}.{lang}"] = f"err:{type(exc).__name__}"

        try:
            tasks = []
            for persona in list_personas():
                for lang in SUPPORTED_LANGS:
                    tasks.append(_one(persona, lang))
            await asyncio.gather(*tasks)
        finally:
            if credential is None and hasattr(creds, "close"):
                await creds.close()

        ok = sum(1 for v in results.values() if v == "ok")
        logger.info("slot %s — %d/%d reports uploaded", slot.slot_id, ok, len(results))
        return results


# ────────────────────────────────────────────────────────────
# Read-back helpers (used by the bot when surfacing a slot)
# ────────────────────────────────────────────────────────────

async def fetch_slot_report(
    storage_account_name: str,
    date_kst: str,
    slot_id: str,
    persona_key: str,
    language: str,
    credential=None,
) -> str | None:
    """Read a single slot report's rendered text. Returns None on miss."""
    path = slot_blob_path(date_kst, slot_id, persona_key, language)
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            client = svc.get_blob_client(CONTAINER, path)
            try:
                stream = await client.download_blob()
                body = await stream.readall()
                doc = json.loads(body)
                return doc.get("rendered_text")
            except ResourceNotFoundError:
                return None
            except Exception:
                logger.exception("slot fetch failed path=%s", path)
                return None
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()


def latest_slot_id_for_now() -> str:
    """Pick the most recent slot whose KST trigger time is ≤ now.
    Wraps around midnight: at 02:00 KST, returns '23_us_after' from previous day's set
    (caller must then look at yesterday's date if today's blob is missing).
    """
    kst = datetime.now(timezone.utc) + timedelta(hours=9)
    minutes = kst.hour * 60 + kst.minute
    # KST minutes for each slot's trigger
    triggers = [
        (6 * 60,    "06_us_close"),
        (8 * 60,    "08_kr_pred"),
        (12 * 60,   "12_asia"),
        (15*60+30,  "15_30_kr_close"),
        (21 * 60,   "21_us_open"),
        (23 * 60,   "23_us_after"),
    ]
    pick = "23_us_after"  # default if before 06:00 KST → use last night's slot
    for trigger_min, slot_id in triggers:
        if minutes >= trigger_min:
            pick = slot_id
    return pick


async def fetch_latest_slot_report(
    storage_account_name: str,
    persona_key: str,
    language: str,
    credential=None,
) -> tuple[str, str] | None:
    """Find the most recent slot blob for this persona × language and return
    (slot_id, rendered_text). Walks backwards through today's slots, then
    yesterday's last slot. Returns None if nothing found in the last 24h.
    """
    kst_today = kst_today_str()
    kst_yest = ((datetime.now(timezone.utc) + timedelta(hours=9)).date() - timedelta(days=1)).isoformat()

    today_slot = latest_slot_id_for_now()
    # Walk: today's current slot → today's earlier slots → yesterday's last few slots
    today_order = [s.slot_id for s in SLOTS]
    try:
        idx = today_order.index(today_slot)
    except ValueError:
        idx = len(today_order) - 1
    candidates = []
    for s_id in reversed(today_order[:idx + 1]):
        candidates.append((kst_today, s_id))
    for s_id in reversed(today_order):
        candidates.append((kst_yest, s_id))

    for date_kst, slot_id in candidates:
        text = await fetch_slot_report(
            storage_account_name, date_kst, slot_id, persona_key, language, credential,
        )
        if text:
            return slot_id, text
    return None
