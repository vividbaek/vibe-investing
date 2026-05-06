"""Azure Functions entry point — Telegram webhook + daily report timer + keepalive.

Deployed by `.github/workflows/deploy.yml` to a Flex Consumption plan in
Korea Central. Runtime layer only — all business logic stays in `bot/` and
`services/` modules from the local 1차 implementation.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import azure.functions as func
from telegram import Update

# OpenTelemetry — routes all Python logging + auto-instruments outgoing
# HTTP calls (DeepSeek, yfinance, Telegram) into Application Insights.
# Must be configured BEFORE any other module imports `logging.getLogger`
# so handlers attach correctly.
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        configure_azure_monitor(logger_name="ai_investor")
except Exception as exc:  # pragma: no cover
    print(f"OpenTelemetry init skipped: {exc}")

from bot.telegram_handler import BotDependencies, build_application
from config import Config, configure_logging
from services.market_report import MarketReportService
from services.persona_engine import PersonaEngine, get_persona
from services.stock_service import StockService
from services.user_profile import UserProfileRepo

logger = logging.getLogger("ai_investor.function_app")

app = func.FunctionApp()

# ---------------------------------------------------------------------
# Cold-start initialization (cached for the lifetime of the instance)
# ---------------------------------------------------------------------

_config: Config | None = None
_ptb_app = None
_market_report_service: MarketReportService | None = None
_profile_repo: UserProfileRepo | None = None


def _bootstrap() -> None:
    """Build the bot application once per Functions instance."""
    global _config, _ptb_app, _market_report_service, _profile_repo
    if _ptb_app is not None:
        return

    _config = Config.load()
    configure_logging(_config.log_level)

    persona_engine = PersonaEngine(
        api_key=_config.deepseek_api_key,
        model=_config.deepseek_model,
        base_url=_config.deepseek_base_url,
    )
    stock_service = StockService()
    # 2차-B: BlobUserProfileRepo will replace SQLite. Until then SQLite path
    # points at a writable mount (Functions /home is persistent across restarts).
    _profile_repo = UserProfileRepo(db_path=_config.sqlite_path, salt=_config.user_id_salt)
    _market_report_service = MarketReportService(persona_engine=persona_engine)

    deps = BotDependencies(
        persona_engine=persona_engine,
        stock_service=stock_service,
        profile_repo=_profile_repo,
        market_report_service=_market_report_service,
        default_persona_key=get_persona(_config.default_persona).key,
    )
    _ptb_app = build_application(_config.telegram_token, deps)
    logger.info("AI Investor bootstrapped (model=%s)", _config.deepseek_model)


# ---------------------------------------------------------------------
# 1) Telegram webhook (HTTP trigger)
# ---------------------------------------------------------------------

@app.route(route="telegram/webhook", auth_level=func.AuthLevel.ANONYMOUS)
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    _bootstrap()
    assert _ptb_app is not None

    # Verify Telegram's secret token to reject forged webhook hits.
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if expected_secret:
        provided = req.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if provided != expected_secret:
            logger.warning("Webhook secret mismatch — rejecting")
            return func.HttpResponse(status_code=401)

    try:
        body: dict[str, Any] = req.get_json()
    except ValueError:
        return func.HttpResponse(status_code=400)

    update = Update.de_json(body, _ptb_app.bot)
    async with _ptb_app:
        await _ptb_app.process_update(update)

    return func.HttpResponse(status_code=200)


# ---------------------------------------------------------------------
# 2) Daily market report timer — KST 06:30 (US close + 30min)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 30 21 * * *",   # UTC 21:30 == KST 06:30
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def daily_report(timer: func.TimerRequest) -> None:
    _bootstrap()
    assert _market_report_service is not None
    from services.blob_report_writer import BlobReportWriter
    from services.persona_engine import list_personas

    if not _config or not _config.storage_account_name:
        logger.warning("STORAGE_ACCOUNT_NAME not set; skipping report upload")
        return

    writer = BlobReportWriter(
        storage_account_name=_config.storage_account_name,
        cdn_subscription_id=os.getenv("CDN_SUBSCRIPTION_ID"),
        cdn_resource_group=os.getenv("CDN_RESOURCE_GROUP"),
        cdn_profile_name=os.getenv("CDN_PROFILE_NAME"),
        cdn_endpoint_name=os.getenv("CDN_ENDPOINT_NAME"),
    )

    paths: list[str] = []
    try:
        for persona in list_personas():
            for lang in ("ko", "en", "ja", "zh"):
                try:
                    report = await _market_report_service.build(persona=persona, language=lang)
                    rendered = report.render(lang, persona.name(lang))
                    path = await writer.upload_report(report, persona, lang, rendered)
                    paths.append(path)
                except Exception:
                    logger.exception("Failed to build/upload persona=%s lang=%s", persona.key, lang)

        if paths:
            await writer.purge_cdn_paths(paths)
            logger.info("daily_report wrote %d blobs and triggered CDN purge", len(paths))
    finally:
        await writer.aclose()


# ---------------------------------------------------------------------
# 3) Keepalive — every 5 minutes to prevent cold starts (Always Ready=1 fallback)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=False,
)
async def keepalive(timer: func.TimerRequest) -> None:
    _bootstrap()
    logger.debug("keepalive tick")
