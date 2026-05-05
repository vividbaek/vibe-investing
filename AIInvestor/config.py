"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_token: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    default_persona: str
    log_level: str

    @staticmethod
    def load() -> "Config":
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

        if not telegram_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Check your .env file.")
        if not deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set. Check your .env file.")

        return Config(
            telegram_token=telegram_token,
            deepseek_api_key=deepseek_api_key,
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
            default_persona=os.getenv("DEFAULT_PERSONA", "buffett").lower(),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
