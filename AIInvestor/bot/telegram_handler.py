"""Telegram bot wiring: 6-step onboarding, i18n, persistent profile."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import os

from services.i18n import SUPPORTED, normalize_language, t
from services.market_report import MarketReportService
from services.persona_engine import PersonaEngine, get_persona, list_personas
from services.stock_service import StockService, StockServiceError
from services.profile_factory import AsyncUserProfileRepo
from services.user_profile import UserProfile

logger = logging.getLogger(__name__)

INTEREST_LABELS: dict[str, dict[str, str]] = {
    "ai_chip":   {"ko": "AI 반도체",      "en": "AI chips",     "ja": "AI半導体",     "zh": "AI 芯片"},
    "bigtech":   {"ko": "빅테크",          "en": "Big Tech",     "ja": "ビッグテック", "zh": "大型科技"},
    "dividend":  {"ko": "배당주",          "en": "Dividends",    "ja": "配当株",       "zh": "股息股"},
    "etf":       {"ko": "ETF",             "en": "ETF",          "ja": "ETF",          "zh": "ETF"},
    "btc":       {"ko": "BTC 관련주",      "en": "BTC-linked",   "ja": "BTC関連株",    "zh": "BTC 概念"},
    "energy":    {"ko": "원자재/에너지",   "en": "Energy",       "ja": "エネルギー",   "zh": "能源"},
    "health":    {"ko": "헬스케어",        "en": "Healthcare",   "ja": "ヘルスケア",   "zh": "医疗"},
}

# Onboarding states
STEP_GREETING = "greeting"
STEP_PERSONA = "persona"
STEP_REPORT_OFFER = "report_offer"
STEP_INTEREST = "interest"
STEP_READY = "ready"

TICKER_RE = re.compile(r"^[A-Z]{1,5}(?:[.\-][A-Z]{1,3})?$")


@dataclass
class BotDependencies:
    persona_engine: PersonaEngine
    stock_service: StockService
    profile_repo: AsyncUserProfileRepo  # Blob native async or SQLite-wrapped
    market_report_service: MarketReportService
    default_persona_key: str
    usage_logger: object = None  # services.usage_logger.UsageLogger or None


def build_application(token: str, deps: BotDependencies) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data["deps"] = deps

    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("help", _cmd_help))
    app.add_handler(CommandHandler("persona", _cmd_persona))
    app.add_handler(CommandHandler("personas", _cmd_personas))
    app.add_handler(CommandHandler("lang", _cmd_lang))
    app.add_handler(CommandHandler("forget", _cmd_forget))
    app.add_handler(CommandHandler("policy", _cmd_policy))
    app.add_handler(CommandHandler("feedback", _cmd_feedback))
    app.add_handler(CommandHandler("whoami", _cmd_whoami))
    app.add_handler(CommandHandler("recommend", _cmd_recommend))
    app.add_handler(CommandHandler("compare", _cmd_compare))
    # Owner-only operator commands (gated by TELEGRAM_OWNER_CHAT_ID)
    app.add_handler(CommandHandler("total_user", _cmd_total_user))
    app.add_handler(CommandHandler("today_user", _cmd_today_user))
    app.add_handler(CommandHandler("new_user", _cmd_new_user))
    app.add_handler(CommandHandler("today_feedback", _cmd_today_feedback))

    app.add_handler(CallbackQueryHandler(_on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))

    app.add_error_handler(_on_error)
    return app


# -----------------------------
# Helpers
# -----------------------------

def _deps(context: ContextTypes.DEFAULT_TYPE) -> BotDependencies:
    return context.application.bot_data["deps"]


def _user_key(update: Update) -> str:
    return f"tg:{update.effective_user.id}"


async def _profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> UserProfile:
    deps = _deps(context)
    detected = normalize_language(update.effective_user.language_code)
    return await deps.profile_repo.get_or_create(
        user_key=_user_key(update),
        default_language=detected,
        default_persona=deps.default_persona_key,
    )


def _persona_keyboard(lang: str) -> InlineKeyboardMarkup:
    s = t(lang)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s.persona_buffett, callback_data="persona:buffett")],
        [InlineKeyboardButton(s.persona_dalio,   callback_data="persona:dalio")],
        [InlineKeyboardButton(s.persona_wood,    callback_data="persona:wood")],
    ])


def _report_keyboard(lang: str) -> InlineKeyboardMarkup:
    s = t(lang)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(s.report_yes,  callback_data="report:show"),
        InlineKeyboardButton(s.report_skip, callback_data="report:skip"),
    ]])


def _interest_keyboard(lang: str, selected: set[str]) -> InlineKeyboardMarkup:
    s = t(lang)
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for label, callback in s.interest_preset_btn:
        marker = "✓ " if callback.split(":", 1)[1] in selected else ""
        pair.append(InlineKeyboardButton(f"{marker}{label}", callback_data=callback))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton(s.interest_done_btn, callback_data="interest:done")])
    return InlineKeyboardMarkup(rows)


def _lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("한국어",  callback_data="lang:ko"),
        InlineKeyboardButton("English", callback_data="lang:en"),
        InlineKeyboardButton("日本語",  callback_data="lang:ja"),
        InlineKeyboardButton("中文",    callback_data="lang:zh"),
    ]])


# §8 Pairings — current persona is paired with a contrasting one.
# Quota cost: 2 (vs 1 for single deep). Premium gate.
_DUAL_COUNTERPARTS = {
    "buffett": "wood",     # value vs growth
    "dalio":   "buffett",  # macro vs value
    "wood":    "dalio",    # innovation vs macro
}

_DUAL_LABELS = {
    "ko": "⚔ 듀얼 페르소나 분석",
    "en": "⚔ Dual-persona analysis",
    "ja": "⚔ デュアルペルソナ分析",
    "zh": "⚔ 双角色分析",
}


def _dual_offer_keyboard(persona_key: str, ticker: str, lang: str) -> InlineKeyboardMarkup:
    """Show after a deep analysis — 'compare with another persona' (premium, 2 quota)."""
    counter = _DUAL_COUNTERPARTS.get(persona_key, "wood")
    if counter == persona_key:
        counter = "buffett" if persona_key != "buffett" else "wood"
    counter_local = get_persona(counter).name(lang)
    label = f"{_DUAL_LABELS.get(lang, _DUAL_LABELS['en'])} (vs {counter_local}, ×2)"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data=f"dual:{persona_key}+{counter}:{ticker}"),
    ]])


def _format_interests(profile: UserProfile, lang: str) -> str:
    if not profile.interest_tags and not profile.watchlist_tickers:
        return ""
    tags = ", ".join(_localize_tag(tag, lang) for tag in profile.interest_tags) or "—"
    if profile.watchlist_tickers:
        return f"\n• {('관심 분야' if lang=='ko' else 'Sectors' if lang=='en' else '分野' if lang=='ja' else '行业')}: {tags}" \
               f"\n• {('관심 종목' if lang=='ko' else 'Tickers' if lang=='en' else '銘柄' if lang=='ja' else '个股')}: {', '.join(profile.watchlist_tickers)}"
    return f" ({tags})"


def _localize_tag(tag: str, lang: str) -> str:
    return INTEREST_LABELS.get(tag, {}).get(lang, tag)


# -----------------------------
# Commands
# -----------------------------

async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = _deps(context)
    profile = await _profile(update, context)
    lang = profile.language
    s = t(lang)

    # [1] Greeting + language hint
    await update.message.reply_text(f"{s.greeting}\n\n{s.language_switch_hint}")

    # [2] Intro (once per user)
    if not profile.intro_seen:
        await update.message.reply_text(s.intro)
        await deps.profile_repo.update(profile.user_key, intro_seen=True)

    # [3] Persona keyboard
    await deps.profile_repo.update(profile.user_key, onboarding_step=STEP_PERSONA)
    await update.message.reply_text(s.persona_prompt, reply_markup=_persona_keyboard(lang))


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = await _profile(update, context)
    s = t(profile.language)
    await update.message.reply_text(
        "/start — onboarding\n"
        "/persona — persona keyboard\n"
        "/personas — list personas\n"
        "/lang — switch language (ko / en / ja / zh)\n"
        "/recommend [sector] — top tickers in a sector (no LLM call)\n"
        "/compare T1 T2 [T3 T4] — side-by-side fundamentals (no LLM call)\n"
        "/feedback <message> — send feedback to dev (피드백 alias works too)\n"
        "/policy — data handling & disclaimer\n"
        "/forget — delete all my stored data\n"
        "/whoami — show your Telegram chat_id (operator setup)\n"
        "/help — this message\n\n"
        f"{s.disclaimer}"
    )


async def _cmd_personas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = await _profile(update, context)
    lang = profile.language
    lines = []
    for persona in list_personas():
        marker = " ✓" if persona.key == profile.persona_key else ""
        lines.append(f"• {persona.key}: {persona.name(lang)}{marker}")
    await update.message.reply_text("\n".join(lines))


async def _cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = await _profile(update, context)
    s = t(profile.language)
    await update.message.reply_text(s.persona_prompt, reply_markup=_persona_keyboard(profile.language))


async def _cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Choose language / 언어 선택 / 言語選択 / 选择语言:",
        reply_markup=_lang_keyboard(),
    )


async def _cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = await _profile(update, context)
    s = t(profile.language)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(s.forget_yes, callback_data="forget:confirm"),
        InlineKeyboardButton(s.forget_no,  callback_data="forget:cancel"),
    ]])
    await update.message.reply_text(s.forget_prompt, reply_markup=keyboard)


async def _cmd_policy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = await _profile(update, context)
    await update.message.reply_text(t(profile.language).policy)


async def _cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reveal the caller's Telegram chat_id (so the operator can set TELEGRAM_OWNER_CHAT_ID)."""
    user = update.effective_user
    chat = update.effective_chat
    # Plain text only — earlier HTML version broke because the literal phrase
    # "TELEGRAM_OWNER_CHAT_ID=<chat_id>" was parsed as an unknown HTML tag.
    text = (
        f"👤 Your Telegram identity\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"chat_id : {chat.id}\n"
        f"user_id : {user.id}\n"
        f"username: @{user.username or '(none)'}\n"
        f"language: {user.language_code or '(none)'}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Operators: copy chat_id above into the App Setting "
        f"TELEGRAM_OWNER_CHAT_ID on func-aiinvestor-prod."
    )
    await update.message.reply_text(text)


# ────────────────────────────────────────────────────────────
# Owner-only operator commands. Gated by TELEGRAM_OWNER_CHAT_ID.
# Silent-deny on non-owner: avoid leaking the existence of the
# command surface (callers see nothing — no error, no echo).
# ────────────────────────────────────────────────────────────

def _is_owner(update: Update) -> bool:
    owner = os.getenv("TELEGRAM_OWNER_CHAT_ID", "").strip()
    if not owner:
        return False
    try:
        return int(owner) == update.effective_user.id
    except (ValueError, AttributeError):
        return False


async def _cmd_total_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Total registered users (count of blobs in users/ container)."""
    if not _is_owner(update):
        return
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        await update.message.reply_text("⚠ STORAGE_ACCOUNT_NAME not set")
        return
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    creds = DefaultAzureCredential()
    count = 0
    try:
        async with BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client("users")
            async for _ in container.list_blobs():
                count += 1
    except Exception as exc:
        logger.exception("total_user count failed")
        await update.message.reply_text(f"⚠ 조회 실패: {type(exc).__name__}")
        return
    finally:
        await creds.close()
    await update.message.reply_text(f"👥 누적 가입자: {count:,}명")


async def _cmd_today_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Distinct anon_user_ids active today (KST) — read from logs/."""
    if not _is_owner(update):
        return
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        await update.message.reply_text("⚠ STORAGE_ACCOUNT_NAME not set")
        return
    from datetime import datetime, timezone, timedelta
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    import json as _json
    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
    seen: set[str] = set()
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client("logs")
            # Read last 36h of logs (KST day spans 2 UTC days)
            now = datetime.now(timezone.utc)
            earliest = now - timedelta(hours=36)
            async for blob in container.list_blobs():
                try:
                    parts = blob.name.split("/")
                    bdt = datetime(int(parts[0]), int(parts[1]), int(parts[2]),
                                   int(parts[3].split(".")[0]), tzinfo=timezone.utc)
                    if bdt < earliest:
                        continue
                except (ValueError, IndexError):
                    continue
                try:
                    bclient = container.get_blob_client(blob.name)
                    stream = await bclient.download_blob()
                    body = await stream.readall()
                    for line in body.decode("utf-8").splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            evt = _json.loads(line)
                            ts = evt.get("ts", "")
                            kst_d = ((datetime.fromisoformat(ts.replace("Z","+00:00"))
                                      + timedelta(hours=9)).date().isoformat())
                            if kst_d == today_kst:
                                a = evt.get("anon")
                                if a:
                                    seen.add(a)
                        except (ValueError, KeyError):
                            continue
                except Exception:
                    continue
    finally:
        await creds.close()
    await update.message.reply_text(f"🔥 오늘 활성 사용자: {len(seen):,}명 (KST {today_kst})")


async def _cmd_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Users whose profile.created_at falls on today's KST date."""
    if not _is_owner(update):
        return
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        await update.message.reply_text("⚠ STORAGE_ACCOUNT_NAME not set")
        return
    from datetime import datetime, timezone, timedelta
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    import json as _json
    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
    new_count = 0
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client("users")
            async for blob in container.list_blobs():
                # Cheap filter — if last_modified date is older than today KST,
                # skip download. The created_at in the JSON is the source of truth.
                try:
                    bclient = container.get_blob_client(blob.name)
                    stream = await bclient.download_blob()
                    body = await stream.readall()
                    doc = _json.loads(body)
                    created = doc.get("created_at", "")
                    if not created:
                        continue
                    kst_d = ((datetime.fromisoformat(created.replace("Z","+00:00"))
                              + timedelta(hours=9)).date().isoformat())
                    if kst_d == today_kst:
                        new_count += 1
                except Exception:
                    continue
    finally:
        await creds.close()
    await update.message.reply_text(f"🆕 오늘 신규 가입: {new_count:,}명 (KST {today_kst})")


async def _cmd_today_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List today's feedback messages from feedback/<KST_date>/*.json."""
    if not _is_owner(update):
        return
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        await update.message.reply_text("⚠ STORAGE_ACCOUNT_NAME not set")
        return
    from datetime import datetime, timezone, timedelta
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    import json as _json
    today_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
    items: list[dict] = []
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client("feedback")
            async for blob in container.list_blobs(name_starts_with=f"{today_kst}/"):
                try:
                    bclient = container.get_blob_client(blob.name)
                    stream = await bclient.download_blob()
                    body = await stream.readall()
                    items.append(_json.loads(body))
                except Exception:
                    continue
    except Exception as exc:
        # Container might not exist yet
        logger.exception("today_feedback container read failed")
        await update.message.reply_text(f"💬 오늘 피드백: 0건 (KST {today_kst}) — feedback 컨테이너 없음")
        return
    finally:
        await creds.close()

    if not items:
        await update.message.reply_text(f"💬 오늘 피드백: 0건 (KST {today_kst})")
        return

    items.sort(key=lambda x: x.get("ts", ""), reverse=True)
    lines = [f"💬 오늘 피드백: {len(items)}건 (KST {today_kst})", ""]
    for it in items[:10]:  # cap at 10 to avoid >4096-byte messages
        ts = (it.get("ts") or "").replace("T", " ")[:19]
        usr = it.get("from_username") or f"id={it.get('from_user_id','?')}"
        lang = it.get("language", "?")
        prs = it.get("persona", "?")
        body = (it.get("body") or "").strip()
        if len(body) > 200:
            body = body[:200] + "…"
        lines.append(f"• [{ts}] @{usr} ({lang}/{prs})\n  {body}")
    if len(items) > 10:
        lines.append(f"\n…외 {len(items) - 10}건")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n…(잘림)"
    await update.message.reply_text(text)


# ── /recommend [sector|interest] — list top tickers, no LLM call ──
# Sector aliases (Korean + lowercase English) → sector key in SECTOR_RELATED
_SECTOR_ALIAS = {
    "tech": "Technology", "기술": "Technology", "테크": "Technology", "반도체": "Technology",
    "comm": "Communication Services", "통신": "Communication Services", "미디어": "Communication Services",
    "consumer": "Consumer Cyclical", "소비": "Consumer Cyclical", "유통": "Consumer Cyclical",
    "defensive": "Consumer Defensive", "필수소비": "Consumer Defensive",
    "finance": "Financial Services", "금융": "Financial Services", "은행": "Financial Services",
    "health": "Healthcare", "헬스케어": "Healthcare", "바이오": "Healthcare",
    "energy": "Energy", "에너지": "Energy", "오일": "Energy",
    "industrial": "Industrials", "산업재": "Industrials",
    "utility": "Utilities", "유틸리티": "Utilities",
    "realestate": "Real Estate", "부동산": "Real Estate",
    "material": "Basic Materials", "소재": "Basic Materials",
    "crypto": "Crypto", "암호화폐": "Crypto", "코인": "Crypto",
}

# Crypto isn't in SECTOR_RELATED; we synthesize a small list.
_CRYPTO_PEERS = ["BTC-USD", "ETH-USD", "MSTR", "COIN", "MARA", "RIOT"]
_CRYPTO_ETFS = ["IBIT", "FBTC"]


async def _cmd_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List top tickers — by sector arg, or by user's revealed interests.
    No LLM call: pure data lookup. Validates the cache-first hypothesis.
    """
    import time as _time
    rec_started = _time.monotonic()
    profile = await _profile(update, context)
    lang = profile.language
    s = t(lang)
    arg = " ".join(context.args or []).strip().lower()
    deps = _deps(context)

    from services.sector_tracker import SECTOR_RELATED

    sector_key: str | None = None
    if arg:
        sector_key = _SECTOR_ALIAS.get(arg)
        if not sector_key:
            for alias, sec in _SECTOR_ALIAS.items():
                if alias in arg:
                    sector_key = sec
                    break

    if not sector_key:
        # Use user's most-asked sector from profile.sector_count
        if profile.sector_count:
            sector_key = max(profile.sector_count.items(), key=lambda kv: kv[1])[0]

    header = {
        "ko": "📋 추천 종목",
        "en": "📋 Recommended tickers",
        "ja": "📋 推奨銘柄",
        "zh": "📋 推荐股票",
    }.get(lang, "📋 Recommended tickers")
    sector_label = {
        "ko": "섹터", "en": "Sector", "ja": "セクター", "zh": "行业",
    }.get(lang, "Sector")
    no_section = {
        "ko": "관심 섹터가 없네요. 예) /recommend 기술 또는 /recommend 헬스케어",
        "en": "No sector context yet. Try /recommend tech or /recommend health.",
        "ja": "セクター指定なし。/recommend tech などをお試しください。",
        "zh": "未指定行业。可输入 /recommend tech 等。",
    }.get(lang, "No sector context.")

    if sector_key == "Crypto":
        peers = _CRYPTO_PEERS
        etfs = _CRYPTO_ETFS
    elif sector_key and sector_key in SECTOR_RELATED:
        peers = SECTOR_RELATED[sector_key]["peers"][:8]
        etfs = SECTOR_RELATED[sector_key]["etfs"]
    else:
        await update.message.reply_text(no_section)
        await _log_usage(deps, profile, "", "recommend_no_sector",
                         int((_time.monotonic() - rec_started) * 1000))
        return

    lines = [f"{header}", f"{sector_label}: {sector_key}", ""]

    # Render each peer with whatever cached price we can get cheaply (no yfinance hit if miss)
    peers_label = {"ko": "📌 핵심 종목", "en": "📌 Peers", "ja": "📌 主要銘柄", "zh": "📌 核心股票"}.get(lang, "📌 Peers")
    etfs_label = {"ko": "🧺 ETF", "en": "🧺 ETFs", "ja": "🧺 ETF", "zh": "🧺 ETF"}.get(lang, "🧺 ETFs")
    lines.append(peers_label)
    for tk in peers:
        try:
            snap = deps.stock_service.get_snapshot(tk)
            price = f"{snap.price:,.2f}" if snap.price else "—"
            m1 = f"{snap.price_change_1m_pct:+.1f}%" if snap.price_change_1m_pct is not None else "—"
            lines.append(f"• {tk}: {price}  1M {m1}")
        except Exception:
            lines.append(f"• {tk}: —")
    if etfs:
        lines.append("")
        lines.append(etfs_label)
        for tk in etfs:
            try:
                snap = deps.stock_service.get_snapshot(tk)
                price = f"{snap.price:,.2f}" if snap.price else "—"
                m1 = f"{snap.price_change_1m_pct:+.1f}%" if snap.price_change_1m_pct is not None else "—"
                lines.append(f"• {tk}: {price}  1M {m1}")
            except Exception:
                lines.append(f"• {tk}: —")
    lines.append("")
    lines.append(f"⚠ {s.short_disclaimer}")
    await update.message.reply_text("\n".join(lines))
    await _log_usage(deps, profile, sector_key or "", "recommend",
                     int((_time.monotonic() - rec_started) * 1000))


async def _cmd_compare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/compare AAPL MSFT [GOOGL …] — side-by-side fundamentals snapshot.
    No LLM call. 2–4 tickers supported.
    """
    import time as _time
    cmp_started = _time.monotonic()
    profile = await _profile(update, context)
    lang = profile.language
    s = t(lang)
    deps = _deps(context)

    raw_args = [a.strip().upper() for a in (context.args or []) if a.strip()]
    if len(raw_args) < 2:
        usage = {
            "ko": "사용법: /compare AAPL MSFT GOOGL  (2~4개 티커)",
            "en": "Usage: /compare AAPL MSFT GOOGL  (2–4 tickers)",
            "ja": "使い方: /compare AAPL MSFT GOOGL  (2〜4銘柄)",
            "zh": "用法: /compare AAPL MSFT GOOGL  (2-4 支股票)",
        }.get(lang, "Usage: /compare AAPL MSFT GOOGL")
        await update.message.reply_text(usage)
        await _log_usage(deps, profile, "", "compare_usage",
                         int((_time.monotonic() - cmp_started) * 1000))
        return

    tickers = raw_args[:4]
    snapshots = []
    for tk in tickers:
        try:
            snapshots.append(deps.stock_service.get_snapshot(tk))
        except StockServiceError:
            await update.message.reply_text(s.ticker_not_found.format(q=tk))
            await _log_usage(deps, profile, tk, "compare_not_found",
                             int((_time.monotonic() - cmp_started) * 1000))
            return
        except Exception:
            logger.exception("compare snapshot failed for %s", tk)

    if len(snapshots) < 2:
        await update.message.reply_text(s.error_market_data)
        await _log_usage(deps, profile, "", "compare_error",
                         int((_time.monotonic() - cmp_started) * 1000))
        return

    # Localized header
    header = {
        "ko": "⚖️ 비교", "en": "⚖️ Comparison",
        "ja": "⚖️ 比較",  "zh": "⚖️ 对比",
    }.get(lang, "⚖️ Comparison")
    rows: list[str] = [header + ": " + " vs ".join(s.ticker for s in snapshots), ""]

    def _fmt(v, suffix=""):
        if v is None:
            return "—"
        return f"{v:,.2f}{suffix}" if isinstance(v, float) else f"{v}{suffix}"

    fields = [
        ("Price",       lambda x: _fmt(x.price)),
        ("Market Cap",  lambda x: _fmt_market_cap(x.market_cap)),
        ("P/E",         lambda x: _fmt(x.pe_ratio)),
        ("Fwd P/E",     lambda x: _fmt(x.forward_pe)),
        ("ROE",         lambda x: _fmt_pct(x.return_on_equity)),
        ("D/E",         lambda x: _fmt(x.debt_to_equity)),
        ("Margin",      lambda x: _fmt_pct(x.profit_margin)),
        ("Rev growth",  lambda x: _fmt_pct(x.revenue_growth)),
        ("1M",          lambda x: _fmt_pct_signed(x.price_change_1m_pct)),
        ("6M",          lambda x: _fmt_pct_signed(x.price_change_6m_pct)),
        ("1Y",          lambda x: _fmt_pct_signed(x.price_change_1y_pct)),
    ]

    # Header row + per-field row
    rows.append(" | ".join(["metric"] + [snap.ticker for snap in snapshots]))
    rows.append("-" * 12)
    for label, fn in fields:
        rows.append(" | ".join([label] + [fn(snap) for snap in snapshots]))
    rows.append("")
    rows.append(f"⚠ {s.short_disclaimer}")
    await update.message.reply_text("\n".join(rows))
    await _log_usage(deps, profile, ",".join(snap.ticker for snap in snapshots)[:8],
                     "compare", int((_time.monotonic() - cmp_started) * 1000))


def _fmt_market_cap(v):
    if v is None: return "—"
    if v >= 1e12: return f"{v/1e12:.2f}T"
    if v >= 1e9:  return f"{v/1e9:.2f}B"
    if v >= 1e6:  return f"{v/1e6:.1f}M"
    return f"{v:,.0f}"


def _fmt_pct(v):
    if v is None: return "—"
    # If looks like fraction (0.18) → 18.0%; otherwise treat as already percent
    if abs(v) < 5:
        return f"{v*100:.1f}%"
    return f"{v:.1f}%"


def _fmt_pct_signed(v):
    if v is None: return "—"
    return f"{v:+.1f}%"


async def _cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward the user's feedback to the operator's Telegram chat."""
    profile = await _profile(update, context)
    s = t(profile.language)
    body = " ".join(context.args or []).strip()
    if not body:
        await update.message.reply_text(s.feedback_usage)
        return
    await _forward_feedback(update, context, profile, body, s)


async def _forward_feedback(update, context, profile, body: str, s) -> None:
    """Shared sender used by /feedback and the '피드백' text-prefix shortcut.

    Fallback chain: if TELEGRAM_OWNER_CHAT_ID is unset OR the chat_id is invalid
    (Telegram returns 400 'chat not found'), the feedback is logged at WARNING
    level so it shows up in App Insights — operator can pull it via KQL even
    without DM delivery.
    """
    owner_id = os.getenv("TELEGRAM_OWNER_CHAT_ID", "").strip()
    user = update.effective_user
    user_label = f"@{user.username}" if user.username else f"id={user.id}"
    forwarded = (
        f"📬 [AI Investor Feedback]\n"
        f"From: {user_label} (id={user.id}, anon={profile.anon_user_id})\n"
        f"Lang: {profile.language} · Persona: {profile.persona_key}\n"
        f"───\n"
        f"{body}"
    )

    # Always log the feedback so it survives DM-delivery failures.
    logger.warning("USER_FEEDBACK from=%s anon=%s lang=%s persona=%s body=%r",
                   user_label, profile.anon_user_id, profile.language,
                   profile.persona_key, body)

    # Persist to Blob so the operator's /today_feedback command can recall it
    # later (App Insights KQL is heavyweight; Blob is straightforward).
    try:
        from datetime import datetime, timezone, timedelta
        import uuid as _uuid
        kst_date = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
        from azure.identity.aio import DefaultAzureCredential
        from azure.storage.blob.aio import BlobServiceClient
        account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
        if account:
            payload = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "kst_date": kst_date,
                "from_username": user.username or None,
                "from_user_id": user.id,
                "anon": profile.anon_user_id,
                "language": profile.language,
                "persona": profile.persona_key,
                "body": body,
            }
            blob_path = f"{kst_date}/{_uuid.uuid4().hex}.json"
            creds = DefaultAzureCredential()
            try:
                async with BlobServiceClient(
                    account_url=f"https://{account}.blob.core.windows.net",
                    credential=creds,
                ) as svc:
                    container = svc.get_container_client("feedback")
                    try:
                        await container.create_container()
                    except Exception:
                        pass  # already exists
                    blob = svc.get_blob_client("feedback", blob_path)
                    import json as _json
                    await blob.upload_blob(
                        _json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                        overwrite=True, content_type="application/json",
                    )
            finally:
                await creds.close()
    except Exception:
        logger.exception("feedback Blob persistence failed (non-fatal)")

    if not owner_id:
        # No DM target configured — say it was received (the log captured it)
        await update.message.reply_text(s.feedback_thanks)
        return

    # If the operator is sending feedback to themselves, skip the forward —
    # otherwise they get a confusing duplicate of their own message.
    try:
        owner_id_int = int(owner_id)
    except ValueError:
        owner_id_int = 0
    if owner_id_int == user.id:
        await update.message.reply_text(s.feedback_thanks)
        return

    try:
        await context.bot.send_message(chat_id=owner_id_int, text=forwarded)
        await update.message.reply_text(s.feedback_thanks)
    except Exception as exc:
        logger.exception("Failed to forward feedback to owner_id=%s err=%s",
                         owner_id, exc)
        # Still confirm to user — log captured it
        await update.message.reply_text(s.feedback_thanks)


# -----------------------------
# Callback queries
# -----------------------------

async def _on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    deps = _deps(context)
    user_key = f"tg:{query.from_user.id}"
    profile = await deps.profile_repo.get_or_create(
        user_key=user_key,
        default_language=normalize_language(query.from_user.language_code),
        default_persona=deps.default_persona_key,
    )

    if data.startswith("lang:"):
        new_lang = data.split(":", 1)[1]
        if new_lang not in SUPPORTED:
            return
        profile = await deps.profile_repo.update(user_key, language=new_lang)
        await query.message.reply_text(t(new_lang).lang_changed)
        return

    if data.startswith("persona:"):
        persona_key = data.split(":", 1)[1]
        persona = get_persona(persona_key)
        previous_step = profile.onboarding_step
        profile = await deps.profile_repo.update(user_key, persona_key=persona.key)
        lang = profile.language
        s = t(lang)
        await query.message.reply_text(s.persona_set.format(persona=persona.name(lang)))

        # If still in onboarding, advance to [4] report offer.
        if previous_step in {STEP_GREETING, STEP_PERSONA}:
            await deps.profile_repo.update(user_key, onboarding_step=STEP_REPORT_OFFER)
            await query.message.reply_text(s.report_offer, reply_markup=_report_keyboard(lang))
        else:
            # Mid-session persona swap — preserve interests, just re-confirm.
            await query.message.reply_text(
                s.persona_changed.format(persona=persona.name(lang), interests=_format_interests(profile, lang))
            )
        return

    if data.startswith("report:"):
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "show":
            await context.bot.send_chat_action(
                chat_id=query.message.chat_id, action=ChatAction.TYPING,
            )
            persona = get_persona(profile.persona_key)
            rendered = await _try_blob_cached_report(persona.key, lang)
            if rendered is not None:
                await query.message.reply_text(rendered)
            else:
                interests = [_localize_tag(tag, lang) for tag in profile.interest_tags]
                interests.extend(profile.watchlist_tickers)
                try:
                    report = await deps.market_report_service.build(
                        persona=persona, language=lang, interests=interests,
                    )
                    await query.message.reply_text(report.render(lang, persona.name(lang)))
                except Exception:
                    logger.exception("Daily report generation failed")
                    await query.message.reply_text(s.error_market_data)

        await deps.profile_repo.update(user_key, onboarding_step=STEP_INTEREST)
        await query.message.reply_text(
            s.interest_prompt,
            reply_markup=_interest_keyboard(lang, set(profile.interest_tags)),
        )
        return

    if data.startswith("deeper:"):
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "no":
            await query.message.reply_text(s.short_disclaimer)
            return

        # §17.2 — daily limit check on deep analyses
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        # KST midnight = UTC 15:00. Build the next reset boundary.
        kst_offset = timedelta(hours=9)
        kst_now = now + kst_offset
        next_midnight_kst = (kst_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)) - kst_offset

        reset_at = profile.daily_deep_reset_at
        try:
            reset_dt = datetime.fromisoformat(reset_at.replace("Z", "+00:00")) if reset_at else None
        except Exception:
            reset_dt = None

        if reset_dt is None or now >= reset_dt:
            # Window expired — start fresh
            profile = await deps.profile_repo.update(
                user_key,
                daily_deep_count=0,
                daily_deep_reset_at=next_midnight_kst.isoformat(timespec="seconds"),
            )

        if profile.daily_deep_count >= 5:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(s.subscribe_offer_yes, callback_data="subscribe:start"),
                InlineKeyboardButton(s.subscribe_offer_no,  callback_data="subscribe:later"),
            ]])
            await query.message.reply_text(s.daily_limit_reached, reply_markup=keyboard)
            return

        # consume one quota unit
        profile = await deps.profile_repo.update(
            user_key, daily_deep_count=profile.daily_deep_count + 1,
        )

        # choice == ticker symbol — run live LLM with full unbounded prompt
        ticker = choice.upper()
        import time as _time
        deep_started = _time.monotonic()
        await context.bot.send_chat_action(
            chat_id=query.message.chat_id, action=ChatAction.TYPING,
        )
        persona = get_persona(profile.persona_key)
        try:
            snapshot = deps.stock_service.get_snapshot(ticker)
            interests = [_localize_tag(tag, lang) for tag in profile.interest_tags] + profile.watchlist_tickers
            reply = await deps.persona_engine.generate_deep(
                persona=persona, snapshot=snapshot, language=lang, interests=interests,
            )
            header_label = {
                "ko": "전문 분석",
                "en": "deep dive",
                "ja": "詳細分析",
                "zh": "深度分析",
            }.get(lang, "deep dive")
            header = f"[{persona.name(lang)} · {ticker} · {header_label}]"
            # Telegram message limit is 4096 chars — long deep analyses may need split
            body = f"{header}\n\n{_strip_md(reply)}\n\n{s.short_disclaimer}"
            if len(body) <= 4000:
                await query.message.reply_text(body, reply_markup=_dual_offer_keyboard(persona.key, ticker, lang))
            else:
                # Split at paragraph boundary close to 3500 chars
                cut = body.rfind("\n\n", 0, 3500)
                if cut == -1:
                    cut = 3500
                await query.message.reply_text(body[:cut])
                await query.message.reply_text(body[cut:].lstrip(),
                    reply_markup=_dual_offer_keyboard(persona.key, ticker, lang))
            await _log_usage(deps, profile, ticker, "deep",
                             int((_time.monotonic() - deep_started) * 1000))
        except StockServiceError:
            await query.message.reply_text(s.ticker_not_found.format(q=ticker))
            await _log_usage(deps, profile, ticker, "deep_not_found",
                             int((_time.monotonic() - deep_started) * 1000))
        except Exception:
            logger.exception("Deeper analysis failed ticker=%s", ticker)
            await query.message.reply_text(s.error_llm)
            await _log_usage(deps, profile, ticker, "deep_error",
                             int((_time.monotonic() - deep_started) * 1000))
        return

    if data.startswith("dual:"):
        # §8 Premium dual-persona analysis. Format: dual:<p1>+<p2>:<ticker>
        # Costs 2 quota units (counts as 2 deep queries).
        rest = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        try:
            pair, ticker = rest.split(":", 1)
            p1, p2 = pair.split("+", 1)
        except ValueError:
            return
        if p1 not in {"buffett", "dalio", "wood"} or p2 not in {"buffett", "dalio", "wood"} or p1 == p2:
            return

        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        kst_offset = timedelta(hours=9)
        kst_now = now + kst_offset
        next_midnight_kst = (kst_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)) - kst_offset
        reset_at = profile.daily_deep_reset_at
        try:
            reset_dt = datetime.fromisoformat(reset_at.replace("Z", "+00:00")) if reset_at else None
        except Exception:
            reset_dt = None
        if reset_dt is None or now >= reset_dt:
            profile = await deps.profile_repo.update(
                user_key, daily_deep_count=0,
                daily_deep_reset_at=next_midnight_kst.isoformat(timespec="seconds"),
            )
        # Dual = 2 quota units
        if profile.daily_deep_count + 2 > 5:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(s.subscribe_offer_yes, callback_data="subscribe:start"),
                InlineKeyboardButton(s.subscribe_offer_no,  callback_data="subscribe:later"),
            ]])
            await query.message.reply_text(s.daily_limit_reached, reply_markup=keyboard)
            return
        profile = await deps.profile_repo.update(
            user_key, daily_deep_count=profile.daily_deep_count + 2,
        )

        ticker = ticker.upper()
        import time as _time
        dual_started = _time.monotonic()
        await context.bot.send_chat_action(
            chat_id=query.message.chat_id, action=ChatAction.TYPING,
        )
        persona_a = get_persona(p1)
        persona_b = get_persona(p2)
        try:
            snapshot = deps.stock_service.get_snapshot(ticker)
            interests = [_localize_tag(tag, lang) for tag in profile.interest_tags] + profile.watchlist_tickers
            reply = await deps.persona_engine.generate_dual(
                persona_a=persona_a, persona_b=persona_b,
                snapshot=snapshot, language=lang, interests=interests,
            )
            header_label = {
                "ko": "듀얼 페르소나 분석",
                "en": "dual-persona analysis",
                "ja": "デュアルペルソナ分析",
                "zh": "双角色分析",
            }.get(lang, "dual-persona analysis")
            header = f"[{persona_a.name(lang)} ⚔ {persona_b.name(lang)} · {ticker} · {header_label}]"
            body = f"{header}\n\n{_strip_md(reply)}\n\n{s.short_disclaimer}"
            if len(body) <= 4000:
                await query.message.reply_text(body)
            else:
                cut = body.rfind("\n\n", 0, 3500)
                if cut == -1:
                    cut = 3500
                await query.message.reply_text(body[:cut])
                await query.message.reply_text(body[cut:].lstrip())
            await _log_usage(deps, profile, ticker, "dual",
                             int((_time.monotonic() - dual_started) * 1000))
        except StockServiceError:
            await query.message.reply_text(s.ticker_not_found.format(q=ticker))
            await _log_usage(deps, profile, ticker, "dual_not_found",
                             int((_time.monotonic() - dual_started) * 1000))
        except Exception:
            logger.exception("Dual-persona analysis failed ticker=%s", ticker)
            await query.message.reply_text(s.error_llm)
            await _log_usage(deps, profile, ticker, "dual_error",
                             int((_time.monotonic() - dual_started) * 1000))
        return

    if data.startswith("sector:"):
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "no":
            await query.message.reply_text(s.short_disclaimer)
            return
        # User said yes — fetch a quick comparison from cache for the relevant sector.
        # This is the "간단 비교" stage. We list ETFs + peers with key metrics from the
        # snapshot cache (no LLM call — pure data lookup).
        sector_name = choice
        from services.sector_tracker import SECTOR_RELATED
        related = SECTOR_RELATED.get(sector_name)
        if not related:
            await query.message.reply_text(s.short_disclaimer)
            return

        lines = [
            (f"📊 {sector_name} 비교" if lang == "ko"
             else f"📊 {sector_name} comparison" if lang == "en"
             else f"📊 {sector_name} 比較" if lang == "ja"
             else f"📊 {sector_name} 对比"),
            "",
        ]
        items = (related.get("etfs", []) + related.get("peers", []))[:8]
        for tkr in items:
            try:
                snap = deps.stock_service.get_snapshot(tkr)
                price = f"{snap.price:,.2f}" if snap.price else "—"
                m1 = f"{snap.price_change_1m_pct:+.1f}%" if snap.price_change_1m_pct is not None else "—"
                pe = f"{snap.pe_ratio:.1f}" if snap.pe_ratio else "—"
                lines.append(f"• {tkr}: {price}  1M {m1}  PE {pe}")
            except Exception:
                lines.append(f"• {tkr}: —")
        lines.append("")
        # Offer further depth — explicitly mention 5–10s wait.
        followup = (
            "추가로 세부 분석이 필요하세요?\n⏱ 예 선택 시 5~10초 소요됩니다." if lang == "ko"
            else "Want a deeper drill-down?\n⏱ Yes takes 5–10 seconds." if lang == "en"
            else "さらに詳しい分析が必要ですか?\n⏱ はい選択で5〜10秒かかります。" if lang == "ja"
            else "需要进一步深度分析吗?\n⏱ 选择「是」需要 5–10 秒。"
        )
        lines.append(followup)
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(s.deeper_analysis_yes, callback_data=f"deeper:{items[0] if items else 'NVDA'}"),
            InlineKeyboardButton(s.deeper_analysis_no,  callback_data="deeper:no"),
        ]])
        await query.message.reply_text("\n".join(lines), reply_markup=keyboard)
        return

    if data.startswith("search:"):
        # AI ticker discovery — user confirmed they want us to LLM-search the
        # ambiguous query. Original text lives in user_data["pending_search_query"].
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        pending = (context.user_data.pop("pending_search_query", "") or "").strip()
        if choice == "no" or not pending:
            await query.message.reply_text(s.search_cancelled)
            return
        await _run_llm_ticker_search(update, context, profile, pending)
        return

    if data.startswith("subscribe:"):
        # §17.2 stub — full email-verify flow lands in next sub-task.
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "later":
            await query.message.reply_text(s.short_disclaimer)
            return
        msg = (
            "구독 예약 기능은 곧 오픈됩니다. 베타 알림을 원하시면 /feedback 으로 이메일을 남겨주세요." if lang == "ko"
            else "Subscription reservation is coming soon. Drop an email via /feedback for beta notifications." if lang == "en"
            else "サブスク予約機能は近日公開。/feedback からメールアドレスを送ってください。" if lang == "ja"
            else "订阅预约即将开放。请通过 /feedback 留下邮箱以接收 beta 通知。"
        )
        await query.message.reply_text(msg)
        return

    if data.startswith("forget:"):
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "confirm":
            await deps.profile_repo.delete(user_key)
            await query.message.reply_text(s.forget_done)
        else:
            await query.message.reply_text(s.forget_cancelled)
        return

    if data.startswith("interest:"):
        token = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if token == "done":
            tags_localized = ", ".join(_localize_tag(t_, lang) for t_ in profile.interest_tags) or "—"
            if profile.watchlist_tickers:
                msg = s.interest_saved_with_tickers.format(
                    tags=tags_localized, tickers=", ".join(profile.watchlist_tickers)
                )
            else:
                msg = s.interest_saved.format(tags=tags_localized)
            await deps.profile_repo.update(user_key, onboarding_step=STEP_READY)
            await query.message.reply_text(msg)
            await query.message.reply_text(s.free_query_invite)
        else:
            tags = list(profile.interest_tags)
            if token in tags:
                tags.remove(token)
            else:
                tags.append(token)
            profile = await deps.profile_repo.update(user_key, interest_tags=tags)
            try:
                await query.message.edit_reply_markup(
                    reply_markup=_interest_keyboard(lang, set(profile.interest_tags))
                )
            except Exception:
                pass
        return


# -----------------------------
# Free text handling
# -----------------------------

async def _on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return

    deps = _deps(context)
    profile = await _profile(update, context)
    lang = profile.language
    s = t(lang)

    # Korean slash-commands like "/피드백" aren't recognized by Telegram (commands
    # must match [a-z0-9_]). Intercept "피드백 ..." or "feedback ..." as a text
    # alias so Korean users get the same UX.
    lowered = text.lower()
    if text.startswith("피드백") or lowered.startswith("feedback"):
        # Strip the prefix word + leading whitespace
        for prefix in ("피드백", "feedback", "FEEDBACK"):
            if text.startswith(prefix):
                body = text[len(prefix):].strip(" :,-—")
                break
        else:
            body = ""
        if not body:
            await update.message.reply_text(s.feedback_usage)
        else:
            await _forward_feedback(update, context, profile, body, s)
        return

    # During interest step, free text is parsed as additional interest input.
    if profile.onboarding_step == STEP_INTEREST:
        await _ingest_interest_text(update, context, profile, text)
        return

    # Default: treat as ticker / company query.
    await _handle_ticker_query(update, context, profile, text)


async def _ingest_interest_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    profile: UserProfile,
    text: str,
) -> None:
    deps = _deps(context)
    lang = profile.language
    s = t(lang)

    tickers = list(profile.watchlist_tickers)
    tags = list(profile.interest_tags)
    for token in re.split(r"[,\s/]+", text):
        token = token.strip()
        if not token:
            continue
        upper = token.upper()
        if TICKER_RE.match(upper):
            if upper not in tickers:
                tickers.append(upper)
        else:
            if token not in tags:
                tags.append(token)

    profile = await deps.profile_repo.update(
        profile.user_key,
        interest_tags=tags,
        watchlist_tickers=tickers,
        onboarding_step=STEP_READY,
    )

    tags_localized = ", ".join(_localize_tag(t_, lang) for t_ in tags) or "—"
    if tickers:
        msg = s.interest_saved_with_tickers.format(tags=tags_localized, tickers=", ".join(tickers))
    else:
        msg = s.interest_saved.format(tags=tags_localized)
    await update.message.reply_text(msg)
    await update.message.reply_text(s.free_query_invite)


_NL_KEYWORDS = (
    "추천", "비교", "비슷한", "포트폴리오", "어떤 주식", "뭐가 좋",
    "recommend", "compare", "similar", "portfolio", "what stock", "which stock",
    "おすすめ", "比較", "ポートフォリオ",
    "推荐", "比较", "投资组合",
)


# Follow-up patterns — short or pronoun-heavy queries that ride on the last ticker.
_FOLLOWUP_DEEP = (
    "자세히", "자세하게", "더 알", "더 자세", "deeper", "deep dive", "전문 분석",
    "もっと詳しく", "詳しく", "更多", "详细",
)
_FOLLOWUP_COMPARE = (
    "비교", "compare", " vs ", "vs.", "비교해", "比較", "比较",
)
_FOLLOWUP_GENERAL = (
    "그건", "그것", "이건", "이거", "그게", "그래서", "그럼",
    "위험", "리스크", "전망", "1년", "5년", "후엔", "미래",
    "what about", "그 종목",
    "リスク", "見通し",
    "风险", "前景",
)


def _followup_intent(text: str) -> str | None:
    """Detect a follow-up phrase that should reuse the user's last ticker.
    Returns 'compare' | 'deep' | 'general' | None.
    """
    t_low = text.lower().strip()
    if not t_low:
        return None
    for kw in _FOLLOWUP_COMPARE:
        if kw in t_low:
            return "compare"
    for kw in _FOLLOWUP_DEEP:
        if kw in t_low:
            return "deep"
    for kw in _FOLLOWUP_GENERAL:
        if kw in t_low:
            return "general"
    # Very short message ending with a question mark — almost always a follow-up.
    if len(text) <= 8 and text.endswith(("?", "?")):
        return "general"
    return None


def _classify_intent(text: str) -> str:
    """Return 'natural_language' for non-ticker asks, 'ticker' otherwise."""
    lowered = text.lower()
    for kw in _NL_KEYWORDS:
        if kw in lowered:
            return "natural_language"
    # Long sentence or sentence-final markers → likely natural language
    if len(text) > 25 or text.endswith(("?", "?", "요", "까")):
        return "natural_language"
    return "ticker"


def _strip_md(text: str) -> str:
    """Strip Markdown emphasis we'd otherwise have to parse-mode-escape.

    Telegram default plain-text mode renders **bold** literally. Removing the
    asterisks is simpler and safer than switching to MarkdownV2 (which would
    require escaping every dot, dash, parenthesis the LLM produces).
    """
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold**
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)  # *italic*
    text = re.sub(r"__(.+?)__", r"\1", text)
    return text


async def _log_usage(deps, profile, ticker: str, tier: str, duration_ms: int) -> None:
    """Best-effort usage telemetry (NDJSON in Blob)."""
    logger_inst = getattr(deps, "usage_logger", None)
    if logger_inst is None:
        return
    try:
        await logger_inst.record(
            anon=profile.anon_user_id, lang=profile.language,
            persona=profile.persona_key, ticker=ticker, tier=tier,
            duration_ms=duration_ms,
        )
    except Exception:
        logger.exception("usage_logger.record failed (non-fatal)")


async def _handle_ticker_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    profile: UserProfile,
    text: str,
) -> None:
    import time
    started = time.monotonic()
    deps = _deps(context)
    lang = profile.language
    s = t(lang)
    persona = get_persona(profile.persona_key)

    # ────────────────────────────────────────────────────────────────
    # Context retention — pronoun-only / vague follow-ups ("리스크는?",
    # "더 자세히", "?") reuse the user's last ticker. We only enter this
    # branch when the text DOES NOT resolve to a known ticker — so e.g.
    # "AMD 어때?" still flows to a fresh AMD lookup.
    # ────────────────────────────────────────────────────────────────
    pre_resolved = deps.stock_service._lookup.resolve(text).upper() if text else ""
    # Resolver falls back to first-token-uppercase even when nothing matches —
    # so "리스크는?" returns "리스크는?". Only treat as a real ticker if the
    # output passes the ticker shape regex (1–5 caps, optional .XX suffix).
    pre_valid = bool(re.match(r"^[A-Z]{1,5}(?:[.\-][A-Z]{1,3})?$", pre_resolved))
    fu = None if pre_valid else (_followup_intent(text) if text else None)
    if fu and profile.recent_tickers:
        last_ticker = profile.recent_tickers[0]

        if fu == "compare" and len(profile.recent_tickers) >= 2:
            # Auto-compare last 2-3 tickers — no LLM call
            context.args = profile.recent_tickers[:3]
            await _cmd_compare(update, context)
            await _log_usage(deps, profile, last_ticker, "followup_compare",
                             int((time.monotonic() - started) * 1000))
            return

        if fu == "deep":
            # Surface the deep-analysis confirm keyboard for the last ticker.
            # Quota gate runs inside the deeper:<ticker> callback handler.
            ack = {
                "ko": f"💡 {last_ticker}에 대한 전문 분석을 보여드릴까요? (일일 5회 한도)",
                "en": f"💡 Show deeper analysis on {last_ticker}? (daily limit 5)",
                "ja": f"💡 {last_ticker} の詳細分析を表示しますか? (1日5回)",
                "zh": f"💡 显示 {last_ticker} 的深度分析? (每日 5 次)",
            }.get(lang, f"💡 Deeper analysis on {last_ticker}?")
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(s.deeper_analysis_yes, callback_data=f"deeper:{last_ticker}"),
                InlineKeyboardButton(s.deeper_analysis_no,  callback_data="deeper:no"),
            ]])
            await update.message.reply_text(ack, reply_markup=keyboard)
            await _log_usage(deps, profile, last_ticker, "followup_deep_offer",
                             int((time.monotonic() - started) * 1000))
            return

        # general → ack + treat the last ticker as the current query
        ack = {
            "ko": f"💡 {last_ticker} 에 대한 후속 질문으로 이해했어요.",
            "en": f"💡 Treating that as a follow-up about {last_ticker}.",
            "ja": f"💡 {last_ticker} の続きの質問として処理します。",
            "zh": f"💡 视为关于 {last_ticker} 的后续提问。",
        }.get(lang, f"💡 Follow-up about {last_ticker}.")
        await update.message.reply_text(ack)
        text = last_ticker  # rewrite — falls through into normal cache path

    # ────────────────────────────────────────────────────────────────
    # Intent classifier — natural-language queries we don't yet support
    # ────────────────────────────────────────────────────────────────
    if _classify_intent(text) == "natural_language":
        # Suggest the explicit commands when we recognize the intent
        lowered = text.lower()
        suggestion = None
        if any(k in lowered for k in ("추천", "recommend", "おすすめ", "推荐")):
            suggestion = {
                "ko": "💡 /recommend 또는 /recommend 기술 처럼 입력해 보세요.",
                "en": "💡 Try /recommend or /recommend tech.",
                "ja": "💡 /recommend や /recommend tech をお試しください。",
                "zh": "💡 试试 /recommend 或 /recommend tech。",
            }.get(lang)
        elif any(k in lowered for k in ("비교", "compare", "比較", "比较")):
            suggestion = {
                "ko": "💡 /compare AAPL MSFT 처럼 2개 이상 티커를 입력하세요.",
                "en": "💡 Try /compare AAPL MSFT (2 or more tickers).",
                "ja": "💡 /compare AAPL MSFT のように2銘柄以上を入力してください。",
                "zh": "💡 试试 /compare AAPL MSFT (2 支以上)。",
            }.get(lang)
        await update.message.reply_text(suggestion or s.intent_unrecognized)
        await _log_usage(deps, profile, "", "intent_unrecognized",
                         int((time.monotonic() - started) * 1000))
        return

    # Resolve to canonical ticker once for cache lookups (e.g. "테슬라" → "TSLA").
    ticker_key = deps.stock_service._lookup.resolve(text).upper() if text else ""

    # ────────────────────────────────────────────────────────────────
    # CACHE TIER 1: pre-warmed commentary blob (fastest — no LLM, no yfinance).
    # Skips if user has personal interests context (those queries miss the
    # generic prewarm cache anyway).
    # ────────────────────────────────────────────────────────────────
    if ticker_key and not profile.interest_tags and not profile.watchlist_tickers:
        cached = await _try_prewarmed_commentary(ticker_key, persona.key, lang)
        if cached is not None:
            logger.info("prewarm.cache_hit ticker=%s persona=%s lang=%s",
                        ticker_key, persona.key, lang)
            await update.message.reply_text(_strip_md(cached))
            await _log_usage(deps, profile, ticker_key, "commentary_hit",
                             int((time.monotonic() - started) * 1000))
            # Snapshot lookup for sector recording is cheap (in-memory cache hit)
            try:
                snap = deps.stock_service.get_snapshot(ticker_key)
                await _record_and_maybe_offer_sector(update, context, profile, ticker_key, snap)
            except Exception:
                logger.exception("sector tracking failed (non-fatal)")
            await _offer_deeper(update, context, ticker_key, persona, lang)
            return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # ────────────────────────────────────────────────────────────────
    # CACHE TIER 2: pre-warmed snapshot blob (skips yfinance, still calls LLM).
    # ────────────────────────────────────────────────────────────────
    snapshot = None
    if ticker_key:
        snapshot = await _try_prewarmed_snapshot(ticker_key)
        if snapshot is not None:
            logger.info("prewarm.snapshot_hit ticker=%s", ticker_key)

    snapshot_was_cached = snapshot is not None
    # Probe the stock_service in-memory cache *before* the call so we can
    # attribute Tier 0 ("function_cache") hits separately from a true live
    # path. The probe is O(1) and never hits yfinance.
    mem_was_cached = (
        False if snapshot_was_cached
        else deps.stock_service.is_cached(text)
    )
    if snapshot is None:
        try:
            snapshot = deps.stock_service.get_snapshot(text)
        except StockServiceError:
            # Instead of giving up, offer to AI-search for the right ticker.
            # Stash the original query in user_data so the callback can retrieve it.
            context.user_data["pending_search_query"] = text
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(s.search_confirm_yes, callback_data="search:yes"),
                InlineKeyboardButton(s.search_confirm_no,  callback_data="search:no"),
            ]])
            await update.message.reply_text(
                s.search_confirm_prompt.format(q=text),
                reply_markup=keyboard,
            )
            await _log_usage(deps, profile, ticker_key or text[:8], "ticker_not_found",
                             int((time.monotonic() - started) * 1000))
            return
        except Exception:
            logger.exception("Stock lookup failed for input=%r", text)
            await update.message.reply_text(s.error_market_data)
            return

    interests = [_localize_tag(tag, lang) for tag in profile.interest_tags]
    interests.extend(profile.watchlist_tickers)

    try:
        reply = await deps.persona_engine.generate(
            persona=persona,
            snapshot=snapshot,
            language=lang,
            interests=interests,
        )
    except Exception:
        logger.exception("Persona generation failed for ticker=%s", snapshot.ticker)
        await update.message.reply_text(s.error_llm)
        return

    header = f"[{persona.name(lang)} · {snapshot.ticker}]"
    await update.message.reply_text(f"{header}\n\n{_strip_md(reply)}")
    if snapshot_was_cached:
        tier = "snapshot_hit"
    elif mem_was_cached:
        tier = "function_cache"  # in-process 5-min snapshot cache, LLM still ran
    else:
        tier = "live"
    await _log_usage(deps, profile, snapshot.ticker, tier,
                     int((time.monotonic() - started) * 1000))
    try:
        await _record_and_maybe_offer_sector(update, context, profile, snapshot.ticker, snapshot)
    except Exception:
        logger.exception("sector tracking failed (non-fatal)")
    await _offer_deeper(update, context, snapshot.ticker, persona, lang)


async def _offer_deeper(update, context, ticker: str, persona, lang: str) -> None:
    """After short response, offer a deeper persona analysis with a disclaimer."""
    s = t(lang)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(s.deeper_analysis_yes, callback_data=f"deeper:{ticker}"),
        InlineKeyboardButton(s.deeper_analysis_no,  callback_data="deeper:no"),
    ]])
    body = f"{s.deeper_analysis_offer.format(persona=persona.name(lang))}\n\n{s.risk_notice}"
    await update.message.reply_text(body, reply_markup=keyboard)


async def _record_and_maybe_offer_sector(
    update, context, profile: UserProfile, ticker: str, snapshot,
) -> None:
    """Record the recent ticker + sector. If user has been hitting the same
    sector ≥ 3 of last 5 queries (and last offer > 60 min ago), surface a
    follow-up button to compare ETFs / peers in that sector.
    """
    from datetime import datetime, timezone
    from services.sector_tracker import update_recent, maybe_offer_followup

    deps = _deps(context)
    sector = getattr(snapshot, "sector", None)
    fields = update_recent(profile, ticker, sector)
    profile = await deps.profile_repo.update(profile.user_key, **fields)

    # Resolver looks up sector for each previously-seen ticker via cached snapshot.
    # We use stock_service which has its own 5-min cache, so this is cheap.
    def resolver(t_key: str) -> str | None:
        try:
            snap = deps.stock_service.get_snapshot(t_key)
            return getattr(snap, "sector", None)
        except Exception:
            return None

    offer = maybe_offer_followup(profile, resolver)
    if offer is None:
        return

    sector_name, etfs, peers = offer
    lang = profile.language
    s = t(lang)
    body = s.sector_followup_offer.format(
        sector=sector_name,
        etfs=", ".join(etfs[:4]),
        peers=", ".join(peers[:5]),
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(s.sector_compare_yes, callback_data=f"sector:{sector_name[:30]}"),
        InlineKeyboardButton(s.sector_compare_no,  callback_data="sector:no"),
    ]])
    await update.message.reply_text(body, reply_markup=keyboard)
    await deps.profile_repo.update(
        profile.user_key, last_followup_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


# ────────────────────────────────────────────────────────────
# AI ticker discovery — when natural-language ticker resolution
# fails locally, fall back to a one-shot LLM lookup that maps the
# query to a yfinance ticker (e.g. 삼성전자 → 005930.KS).
# ────────────────────────────────────────────────────────────

import asyncio as _asyncio_search


async def _progress_dots(message, base_text: str, stop_event) -> None:
    """Edit `message` to "<base>." → ".." → "..." every ~700ms until stop_event set.
    Lets users feel the search is alive when LLM > 2s.
    """
    n = 1
    while not stop_event.is_set():
        try:
            await _asyncio_search.wait_for(stop_event.wait(), timeout=0.7)
            break
        except _asyncio_search.TimeoutError:
            try:
                await message.edit_text(f"{base_text}{'.' * n}")
            except Exception:
                pass
            n = (n % 3) + 1


async def _llm_resolve_ticker(deps, query: str) -> str:
    """Ask DeepSeek to map a natural-language stock query → yfinance ticker.
    Returns "" if the LLM call fails or returns garbage. Caller must verify
    the ticker by attempting a yfinance fetch.
    """
    system = (
        "You are a stock-ticker mapping service. Given a user query in any language "
        "(Korean / English / Japanese / Chinese), return the single best yfinance "
        "ticker symbol. Use exchange suffixes correctly:\n"
        "  .KS for KOSPI Korean stocks (e.g. 삼성전자 → 005930.KS)\n"
        "  .KQ for KOSDAQ\n"
        "  .T for Tokyo (e.g. トヨタ → 7203.T)\n"
        "  .HK for Hong Kong\n"
        "  .SS / .SZ for Shanghai / Shenzhen\n"
        "Crypto uses -USD suffix (BTC-USD, ETH-USD).\n"
        "If ambiguous, pick the most-traded match. "
        "Respond with the TICKER ONLY — no quotes, no explanation, no prefix."
    )
    user = f"User query: {query}\nReturn the yfinance ticker:"
    try:
        response = await deps.persona_engine._client.chat.completions.create(
            model=deps.persona_engine._model,
            temperature=0.0,
            max_tokens=20,
            timeout=15.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
    except Exception:
        logger.exception("LLM ticker resolve call failed query=%r", query)
        return ""

    raw = (response.choices[0].message.content or "").strip()
    # Take first line, strip quotes/markdown, uppercase
    raw = raw.split("\n")[0].strip()
    for ch in ("`", '"', "'", "*", "(", ")"):
        raw = raw.replace(ch, "")
    raw = raw.strip(" .,;:").upper()
    # Validate yfinance-shape ticker
    if re.match(r"^[A-Z0-9]{1,8}(?:[.\-][A-Z]{1,4})?$", raw):
        return raw
    logger.warning("LLM returned non-ticker response query=%r raw=%r", query, raw)
    return ""


async def _run_llm_ticker_search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    profile: UserProfile,
    query_text: str,
) -> None:
    """Full search flow: progressive dots → LLM lookup → yfinance verify →
    persona analysis. Reuses _handle_ticker_query downstream when possible.
    """
    import time
    started = time.monotonic()
    deps = _deps(context)
    lang = profile.language
    s = t(lang)
    persona = get_persona(profile.persona_key)
    callback_query = update.callback_query
    chat_id = callback_query.message.chat_id if callback_query else update.effective_chat.id

    # Animated progress message — runs in parallel with the LLM call
    progress_msg = await context.bot.send_message(chat_id, f"{s.search_in_progress}.")
    stop_event = _asyncio_search.Event()
    progress_task = _asyncio_search.create_task(
        _progress_dots(progress_msg, s.search_in_progress, stop_event)
    )

    try:
        ticker = await _llm_resolve_ticker(deps, query_text)
    except Exception:
        ticker = ""
    finally:
        # Stop animator before any further IO so the message is steady
        stop_event.set()
        try:
            await progress_task
        except Exception:
            pass

    if not ticker:
        try:
            await progress_msg.edit_text(s.search_failed.format(q=query_text))
        except Exception:
            pass
        await _log_usage(deps, profile, query_text[:8], "search_failed",
                         int((time.monotonic() - started) * 1000))
        return

    # Verify the LLM's answer by attempting a yfinance fetch
    try:
        snapshot = await _asyncio_search.to_thread(deps.stock_service.get_snapshot, ticker)
    except StockServiceError:
        try:
            await progress_msg.edit_text(s.search_failed.format(q=query_text))
        except Exception:
            pass
        await _log_usage(deps, profile, ticker, "search_failed",
                         int((time.monotonic() - started) * 1000))
        return
    except Exception:
        logger.exception("yfinance verify failed for LLM-resolved ticker=%s", ticker)
        try:
            await progress_msg.edit_text(s.error_market_data)
        except Exception:
            pass
        return

    # Replace the dots message with a ✓ found notice
    try:
        await progress_msg.edit_text(f"✓ {ticker} — {snapshot.name}")
    except Exception:
        pass

    interests = [_localize_tag(tag, lang) for tag in profile.interest_tags] + profile.watchlist_tickers
    try:
        reply = await deps.persona_engine.generate(
            persona=persona, snapshot=snapshot, language=lang, interests=interests,
        )
    except Exception:
        logger.exception("Persona generation failed after AI search ticker=%s", ticker)
        await context.bot.send_message(chat_id, s.error_llm)
        return

    header = f"[{persona.name(lang)} · {snapshot.ticker}]"
    await context.bot.send_message(chat_id, f"{header}\n\n{_strip_md(reply)}")
    await _log_usage(deps, profile, snapshot.ticker, "ai_search_live",
                     int((time.monotonic() - started) * 1000))
    try:
        await _record_and_maybe_offer_sector(update, context, profile, snapshot.ticker, snapshot)
    except Exception:
        logger.exception("sector tracking after AI search failed (non-fatal)")
    # Fake an Update so _offer_deeper still works — re-use callback_query.message
    if callback_query:
        # Pretend the original message is the user's — _offer_deeper only needs reply_text
        class _Stub:
            def __init__(self, m): self.message = m
        await _offer_deeper(_Stub(callback_query.message), context, snapshot.ticker, persona, lang)


async def _try_prewarmed_commentary(ticker: str, persona_key: str, language: str) -> str | None:
    """Return blob-cached rendered text if available (production), else None."""
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        return None
    try:
        from services.prewarm_service import fetch_cached_commentary
        return await fetch_cached_commentary(account, ticker, persona_key, language)
    except Exception:
        logger.exception("prewarm commentary fetch failed")
        return None


async def _try_prewarmed_snapshot(ticker: str):
    """Return blob-cached StockSnapshot if available, else None."""
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if not account:
        return None
    try:
        from services.prewarm_service import fetch_cached_snapshot
        return await fetch_cached_snapshot(account, ticker)
    except Exception:
        logger.exception("prewarm snapshot fetch failed")
        return None


async def _try_blob_cached_report(persona_key: str, language: str) -> str | None:
    """Fetch the most recent pre-rendered report from Blob.

    Lookup order:
      1. Latest 6-slot report (KST timezone, walks backward through today's slots
         then yesterday's). 1차 cache hit per the §report-generation-policy §2.
      2. Legacy daily_report blob (single per-day, KST 06:30).
      3. None — caller builds on-demand via DeepSeek.
    """
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if backend != "blob" or not account:
        return None
    # 1. Slot-based report (latest)
    try:
        from services.slot_report import fetch_latest_slot_report
        result = await fetch_latest_slot_report(account, persona_key, language)
        if result:
            return result[1]
    except Exception:
        logger.exception("slot report fetch failed (will try legacy)")
    # 2. Legacy daily report
    try:
        from datetime import datetime, timezone
        from services.blob_report_writer import fetch_cached_report
        date_str = datetime.now(timezone.utc).date().isoformat()
        return await fetch_cached_report(account, date_str, persona_key, language)
    except Exception:
        logger.exception("legacy blob report fetch failed")
        return None


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error in update %s", update, exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Something went wrong on our side. Please try again shortly."
            )
    except Exception:
        pass
