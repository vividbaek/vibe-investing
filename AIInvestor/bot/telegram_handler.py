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
from services.user_profile import UserProfile, UserProfileRepo

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
    profile_repo: UserProfileRepo
    market_report_service: MarketReportService
    default_persona_key: str


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


def _profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> UserProfile:
    deps = _deps(context)
    detected = normalize_language(update.effective_user.language_code)
    return deps.profile_repo.get_or_create(
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
    profile = _profile(update, context)
    lang = profile.language
    s = t(lang)

    # [1] Greeting + language hint
    await update.message.reply_text(f"{s.greeting}\n\n{s.language_switch_hint}")

    # [2] Intro (once per user)
    if not profile.intro_seen:
        await update.message.reply_text(s.intro)
        deps.profile_repo.update(profile.user_key, intro_seen=True)

    # [3] Persona keyboard
    deps.profile_repo.update(profile.user_key, onboarding_step=STEP_PERSONA)
    await update.message.reply_text(s.persona_prompt, reply_markup=_persona_keyboard(lang))


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = _profile(update, context)
    s = t(profile.language)
    await update.message.reply_text(
        "/start — onboarding\n"
        "/persona — persona keyboard\n"
        "/personas — list personas\n"
        "/lang — switch language (ko / en / ja / zh)\n"
        "/feedback <message> — send feedback to dev (피드백 alias works too)\n"
        "/policy — data handling & disclaimer\n"
        "/forget — delete all my stored data\n"
        "/whoami — show your Telegram chat_id (operator setup)\n"
        "/help — this message\n\n"
        f"{s.disclaimer}"
    )


async def _cmd_personas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = _profile(update, context)
    lang = profile.language
    lines = []
    for persona in list_personas():
        marker = " ✓" if persona.key == profile.persona_key else ""
        lines.append(f"• {persona.key}: {persona.name(lang)}{marker}")
    await update.message.reply_text("\n".join(lines))


async def _cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = _profile(update, context)
    s = t(profile.language)
    await update.message.reply_text(s.persona_prompt, reply_markup=_persona_keyboard(profile.language))


async def _cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Choose language / 언어 선택 / 言語選択 / 选择语言:",
        reply_markup=_lang_keyboard(),
    )


async def _cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = _profile(update, context)
    s = t(profile.language)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(s.forget_yes, callback_data="forget:confirm"),
        InlineKeyboardButton(s.forget_no,  callback_data="forget:cancel"),
    ]])
    await update.message.reply_text(s.forget_prompt, reply_markup=keyboard)


async def _cmd_policy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = _profile(update, context)
    await update.message.reply_text(t(profile.language).policy)


async def _cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reveal the caller's Telegram chat_id (so the operator can set TELEGRAM_OWNER_CHAT_ID)."""
    user = update.effective_user
    chat = update.effective_chat
    text = (
        f"👤 Your Telegram identity\n\n"
        f"chat_id: <code>{chat.id}</code>\n"
        f"user_id: <code>{user.id}</code>\n"
        f"username: @{user.username or '(none)'}\n"
        f"language: {user.language_code or '(none)'}\n\n"
        f"Operators set TELEGRAM_OWNER_CHAT_ID=<chat_id> on the Function App."
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def _cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward the user's feedback to the operator's Telegram chat."""
    profile = _profile(update, context)
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

    if not owner_id:
        # No DM target configured — say it was received (the log captured it)
        await update.message.reply_text(s.feedback_thanks)
        return

    try:
        await context.bot.send_message(chat_id=int(owner_id), text=forwarded)
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
    profile = deps.profile_repo.get_or_create(
        user_key=user_key,
        default_language=normalize_language(query.from_user.language_code),
        default_persona=deps.default_persona_key,
    )

    if data.startswith("lang:"):
        new_lang = data.split(":", 1)[1]
        if new_lang not in SUPPORTED:
            return
        profile = deps.profile_repo.update(user_key, language=new_lang)
        await query.message.reply_text(t(new_lang).lang_changed)
        return

    if data.startswith("persona:"):
        persona_key = data.split(":", 1)[1]
        persona = get_persona(persona_key)
        previous_step = profile.onboarding_step
        profile = deps.profile_repo.update(user_key, persona_key=persona.key)
        lang = profile.language
        s = t(lang)
        await query.message.reply_text(s.persona_set.format(persona=persona.name(lang)))

        # If still in onboarding, advance to [4] report offer.
        if previous_step in {STEP_GREETING, STEP_PERSONA}:
            deps.profile_repo.update(user_key, onboarding_step=STEP_REPORT_OFFER)
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

        deps.profile_repo.update(user_key, onboarding_step=STEP_INTEREST)
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
        # choice == ticker symbol — run live LLM with full unbounded prompt
        ticker = choice.upper()
        await context.bot.send_chat_action(
            chat_id=query.message.chat_id, action=ChatAction.TYPING,
        )
        persona = get_persona(profile.persona_key)
        try:
            snapshot = deps.stock_service.get_snapshot(ticker)
            reply = await deps.persona_engine.generate(
                persona=persona, snapshot=snapshot, language=lang,
                interests=[_localize_tag(tag, lang) for tag in profile.interest_tags] + profile.watchlist_tickers,
            )
            header = f"[{persona.name(lang)} · {ticker} · 전문 분석]" if lang == "ko" else f"[{persona.name(lang)} · {ticker} · deep]"
            await query.message.reply_text(f"{header}\n\n{_strip_md(reply)}\n\n{s.short_disclaimer}")
        except StockServiceError:
            await query.message.reply_text(s.ticker_not_found.format(q=ticker))
        except Exception:
            logger.exception("Deeper analysis failed ticker=%s", ticker)
            await query.message.reply_text(s.error_llm)
        return

    if data.startswith("forget:"):
        choice = data.split(":", 1)[1]
        lang = profile.language
        s = t(lang)
        if choice == "confirm":
            deps.profile_repo.delete(user_key)
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
            deps.profile_repo.update(user_key, onboarding_step=STEP_READY)
            await query.message.reply_text(msg)
            await query.message.reply_text(s.free_query_invite)
        else:
            tags = list(profile.interest_tags)
            if token in tags:
                tags.remove(token)
            else:
                tags.append(token)
            profile = deps.profile_repo.update(user_key, interest_tags=tags)
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
    profile = _profile(update, context)
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

    profile = deps.profile_repo.update(
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


async def _handle_ticker_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    profile: UserProfile,
    text: str,
) -> None:
    deps = _deps(context)
    lang = profile.language
    s = t(lang)
    persona = get_persona(profile.persona_key)

    # ────────────────────────────────────────────────────────────────
    # Intent classifier — natural-language queries we don't yet support
    # ────────────────────────────────────────────────────────────────
    if _classify_intent(text) == "natural_language":
        await update.message.reply_text(s.intent_unrecognized)
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

    if snapshot is None:
        try:
            snapshot = deps.stock_service.get_snapshot(text)
        except StockServiceError:
            # Localize the not-found error
            await update.message.reply_text(s.ticker_not_found.format(q=text))
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
    """In Azure (STORAGE_BACKEND=blob), fetch the pre-rendered report from Blob/CDN.

    Falls back to None on any error or when not running on Azure — caller
    will then build the report on-demand via DeepSeek.
    """
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    account = os.getenv("STORAGE_ACCOUNT_NAME", "").strip()
    if backend != "blob" or not account:
        return None
    try:
        from datetime import datetime, timezone
        from services.blob_report_writer import fetch_cached_report
        date_str = datetime.now(timezone.utc).date().isoformat()
        return await fetch_cached_report(account, date_str, persona_key, language)
    except Exception:
        logger.exception("blob report fetch failed")
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
