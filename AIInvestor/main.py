"""AI Investor — Telegram bot entry point."""

from __future__ import annotations

import logging

from bot.telegram_handler import BotDependencies, build_application
from config import Config, configure_logging
from services.persona_engine import PersonaEngine, get_persona
from services.stock_service import StockService

logger = logging.getLogger("ai_investor")


def main() -> None:
    config = Config.load()
    configure_logging(config.log_level)

    persona_engine = PersonaEngine(
        api_key=config.deepseek_api_key,
        model=config.deepseek_model,
        base_url=config.deepseek_base_url,
    )
    stock_service = StockService()

    deps = BotDependencies(
        persona_engine=persona_engine,
        stock_service=stock_service,
        default_persona_key=get_persona(config.default_persona).key,
    )

    app = build_application(config.telegram_token, deps)

    logger.info(
        "AI Investor starting. Default persona=%s, model=%s, base_url=%s",
        deps.default_persona_key,
        config.deepseek_model,
        config.deepseek_base_url,
    )
    app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
