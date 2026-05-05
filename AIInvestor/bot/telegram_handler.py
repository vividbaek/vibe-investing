"""Telegram bot wiring: commands, message routing, per-chat persona state."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from services.persona_engine import (
    DEFAULT_PERSONA_KEY,
    PersonaEngine,
    get_persona,
    list_personas,
)
from services.stock_service import StockService, StockServiceError

logger = logging.getLogger(__name__)

PERSONA_KEY = "persona_key"


@dataclass
class BotDependencies:
    persona_engine: PersonaEngine
    stock_service: StockService
    default_persona_key: str


def build_application(token: str, deps: BotDependencies) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data["deps"] = deps

    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("help", _cmd_help))
    app.add_handler(CommandHandler("persona", _cmd_persona))
    app.add_handler(CommandHandler("personas", _cmd_personas))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))
    app.add_error_handler(_on_error)

    return app


def _deps(context: ContextTypes.DEFAULT_TYPE) -> BotDependencies:
    return context.application.bot_data["deps"]


def _current_persona_key(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.chat_data.get(PERSONA_KEY) or _deps(context).default_persona_key


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    persona = get_persona(_current_persona_key(context))
    await update.message.reply_text(
        f"Welcome to AI Investor.\n\n"
        f"Current persona: {persona.display_name}\n\n"
        f"Send a ticker (e.g. AAPL, TSLA, NVDA) and I'll respond in character.\n"
        f"Type /help for commands."
    )


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/persona <key> — switch persona (e.g. /persona buffett)\n"
        "/personas — list available personas\n"
        "/help — show this help\n\n"
        "Or just send a ticker like AAPL or NVDA.\n\n"
        "Disclaimer: this bot does not provide financial advice."
    )


async def _cmd_personas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = _current_persona_key(context)
    lines = ["Available personas:"]
    for persona in list_personas():
        marker = " (current)" if persona.key == current else ""
        lines.append(f"- {persona.key}: {persona.display_name}{marker}")
    await update.message.reply_text("\n".join(lines))


async def _cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        current = get_persona(_current_persona_key(context))
        await update.message.reply_text(
            f"Current persona: {current.display_name} ({current.key}).\n"
            f"Usage: /persona <key>. See /personas for the list."
        )
        return

    requested = context.args[0].lower()
    persona = get_persona(requested)
    if persona.key != requested:
        await update.message.reply_text(
            f"Unknown persona '{requested}'. Use /personas to see available options."
        )
        return

    context.chat_data[PERSONA_KEY] = persona.key
    await update.message.reply_text(f"Persona switched to {persona.display_name}.")


async def _on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return

    deps = _deps(context)
    persona = get_persona(_current_persona_key(context))

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        snapshot = deps.stock_service.get_snapshot(text)
    except StockServiceError as exc:
        await update.message.reply_text(str(exc))
        return
    except Exception:
        logger.exception("Stock lookup failed for input=%r", text)
        await update.message.reply_text(
            "I couldn't fetch market data right now. Please try again in a moment."
        )
        return

    try:
        reply = deps.persona_engine.generate(persona, snapshot)
    except Exception:
        logger.exception("Persona generation failed for ticker=%s", snapshot.ticker)
        await update.message.reply_text(
            "I couldn't generate a response right now. Please try again shortly."
        )
        return

    header = f"[{persona.display_name} on {snapshot.ticker}]"
    await update.message.reply_text(f"{header}\n\n{reply}")


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error in update %s", update, exc_info=context.error)
