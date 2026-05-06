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
from services.profile_factory import build_repo
from services.stock_service import StockService

logger = logging.getLogger("ai_investor.function_app")

app = func.FunctionApp()

# ---------------------------------------------------------------------
# Cold-start initialization (cached for the lifetime of the instance)
# ---------------------------------------------------------------------

_config: Config | None = None
_ptb_app = None
_market_report_service: MarketReportService | None = None
_profile_repo = None
_persona_engine = None
_stock_service = None
_usage_logger = None


async def _bootstrap() -> None:
    """Build the bot application once per Functions instance.

    Calling _ptb_app.initialize() ONCE here (instead of `async with` per
    request) saves ~750ms on every webhook call — that's the getMe round
    trip the bot performs on entry to its async context manager.
    """
    global _config, _ptb_app, _market_report_service, _profile_repo
    global _persona_engine, _stock_service, _usage_logger
    if _ptb_app is not None:
        return

    _config = Config.load()
    configure_logging(_config.log_level)

    _persona_engine = PersonaEngine(
        api_key=_config.deepseek_api_key,
        model=_config.deepseek_model,
        base_url=_config.deepseek_base_url,
    )
    _stock_service = StockService()
    # profile_factory picks Blob (production) or SQLite-async-wrapped (dev)
    # based on STORAGE_BACKEND env. Both expose the same async surface.
    _profile_repo = build_repo(_config)
    _market_report_service = MarketReportService(persona_engine=_persona_engine)

    # Usage logger — async append-blob NDJSON. Best-effort.
    if _config.storage_account_name:
        from services.usage_logger import UsageLogger
        _usage_logger = UsageLogger(_config.storage_account_name)

    deps = BotDependencies(
        persona_engine=_persona_engine,
        stock_service=_stock_service,
        profile_repo=_profile_repo,
        market_report_service=_market_report_service,
        default_persona_key=get_persona(_config.default_persona).key,
        usage_logger=_usage_logger,
    )
    _ptb_app = build_application(_config.telegram_token, deps)
    await _ptb_app.initialize()  # one getMe call — never repeated per request

    # Publish the slash-command menu so /feedback etc. show in autocomplete.
    try:
        from telegram import BotCommand
        await _ptb_app.bot.set_my_commands([
            BotCommand("start",     "Start onboarding"),
            BotCommand("persona",   "Switch investor persona"),
            BotCommand("personas",  "List personas"),
            BotCommand("lang",      "Switch language (ko/en/ja/zh)"),
            BotCommand("recommend", "Top tickers in a sector"),
            BotCommand("compare",   "Side-by-side ticker fundamentals"),
            BotCommand("feedback",  "Send feedback to the dev"),
            BotCommand("policy",    "Data handling & disclaimer"),
            BotCommand("forget",    "Delete all my data"),
            BotCommand("help",      "Show command list"),
        ])
    except Exception:
        logger.exception("set_my_commands failed (non-fatal)")

    logger.info("AI Investor bootstrapped (model=%s)", _config.deepseek_model)


# ---------------------------------------------------------------------
# 1) Telegram webhook (HTTP trigger)
# ---------------------------------------------------------------------

@app.route(route="telegram/webhook", auth_level=func.AuthLevel.ANONYMOUS)
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    await _bootstrap()
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
    # No `async with` — initialize() ran once at bootstrap; per-request
    # context entry was costing ~750ms of getMe roundtrip.
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
    await _bootstrap()
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
# 3a) Prewarm — snapshots for ~250 priority tickers (every 4 hours)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 0 */4 * * *",   # 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def prewarm_snapshots(timer: func.TimerRequest) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        logger.warning("STORAGE_ACCOUNT_NAME not set; skipping prewarm_snapshots")
        return
    from services.prewarm_service import PrewarmService, load_priority_tickers
    pool, _top50 = load_priority_tickers()
    if not pool:
        logger.warning("priority_tickers.csv empty; skipping")
        return
    svc = PrewarmService(
        storage_account_name=_config.storage_account_name,
        persona_engine=_persona_engine,
        stock_service=_stock_service,
    )
    try:
        await svc.refresh_snapshots(pool)
    finally:
        await svc.aclose()


# ---------------------------------------------------------------------
# 3b) Prewarm — commentaries for TOP_50 (every 4 hours, offset 30 min)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 30 */4 * * *",   # 00:30, 04:30, 08:30, ...
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def prewarm_commentaries(timer: func.TimerRequest) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        logger.warning("STORAGE_ACCOUNT_NAME not set; skipping prewarm_commentaries")
        return
    from services.prewarm_service import PrewarmService, load_priority_tickers, fetch_cached_snapshot
    _pool, top50 = load_priority_tickers()
    if not top50:
        logger.warning("no top50 in priority_tickers.csv")
        return

    # Pull pre-warmed snapshots back from blob (so we don't re-hit yfinance).
    snapshots = {}
    for ticker in top50:
        snap = await fetch_cached_snapshot(_config.storage_account_name, ticker)
        if snap is not None:
            snapshots[ticker] = snap
    if not snapshots:
        logger.warning("no snapshots cached yet; commentaries will not run")
        return

    svc = PrewarmService(
        storage_account_name=_config.storage_account_name,
        persona_engine=_persona_engine,
        stock_service=_stock_service,
    )
    try:
        await svc.refresh_commentaries(snapshots, top50)
    finally:
        await svc.aclose()


# ---------------------------------------------------------------------
# 2b) Slot reports (§report-generation-policy §2) — 6 KST time slots
#     × 3 personas × 4 languages = 72 reports/day, ~$1.13/month LLM
#     Skips on Saturday/Sunday KST (both markets idle).
# ---------------------------------------------------------------------

async def _run_slot(slot_id: str) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.slot_report import SlotReportService, SLOTS_BY_ID
    slot = SLOTS_BY_ID.get(slot_id)
    if slot is None:
        logger.error("unknown slot_id=%s", slot_id)
        return
    svc = SlotReportService(persona_engine=_persona_engine)
    try:
        await svc.build_and_upload_slot(slot, _config.storage_account_name)
    except Exception:
        logger.exception("slot %s build_and_upload_slot failed", slot_id)


# Slot 1 — KST 06:00 (UTC 21:00 prev day) — 미국 마감 요약
@app.timer_trigger(schedule="0 0 21 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_06_us_close(timer: func.TimerRequest) -> None:
    await _run_slot("06_us_close")


# Slot 2 — KST 08:00 (UTC 23:00 prev day) — 한국 개장 전 예측
@app.timer_trigger(schedule="0 0 23 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_08_kr_pred(timer: func.TimerRequest) -> None:
    await _run_slot("08_kr_pred")


# Slot 3 — KST 12:00 (UTC 03:00) — 한국 오전 + 아시아 요약
@app.timer_trigger(schedule="0 0 3 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_12_asia(timer: func.TimerRequest) -> None:
    await _run_slot("12_asia")


# Slot 4 — KST 15:30 (UTC 06:30) — 한국 마감 요약
@app.timer_trigger(schedule="0 30 6 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_15_30_kr_close(timer: func.TimerRequest) -> None:
    await _run_slot("15_30_kr_close")


# Slot 5 — KST 21:00 (UTC 12:00) — 미국 개장 전 포인트
@app.timer_trigger(schedule="0 0 12 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_21_us_open(timer: func.TimerRequest) -> None:
    await _run_slot("21_us_open")


# Slot 6 — KST 23:00 (UTC 14:00) — 미국 개장 후 시황
@app.timer_trigger(schedule="0 0 14 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
async def slot_23_us_after(timer: func.TimerRequest) -> None:
    await _run_slot("23_us_after")


# ---------------------------------------------------------------------
# 4) Keepalive — every 5 minutes to prevent cold starts (Always Ready=1 fallback)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 */5 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=False,
)
async def keepalive(timer: func.TimerRequest) -> None:
    await _bootstrap()
    logger.debug("keepalive tick")
    # Flush any buffered usage events on every 5-min tick (best effort)
    if _usage_logger is not None:
        try:
            await _usage_logger.flush()
        except Exception:
            logger.exception("usage_logger flush failed (non-fatal)")


# ---------------------------------------------------------------------
# 7) Public ticker price feed — /api/data/{ticker}
#     3-tier cache: memory → Blob → yfinance origin
# ---------------------------------------------------------------------

@app.route(route="data/{ticker}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def ticker_data(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    ticker = (req.route_params.get("ticker") or "").strip()
    if not ticker or len(ticker) > 12 or not ticker.replace(".", "").replace("-", "").isalnum():
        return func.HttpResponse(
            json.dumps({"error": "invalid ticker"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS,
        )

    from services.ticker_data_cache import get_or_fetch, get_ttl_seconds
    try:
        data, source = await get_or_fetch(ticker, _config.storage_account_name)
    except Exception:
        logger.exception("ticker_data fetch failed for %s", ticker)
        return func.HttpResponse(
            json.dumps({"error": "fetch failed", "ticker": ticker.upper()}),
            status_code=502, mimetype="application/json", headers=_CORS_HEADERS,
        )

    ttl = get_ttl_seconds(ticker.upper())
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = f"public, max-age={ttl}, stale-while-revalidate=60"
    headers["X-Cache-Source"] = source

    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


# ---------------------------------------------------------------------
# 8) Hot ticker pre-warm — every 30 min (skips weekends + KST closed window)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 */30 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def refresh_hot_ticker_data(timer: func.TimerRequest) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.ticker_data_cache import refresh_hot_tickers
    try:
        results = await refresh_hot_tickers(_config.storage_account_name)
        ok = sum(1 for v in results.values() if v == "ok")
        logger.info("refresh_hot_ticker_data — %d/%d ok", ok, len(results))
    except Exception:
        logger.exception("refresh_hot_ticker_data failed")


# ---------------------------------------------------------------------
# 9) Daily HOT_TICKERS rotation — KST 02:00 (UTC 17:00) every day
#    Combines static Korean favorites with last-7-day traffic frequency
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 0 17 * * *",   # UTC 17:00 = KST 02:00
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def rotate_hot_tickers(timer: func.TimerRequest) -> None:
    """§9 Daily HOT_TICKERS rotation. Pool size auto-scales with weekly
    distinct-user traffic: 22 → 50 → 100 → 200 across 4 tiers."""
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.hot_ticker_resolver import resolve_hot_tickers, resolve_pool_size
    from services.ticker_data_cache import update_hot_tickers
    try:
        pool_size, weekly_users = await resolve_pool_size(_config.storage_account_name)
        new_hot = await resolve_hot_tickers(_config.storage_account_name, top_k=pool_size)
        if new_hot:
            update_hot_tickers(new_hot)
            logger.info(
                "rotate_hot_tickers — weekly_users=%d pool_size=%d top 5: %s",
                weekly_users, pool_size, new_hot[:5],
            )
    except Exception:
        logger.exception("rotate_hot_tickers failed")


# ---------------------------------------------------------------------
# 5) Dashboard aggregator — every 15 minutes builds dashboard/24h.json + 7d.json
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 */15 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def aggregate_dashboard(timer: func.TimerRequest) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.dashboard_aggregator import run_aggregation
    try:
        await run_aggregation(_config.storage_account_name)
    except Exception:
        logger.exception("dashboard aggregation failed")


# ---------------------------------------------------------------------
# 5b) V2 dashboard aggregator — heavier, runs every 30 min
#     Builds dashboard/v2.json (4-way cache + cohorts + significance)
# ---------------------------------------------------------------------

@app.timer_trigger(
    schedule="0 5,35 * * * *",   # 5 min after 24h job to avoid overlap
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
async def aggregate_dashboard_v2(timer: func.TimerRequest) -> None:
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.dashboard_aggregator import run_aggregation_v2
    try:
        await run_aggregation_v2(_config.storage_account_name, days=30)
    except Exception:
        logger.exception("v2 dashboard aggregation failed")


# ---------------------------------------------------------------------
# 6) Public landing + Operator dashboard (key-gated)
# ---------------------------------------------------------------------

def _check_dashboard_key(req: func.HttpRequest) -> bool:
    expected = os.getenv("DASHBOARD_ACCESS_KEY", "").strip()
    if not expected or len(expected) < 16:
        return False
    provided = (req.params.get("key") or "").strip()
    return provided == expected


# HTML dashboard moved to Static Web App — see static_web/.
# This Function App still serves:
#   /api/dashboard_stats?key=...&window=24h|7d  → JSON (consumed by SWA dashboard.html)
#   /api/dashboard_export?key=...&window=24h|7d → streaming CSV download

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


@app.route(route="stats", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def public_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Public anonymized stats for the landing page CountUp widgets.

    No key gate — returns only aggregate counts (cumulative users, today's
    active users, MAU). Cached 10 min via Cache-Control. Heavy lifting
    (per-user aggregation) is done by the dashboard_aggregator Timer; this
    route just reads cumulative numbers cheaply.
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    from datetime import datetime, timezone, timedelta
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient

    cumulative_users = 0
    active_today = 0
    mau = 0

    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{_config.storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            # Cumulative users — count blobs in users/ container
            try:
                users_container = svc.get_container_client("users")
                today_utc = datetime.now(timezone.utc).date()
                async for b in users_container.list_blobs():
                    cumulative_users += 1
                    # Active today proxy: blob modified today (i.e. interacted)
                    if b.last_modified and b.last_modified.date() == today_utc:
                        active_today += 1
            except Exception:
                logger.warning("users count failed", exc_info=True)

            # MAU — read dashboard/7d aggregation if present, sum unique anon
            # (We don't have a 30d aggregator yet — extrapolate from 7d × 4
            # for now, with a clear placeholder if 7d data unavailable)
            try:
                dash_blob = svc.get_blob_client("dashboard", "7d.json")
                stream = await dash_blob.download_blob()
                body = await stream.readall()
                doc = json.loads(body)
                # 7d total events / 사용자당 평균 7건 가정
                d7_total = int(doc.get("total", 0))
                # rough MAU estimate
                mau = max(d7_total // 7, cumulative_users)
            except Exception:
                # Fallback to cumulative users
                mau = cumulative_users
    finally:
        await creds.close()

    payload = {
        "cumulative_users": cumulative_users,
        "active_today": active_today,
        "mau": mau,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=600"  # 10 min browser cache
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="dashboard_stats", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def dashboard_stats(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse(
            json.dumps({"error": "forbidden"}),
            status_code=403, mimetype="application/json", headers=_CORS_HEADERS,
        )
    window = (req.params.get("window") or "24h").strip()
    if window not in ("24h", "7d"):
        return func.HttpResponse(
            json.dumps({"error": "bad window"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS,
        )
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    from services.dashboard_aggregator import fetch_dashboard_json
    stats = await fetch_dashboard_json(_config.storage_account_name, window)
    body = json.dumps(stats or {}, ensure_ascii=False)
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=1800"  # 30 min browser cache
    return func.HttpResponse(body, status_code=200, mimetype="application/json", headers=headers)


@app.route(route="dashboard_stats_persona", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def dashboard_stats_persona(req: func.HttpRequest) -> func.HttpResponse:
    """§7 Persona sub-dashboard — per-persona breakdown of KR favorites.
    Query: ?key=<DASHBOARD_ACCESS_KEY>&window=24h|7d&p=buffett|dalio|wood (p optional)
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse(
            json.dumps({"error": "forbidden"}),
            status_code=403, mimetype="application/json", headers=_CORS_HEADERS,
        )
    window = (req.params.get("window") or "7d").strip()
    if window not in ("24h", "7d"):
        return func.HttpResponse(
            json.dumps({"error": "bad window"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS,
        )
    persona = (req.params.get("p") or "").strip().lower() or None
    if persona and persona not in ("buffett", "dalio", "wood"):
        return func.HttpResponse(
            json.dumps({"error": "bad persona"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS,
        )
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    from services.dashboard_aggregator import fetch_persona_breakdown
    data = await fetch_persona_breakdown(_config.storage_account_name, window, persona)
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=900"  # 15 min
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="dashboard_v2", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def dashboard_v2(req: func.HttpRequest) -> func.HttpResponse:
    """V2 observability dashboard JSON. Read pre-computed dashboard/v2.json.
    Falls back to live aggregation if cache miss (slow but functional).
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse(
            json.dumps({"error": "forbidden"}),
            status_code=403, mimetype="application/json", headers=_CORS_HEADERS,
        )
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )
    from services.dashboard_aggregator import fetch_dashboard_v2, run_aggregation_v2
    data = await fetch_dashboard_v2(_config.storage_account_name)
    if data is None:
        # Lazy first-build — kick off then return a shell so UI doesn't break
        try:
            await run_aggregation_v2(_config.storage_account_name, days=30)
            data = await fetch_dashboard_v2(_config.storage_account_name)
        except Exception:
            logger.exception("v2 lazy aggregation failed")
        if data is None:
            data = {"error": "no data yet — aggregator will build on next tick"}

    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=600"
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="dashboard_dates", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def dashboard_dates(req: func.HttpRequest) -> func.HttpResponse:
    """Paginated list of dates with daily traffic counts. Max 10 dates per page.
    Query: ?key=...&page=1   (1-indexed)
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse(
            json.dumps({"error": "forbidden"}),
            status_code=403, mimetype="application/json", headers=_CORS_HEADERS,
        )
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(
            json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    try:
        page = max(1, int(req.params.get("page", "1")))
    except ValueError:
        page = 1
    PER_PAGE = 10

    from services.dashboard_aggregator import fetch_dashboard_v2
    data = await fetch_dashboard_v2(_config.storage_account_name)
    daily = (data or {}).get("daily_series", [])
    total_pages = max(1, (len(daily) + PER_PAGE - 1) // PER_PAGE)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    payload = {
        "page": page,
        "per_page": PER_PAGE,
        "total_pages": total_pages,
        "total_dates": len(daily),
        "dates": daily[start:end],   # already sorted desc by date
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=600"
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="dashboard_export_daily", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def dashboard_export_daily(req: func.HttpRequest) -> func.HttpResponse:
    """CSV download for one specific KST day. Query: ?key=...&date=YYYY-MM-DD"""
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse("Forbidden", status_code=403)
    date_str = (req.params.get("date") or "").strip()
    # Strict YYYY-MM-DD validation
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return func.HttpResponse("Bad date (expected YYYY-MM-DD)", status_code=400)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse("Not configured", status_code=500)

    from services.dashboard_aggregator import export_daily_csv
    csv_body = await export_daily_csv(_config.storage_account_name, date_str)
    return func.HttpResponse(
        csv_body,
        mimetype="text/csv",
        status_code=200,
        headers={
            "Content-Disposition": f'attachment; filename="ai_investor_{date_str}.csv"',
            "Cache-Control": "private, max-age=300",
        },
    )


@app.route(route="dashboard_export", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def dashboard_export(req: func.HttpRequest) -> func.HttpResponse:
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse("Forbidden", status_code=403)

    window = (req.params.get("window") or "24h").strip()
    if window not in ("24h", "7d"):
        return func.HttpResponse("Bad window", status_code=400)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse("Not configured", status_code=500)

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    from services.dashboard_aggregator import _read_logs_in_window
    hours = 24 if window == "24h" else 168

    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{_config.storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            events = await _read_logs_in_window(svc, hours)
    finally:
        await creds.close()

    lines = ["timestamp,anon_user_id_short,language,persona,ticker,tier,duration_ms,llm_in,llm_out"]
    for e in events:
        lines.append(",".join([
            str(e.get("ts", "")),
            str(e.get("anon", ""))[:8],
            str(e.get("lang", "")),
            str(e.get("persona", "")),
            str(e.get("ticker", "")),
            str(e.get("tier", "")),
            str(e.get("duration_ms", 0)),
            str(e.get("llm_in", 0)),
            str(e.get("llm_out", 0)),
        ]))
    csv_body = "\n".join(lines).encode("utf-8")

    return func.HttpResponse(
        csv_body,
        mimetype="text/csv",
        status_code=200,
        headers={
            "Content-Disposition": f'attachment; filename="ai_investor_{window}.csv"'
        },
    )
