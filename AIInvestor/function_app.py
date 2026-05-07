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
        # Reduced public menu — only 6 essentials (Korean descriptions).
        # The full command list is shown via /help in the user's language.
        await _ptb_app.bot.set_my_commands([
            BotCommand("start",    "다시 시작"),
            BotCommand("persona",  "투자 페르소나"),
            BotCommand("miniapp",  "투자의 전장으로 가자!"),
            BotCommand("lang",     "언어 변경 (ko / en / ja / zh)"),
            BotCommand("feedback", "개발자에게 한마디"),
            BotCommand("help",     "도움말"),
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
        usage_logger=_usage_logger,    # track prewarm LLM calls in dashboard
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
        usage_logger=_usage_logger,    # track prewarm LLM calls in dashboard
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
# §T2E-B — Prediction resolve timers
# ---------------------------------------------------------------------

async def _resolve_one_market(market: str, window_id: str) -> int:
    """Generic per-market resolver. Reads yf_ticker from MARKET_WINDOWS,
    fetches close-vs-open from yfinance, applies UP/DOWN to all predictions
    for the given (market, window_id). Returns number of users awarded."""
    from services.prediction_service import resolve_market_predictions, MARKET_WINDOWS
    cfg = MARKET_WINDOWS.get(market)
    if not cfg:
        return 0
    yf_ticker = cfg.get("yf_ticker")
    try:
        import yfinance as yf
        import asyncio as _asyncio
        df = await _asyncio.to_thread(
            yf.download, yf_ticker, period="2d", interval="1d",
            auto_adjust=False, progress=False,
        )
        if df is None or df.empty or len(df) < 1:
            logger.warning("%s close data unavailable, skipping resolve", market)
            return 0
        last = df.iloc[-1]
        open_p, close_p = float(last["Open"]), float(last["Close"])
        actual = "up" if close_p >= open_p else "down"
        logger.info("%s resolve: open=%.2f close=%.2f → %s",
                    market, open_p, close_p, actual)
        awarded = await resolve_market_predictions(
            _config.storage_account_name, market, actual, window_id,
            repo=_profile_repo, usage_logger=_usage_logger,
        )
        return len(awarded)
    except Exception:
        logger.exception("%s resolve failed", market)
        return 0


@app.timer_trigger(
    schedule="0 0 7 * * 1-5",   # KST 16:00 = UTC 07:00, Mon-Fri
    arg_name="timer", run_on_startup=False, use_monitor=True,
)
async def resolve_kospi_predictions(timer: func.TimerRequest) -> None:
    """KST 16:00 — KOSPI close. Window deadline is 14:00 KST (mid-session)."""
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from datetime import datetime, timezone, timedelta
    window_id = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
    n = await _resolve_one_market("kospi", window_id)
    logger.info("KOSPI resolve: %d awarded", n)


@app.timer_trigger(
    schedule="0 0 21 * * 2-6",  # KST 06:00 next day; Mon-Fri close → Tue-Sat resolve
    arg_name="timer", run_on_startup=False, use_monitor=True,
)
async def resolve_nasdaq_and_tickers(timer: func.TimerRequest) -> None:
    """KST 06:00 — NASDAQ + per-ticker close. Resolves NASDAQ index plus
    every individual ticker registered in MARKET_WINDOWS that shares the
    nasdaq deadline (TSLA, NVDA, ...)."""
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from datetime import datetime, timezone, timedelta
    from services.prediction_service import MARKET_WINDOWS
    # Yesterday's KST date — the day user submitted
    window_id = ((datetime.now(timezone.utc) + timedelta(hours=9)).date() - timedelta(days=1)).isoformat()
    # Resolve all markets whose window deadline is 22:30 KST (NASDAQ + TSLA + NVDA)
    nasdaq_aligned = [m for m, cfg in MARKET_WINDOWS.items()
                      if cfg.get("deadline_kst_hour") == 22 and cfg.get("deadline_kst_min") == 30]
    total = 0
    for m in nasdaq_aligned:
        total += await _resolve_one_market(m, window_id)
    logger.info("NASDAQ+tickers resolve: %d awarded across %d markets",
                total, len(nasdaq_aligned))


@app.timer_trigger(
    schedule="0 0 3 * * *",   # KST 12:00 = UTC 03:00 daily
    arg_name="timer", run_on_startup=False, use_monitor=True,
)
async def detect_invite_zombies(timer: func.TimerRequest) -> None:
    """§T2E-C — Daily KST 12:00, find 7-day idle invitees and penalize their inviter."""
    await _bootstrap()
    from services.invite_service import detect_zombies
    try:
        n = await detect_zombies(_profile_repo, usage_logger=_usage_logger, days_threshold=7)
        logger.info("zombie detection: %d processed", n)
    except Exception:
        logger.exception("zombie detection failed")


@app.timer_trigger(
    schedule="0 1 * * * *",  # Top of hour + 1 min
    arg_name="timer", run_on_startup=False, use_monitor=True,
)
async def resolve_btc_hourly(timer: func.TimerRequest) -> None:
    """Resolve last hour's BTC price predictions. Window ID = the hour just ended."""
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.prediction_service import resolve_btc_hourly_predictions
    from datetime import datetime, timezone, timedelta
    # Window that just resolved = previous hour KST
    kst_prev = (datetime.now(timezone.utc) + timedelta(hours=9)) - timedelta(hours=1)
    window_id = f"{kst_prev.year:04d}-{kst_prev.month:02d}-{kst_prev.day:02d}T{kst_prev.hour:02d}"
    try:
        import yfinance as yf
        import asyncio as _asyncio
        ticker = yf.Ticker("BTC-USD")
        info = await _asyncio.to_thread(lambda: ticker.fast_info)
        actual = float(info.last_price) if info and info.last_price else None
        if not actual:
            logger.warning("BTC price unavailable, skipping resolve")
            return
        logger.info("BTC hourly resolve window=%s actual=$%.2f", window_id, actual)

        awarded = await resolve_btc_hourly_predictions(
            _config.storage_account_name, actual, window_id,
            repo=_profile_repo, usage_logger=_usage_logger,
        )
        if awarded:
            logger.info("BTC resolve: %d users awarded", len(awarded))
    except Exception:
        logger.exception("BTC hourly resolve failed")


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
# §T2E-A — Gamification HTTP endpoints (consumed by Mini App)
# ---------------------------------------------------------------------

async def _verify_telegram_init_data_get_userkey(req: func.HttpRequest) -> str | None:
    """Verify the Telegram WebApp `init_data` HMAC and return our internal user_key.

    Returns None if missing/invalid. Init data is sent in the
    X-Telegram-Init-Data header by Mini App calls.
    """
    init_data = req.headers.get("X-Telegram-Init-Data", "").strip()
    if not init_data:
        return None
    bot_token = (_config.telegram_token if _config else os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
    if not bot_token:
        return None

    import hashlib, hmac
    from urllib.parse import parse_qsl

    parsed = dict(parse_qsl(init_data))
    received_hash = parsed.pop("hash", "")
    if not received_hash:
        return None

    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, computed):
        return None

    try:
        user = json.loads(parsed.get("user", "{}"))
        tg_user_id = user.get("id")
        if not tg_user_id:
            return None
        return f"tg:{tg_user_id}"
    except (json.JSONDecodeError, KeyError):
        return None


@app.route(route="gamification/profile", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Return the user's gamification snapshot (points, tier, attendance, invites)."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(
            json.dumps({"error": "unauthorized — missing or invalid Telegram WebApp init_data"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS,
        )

    from services.tier_calculator import compute_tier_stage, points_to_next_tier
    from services.gamification_config import current_season_id

    try:
        profile = await _profile_repo.get_or_create(
            user_key=user_key,
            default_language="ko",
            default_persona="buffett",
        )
    except AttributeError:
        # Sync repo (SQLite)
        profile = _profile_repo.get_or_create(user_key=user_key, default_language="ko", default_persona="buffett")

    tier, stage, label = compute_tier_stage(profile.points_cumulative, profile.points_this_season)
    payload = {
        "anon_user_id": profile.anon_user_id,
        "display_name": profile.display_name or f"User_{profile.anon_user_id[:4]}",
        "language": profile.language,
        "persona_key": profile.persona_key,
        "points": {
            "balance": profile.points_balance,
            "cumulative": profile.points_cumulative,
            "this_season": profile.points_this_season,
            "season_id": profile.season_id or current_season_id(),
        },
        "tier": {
            "name": tier,
            "stage": stage,
            "label": label,
            "to_next": points_to_next_tier(profile.points_cumulative, profile.points_this_season),
        },
        "attendance": {
            "consecutive_days": profile.consecutive_login_days,
            "last_kst": profile.last_attendance_kst,
        },
        "invite": {
            "code": profile.invite_code,
            "validated": profile.invite_validated_count,
            "landings": profile.invite_landings_count,
            "zombies": profile.invite_zombie_count,
        },
        "opt_in_leaderboard": profile.opt_in_leaderboard,
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=10"
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/invite_pack", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_invite_pack(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-E Mini App invite tab — full referral pack (link + 4 message templates + stats).
    init_data HMAC gated. Lazy-generates the invite_code if missing.
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)

    from services.invite_service import get_or_create_invite_code

    # Generate invite code if missing
    try:
        invite_code = await get_or_create_invite_code(_profile_repo, user_key)
    except Exception:
        logger.exception("invite code generation failed")
        return func.HttpResponse(json.dumps({"error": "code_generation_failed"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS)

    # Re-read profile to get fresh stats
    profile_get = _profile_repo.get(user_key) if hasattr(_profile_repo, "get") else None
    profile = profile_get if not (profile_get and hasattr(profile_get, "__await__")) else await profile_get

    # Bot username (cached at bootstrap)
    bot_username = "AI_vibe_investor_bot"
    try:
        if _ptb_app:
            me = await _ptb_app.bot.get_me()
            bot_username = me.username
    except Exception:
        pass

    invite_link = f"https://t.me/{bot_username}?start=ref_{invite_code}"
    earned_p = profile.invite_landings_count * 30 + profile.invite_validated_count * 470

    # 4 message templates (mirrors §6.9.2 of t2e v2.0 spec)
    templates = {
        "casual": {
            "label_ko": "친근한 톤",
            "label_en": "Casual",
            "text_ko": (
                f"증권당이라는 AI 챗봇 써봤어?\n"
                f"워렌 버핏, 캐시 우드, 레이 달리오 페르소나가 시황 알려줘.\n"
                f"내 추천 링크로 가입하면 200 P 받아.\n{invite_link}"
            ),
            "text_en": (
                f"Tried this AI investor chatbot?\n"
                f"Buffett, Wood, Dalio personas explain market moves.\n"
                f"Sign up via my link for 200 P.\n{invite_link}"
            ),
        },
        "professional": {
            "label_ko": "전문가 톤",
            "label_en": "Professional",
            "text_ko": (
                f"AI 투자 챗봇 증권당을 추천합니다.\n"
                f"NASDAQ·KOSPI·암호화폐를 4개 언어로 분석하는 페르소나 봇입니다.\n"
                f"추천 링크: {invite_link}\n"
                f"가입 시 200 Point 환영 보너스가 즉시 지급됩니다."
            ),
            "text_en": (
                f"I recommend AI investor chatbot 증권당.\n"
                f"NASDAQ·KOSPI·crypto analysis in 4 languages by persona bots.\n"
                f"Referral link: {invite_link}\n"
                f"200 Point welcome bonus on signup."
            ),
        },
        "fomo": {
            "label_ko": "FOMO 자극",
            "label_en": "FOMO",
            "text_ko": (
                f"오늘 코스피·나스닥 시황 예측해서 Point 받았어.\n"
                f"AI 페르소나가 종목 분석해주는데 진짜 신기함.\n"
                f"먼저 들어가면 이달의 랭킹도 노릴 만함:\n{invite_link}"
            ),
            "text_en": (
                f"Predicted KOSPI·NASDAQ today and earned Points.\n"
                f"AI personas explain tickers — surprisingly good.\n"
                f"Get in early for monthly rankings:\n{invite_link}"
            ),
        },
        "minimal": {
            "label_ko": "초간단",
            "label_en": "Minimal",
            "text_ko": f"AI 투자 챗봇 추천 → 200 P 환영 보너스\n{invite_link}",
            "text_en": f"AI investor chatbot referral — 200 P welcome bonus\n{invite_link}",
        },
    }

    payload = {
        "invite_code": invite_code,
        "invite_link": invite_link,
        "bot_username": bot_username,
        "stats": {
            "landings": profile.invite_landings_count,
            "validated": profile.invite_validated_count,
            "zombies": profile.invite_zombie_count,
            "points_earned": earned_p,
        },
        "milestones": {
            # next milestone shows the user what to push toward
            "next_count": _next_invite_milestone(profile.invite_validated_count),
            "next_reward": _next_invite_reward(profile.invite_validated_count),
        },
        "templates": templates,
        "language": profile.language,
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=10"
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


def _next_invite_milestone(current: int) -> int:
    for n in (2, 3, 5, 10, 20, 50):
        if current < n:
            return n
    return 100


def _next_invite_reward(current: int) -> str:
    rewards = {
        2:  "프리미엄 3일 + 200 P",
        3:  "프리미엄 7일 + 500 P",
        5:  "프리미엄 30일 + 1,000 P",
        10: "프리미엄 90일 + 5,000 P",
        20: "프리미엄 영구 + 다이아몬드",
        50: "명예의 전당 + 챔피언 페르소나",
    }
    nxt = _next_invite_milestone(current)
    return rewards.get(nxt, "")


@app.route(route="gamification/brag_cards", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_brag_cards(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-O — Return the user's existing brag cards (most recent first)."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"items": []}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS)
    from services.brag_card_service import list_user_cards
    items = await list_user_cards(_config.storage_account_name, user_key)
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=30"
    return func.HttpResponse(
        json.dumps({"items": items}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/brag_card/generate", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def gamification_brag_card_generate(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-O — Manually generate a brag card (called from Mini App).
    Body: {"kind": "tier_promotion" | "streak_accuracy" | "bet_profit"}
    The auto-trigger paths fire on milestone events; this endpoint lets users
    manually re-create from the current snapshot.
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS)

    try:
        body = req.get_json()
    except ValueError:
        body = {}
    kind = (body.get("kind") or "tier_promotion").strip()

    from services.brag_card_service import (
        build_tier_promotion_card, build_streak_accuracy_card,
        build_bet_profit_card, render_and_upload,
    )
    from services.invite_service import get_or_create_invite_code
    from services.tier_calculator import next_tier_threshold

    profile_call = _profile_repo.get_or_create(user_key=user_key, default_language="ko", default_persona="buffett")
    profile = await profile_call if hasattr(profile_call, "__await__") else profile_call
    invite_code = await get_or_create_invite_code(_profile_repo, user_key)

    bot_username = "AI_vibe_investor_bot"
    try:
        if _ptb_app:
            me = await _ptb_app.bot.get_me()
            bot_username = me.username
    except Exception:
        pass
    invite_link = f"https://t.me/{bot_username}?start=ref_{invite_code}"
    nickname = profile.display_name or f"User_{profile.anon_user_id[:4]}"

    if kind == "tier_promotion":
        card = build_tier_promotion_card(
            nickname=nickname, tier=profile.tier,
            season_points=profile.points_this_season,
            next_threshold=next_tier_threshold(profile.tier),
            rank=None, invite_link=invite_link, user_id=user_key,
        )
    elif kind == "streak_accuracy":
        card = build_streak_accuracy_card(
            nickname=nickname, tier=profile.tier,
            streak_days=profile.consecutive_login_days,
            accuracy_pct=0.0,    # Mini App could pass an explicit value
            percentile=None, invite_link=invite_link, user_id=user_key,
        )
    elif kind == "bet_profit":
        card = build_bet_profit_card(
            nickname=nickname, tier=profile.tier,
            profit_p=int(body.get("profit_p", 0) or 0),
            win_count=int(body.get("win_count", 0) or 0),
            total_bets=int(body.get("total_bets", 0) or 0),
            invite_link=invite_link, user_id=user_key,
        )
    else:
        return func.HttpResponse(json.dumps({"error": "unknown kind"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS)

    try:
        card = await render_and_upload(card, _config.storage_account_name)
    except Exception as exc:
        logger.exception("brag card generation failed")
        return func.HttpResponse(json.dumps({"error": str(exc)[:200]}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS)

    return func.HttpResponse(
        json.dumps({"success": True, **card.__dict__}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS,
    )


@app.route(route="share-card/{*path}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def share_card_proxy(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-O — Public proxy serving brag card PNGs from private Blob.
    Path: /api/share-card/<user_short>/<kind>/<uuid>.png
    No auth (cards are meant to be sharable). Public URLs aren't supported on
    Free Trial Storage Accounts (allowBlobPublicAccess=false), so we proxy.
    """
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return func.HttpResponse("not configured", status_code=500)
    path = (req.route_params.get("path") or "").strip("/")
    if not path.endswith(".png") or ".." in path or path.count("/") > 3:
        return func.HttpResponse("bad path", status_code=400)

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    from azure.core.exceptions import ResourceNotFoundError
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{_config.storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            client = svc.get_blob_client("share-cards", path)
            try:
                stream = await client.download_blob()
                body = await stream.readall()
            except ResourceNotFoundError:
                return func.HttpResponse("not found", status_code=404)
    finally:
        await creds.close()
    return func.HttpResponse(
        body, status_code=200, mimetype="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.route(route="gamification/today_market", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_today_market(req: func.HttpRequest) -> func.HttpResponse:
    """§A5 — Latest 6-slot market report for Mini App Home card.
    Returns the most recent slot's rendered text + the slot label so the
    Mini App can show a one-line teaser + "더 보기" button."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"available": False}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS)

    # User's profile to know persona + language
    profile_call = _profile_repo.get_or_create(user_key=user_key, default_language="ko", default_persona="buffett")
    profile = await profile_call if hasattr(profile_call, "__await__") else profile_call

    from services.slot_report import fetch_latest_slot_report, SLOTS_BY_ID
    result = await fetch_latest_slot_report(
        _config.storage_account_name, profile.persona_key, profile.language,
    )
    if result is None:
        return func.HttpResponse(json.dumps({"available": False}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS)
    slot_id, rendered_text = result
    slot = SLOTS_BY_ID.get(slot_id)
    payload = {
        "available": True,
        "slot_id": slot_id,
        "slot_name_kr": slot.name_kr if slot else slot_id,
        "slot_name_en": slot.name_en if slot else slot_id,
        "kst_time": slot.kst_time if slot else "",
        "rendered_text": rendered_text,
        "persona": profile.persona_key,
        "language": profile.language,
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=120"  # 2 min — slot updates every few hours
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/persona", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def gamification_set_persona(req: func.HttpRequest) -> func.HttpResponse:
    """§A4 — Switch the user's persona from the Mini App.
    Body: {"persona_key": "buffett" | "dalio" | "wood"}
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "bad json"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS)

    persona_key = (body.get("persona_key") or "").strip().lower()
    if persona_key not in ("buffett", "dalio", "wood"):
        return func.HttpResponse(json.dumps({"error": "invalid persona"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS)

    update_res = _profile_repo.update(user_key, persona_key=persona_key)
    profile = await update_res if hasattr(update_res, "__await__") else update_res
    return func.HttpResponse(
        json.dumps({"success": True, "persona_key": profile.persona_key}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS,
    )


@app.route(route="gamification/welcome_event/status", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_welcome_event_status(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-N — Return the user's active (or recently resolved) welcome event."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"active": False}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS)

    from services.welcome_event import get_active_welcome_event
    evt = await get_active_welcome_event(_config.storage_account_name, user_key)
    if evt is None:
        return func.HttpResponse(
            json.dumps({"active": False}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS,
        )
    payload = {
        "active": True,
        "event_id": evt.event_id,
        "started_btc_price": evt.started_btc_price,
        "started_at": evt.started_at,
        "target_at": evt.target_at,
        "status": evt.status,                   # open | predicted | resolved
        "user_prediction": evt.user_prediction,
        "actual_price": evt.actual_price,
        "correct": evt.correct,
        "tolerance_pct": 0.3,
        "reward_correct": 500,
        "reward_participation": 50,
    }
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=5"  # very short — countdown is live
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/prediction_history", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def gamification_prediction_history(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-B — Return the user's recent prediction submissions across all markets.
    Used by Mini App Predict tab to show history + accuracy. Limited to last 14 days
    × 3 markets to keep response small."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"items": []}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS)

    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient
    from datetime import timedelta as _td

    user_short = user_key.replace("tg:", "")
    items: list[dict] = []
    creds = DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{_config.storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client("predictions")
            prefix = f"{user_short}/"
            cutoff = datetime.now(timezone.utc) - _td(days=14)
            async for blob in container.list_blobs(name_starts_with=prefix):
                if blob.last_modified and blob.last_modified < cutoff:
                    continue
                try:
                    client = container.get_blob_client(blob.name)
                    stream = await client.download_blob()
                    body = await stream.readall()
                    pred = json.loads(body)
                except Exception:
                    continue
                items.append({
                    "market": pred.get("market"),
                    "window_id": pred.get("window_id"),
                    "direction": pred.get("direction"),
                    "predicted_price": pred.get("predicted_price"),
                    "submitted_at": pred.get("submitted_at"),
                    "resolved": pred.get("resolved", False),
                    "actual_direction": pred.get("actual_direction"),
                    "actual_price": pred.get("actual_price"),
                    "correct": pred.get("correct", False),
                })
    except Exception:
        logger.exception("prediction history read failed")
    finally:
        await creds.close()

    items.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    items = items[:30]   # cap
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=15"
    return func.HttpResponse(
        json.dumps({"items": items}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/welcome_event/predict", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def gamification_welcome_event_predict(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-N — Submit BTC price guess for the welcome mini-event."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS_POST)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS_POST)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS_POST)

    try:
        body = req.get_json()
        price = float(body.get("predicted_price", 0))
    except (ValueError, TypeError):
        return func.HttpResponse(json.dumps({"error": "bad input"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    from services.welcome_event import submit_welcome_prediction
    ok, err, payload = await submit_welcome_prediction(
        _config.storage_account_name, user_key, price,
        repo=_profile_repo, usage_logger=_usage_logger,
    )
    if not ok:
        return func.HttpResponse(json.dumps({"error": err}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)
    return func.HttpResponse(json.dumps({"success": True, **(payload or {})}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS_POST)


@app.timer_trigger(
    schedule="0 */1 * * * *",   # every 1 minute
    arg_name="timer", run_on_startup=False, use_monitor=False,
)
async def settle_welcome_events(timer: func.TimerRequest) -> None:
    """§T2E-N — Resolve any welcome mini-events whose 30min target has passed."""
    await _bootstrap()
    if not _config or not _config.storage_account_name:
        return
    from services.welcome_event import settle_pending_welcome_events
    try:
        awarded = await settle_pending_welcome_events(
            _config.storage_account_name, repo=_profile_repo, usage_logger=_usage_logger,
        )
        if awarded:
            logger.info("welcome event settle: %d awarded", len(awarded))
    except Exception:
        logger.exception("settle_welcome_events failed")


@app.route(route="gamification/predict", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def gamification_predict(req: func.HttpRequest) -> func.HttpResponse:
    """§T2E-B — Submit a daily prediction. Body:
       {"market":"kospi"|"nasdaq", "direction":"up"|"down"}
    or {"market":"btc", "predicted_price": 87432.50}
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS_POST)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS_POST)
    if not _config or not _config.storage_account_name:
        return func.HttpResponse(json.dumps({"error": "not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS_POST)

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "bad json"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    # Market is case-sensitive for tickers (TSLA, NVDA), lowercase for index
    raw_market = (body.get("market") or "").strip()
    # Normalize: kospi/nasdaq → lower; TSLA/NVDA → upper
    if raw_market.lower() in ("kospi", "nasdaq"):
        market = raw_market.lower()
    else:
        market = raw_market.upper()
    profile_get = _profile_repo.get_or_create(user_key=user_key, default_language="ko", default_persona="buffett")
    profile = await profile_get if hasattr(profile_get, "__await__") else profile_get

    from services.prediction_service import (
        submit_daily_prediction, submit_btc_hourly_prediction, MARKET_WINDOWS,
    )
    if market in MARKET_WINDOWS:
        # KOSPI / NASDAQ index OR per-ticker (TSLA / NVDA / ...)
        ok, err, payload = await submit_daily_prediction(
            _config.storage_account_name, user_key, profile.anon_user_id,
            market, (body.get("direction") or "").strip().lower(),
            repo=_profile_repo, usage_logger=_usage_logger,
        )
    elif market.lower() == "btc":
        direction = (body.get("direction") or "").strip().lower()
        ok, err, payload = await submit_btc_hourly_prediction(
            _config.storage_account_name, user_key, profile.anon_user_id, direction,
            repo=_profile_repo, usage_logger=_usage_logger,
        )
    else:
        return func.HttpResponse(json.dumps({"error": "unknown market"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    if not ok:
        return func.HttpResponse(json.dumps({"error": err}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)
    return func.HttpResponse(json.dumps({"success": True, **(payload or {})}, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS_POST)


@app.route(route="gamification/attend", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def gamification_attend(req: func.HttpRequest) -> func.HttpResponse:
    """Daily attendance check-in. Idempotent per KST day."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS_POST)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(
            json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS_POST,
        )

    from services.attendance import daily_check_in
    result = await daily_check_in(
        _profile_repo, user_key, usage_logger=_usage_logger,
    )
    payload = {
        "success": result.success,
        "reason": result.reason,
        "base_points": result.base_points,
        "streak_bonus": result.streak_bonus,
        "streak_days": result.streak_days,
    }
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS_POST,
    )


# ---------------------------------------------------------------------
# §SAJU — Four Pillars (Saju) reading + element-matched stock recommendations
# ---------------------------------------------------------------------

@app.route(route="gamification/saju/profile", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def saju_save_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Persist user's birth date + hour. Body: {birth_date: 'YYYY-MM-DD', birth_hour: 0-23 | null}."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS_POST)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS_POST)

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "invalid_json"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    birth_date = (body or {}).get("birth_date", "").strip()
    birth_hour_raw = (body or {}).get("birth_hour")
    birth_hour: int | None = None
    if birth_hour_raw is not None and birth_hour_raw != "":
        try:
            birth_hour = int(birth_hour_raw)
            if not (0 <= birth_hour <= 23):
                raise ValueError
        except (TypeError, ValueError):
            return func.HttpResponse(
                json.dumps({"error": "invalid_birth_hour"}),
                status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    from services.saju_service import save_birth_data
    try:
        await save_birth_data(_profile_repo, user_key,
                              birth_date=birth_date, birth_hour=birth_hour)
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "invalid_birth_date"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    return func.HttpResponse(json.dumps({"success": True}),
        status_code=200, mimetype="application/json", headers=_CORS_HEADERS_POST)


@app.route(route="gamification/saju/today", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def saju_today(req: func.HttpRequest) -> func.HttpResponse:
    """Today's Saju reading + 5 stock picks (1 free, 4 locked unless free trial / unlocked)."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS)

    from services.saju_service import (
        build_today_payload, has_birth_data, mark_first_use,
        reset_unlocks_if_new_day,
    )

    try:
        profile = await _profile_repo.get_or_create(
            user_key=user_key, default_language="ko", default_persona="buffett",
        )
    except AttributeError:
        profile = _profile_repo.get_or_create(
            user_key=user_key, default_language="ko", default_persona="buffett")

    if not has_birth_data(profile):
        return func.HttpResponse(
            json.dumps({"available": False, "reason": "birth_data_missing"}),
            status_code=200, mimetype="application/json", headers=_CORS_HEADERS,
        )

    profile = await reset_unlocks_if_new_day(_profile_repo, user_key, profile)
    profile = await mark_first_use(_profile_repo, user_key, profile)

    payload = build_today_payload(profile, user_key)
    payload["available"] = True

    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "private, max-age=60"
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=200, mimetype="application/json", headers=headers,
    )


@app.route(route="gamification/saju/unlock", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST", "OPTIONS"])
async def saju_unlock(req: func.HttpRequest) -> func.HttpResponse:
    """Spend points to unlock one of today's locked recommendations.
    Body: {ticker: 'NVDA'}."""
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS_POST)
    await _bootstrap()
    user_key = await _verify_telegram_init_data_get_userkey(req)
    if not user_key:
        return func.HttpResponse(json.dumps({"error": "unauthorized"}),
            status_code=401, mimetype="application/json", headers=_CORS_HEADERS_POST)

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "invalid_json"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    ticker = (body or {}).get("ticker", "").strip().upper()
    if not ticker:
        return func.HttpResponse(json.dumps({"error": "missing_ticker"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    from services.saju_service import has_birth_data, unlock_ticker

    try:
        profile = await _profile_repo.get_or_create(
            user_key=user_key, default_language="ko", default_persona="buffett",
        )
    except AttributeError:
        profile = _profile_repo.get_or_create(
            user_key=user_key, default_language="ko", default_persona="buffett")

    if not has_birth_data(profile):
        return func.HttpResponse(json.dumps({"error": "birth_data_missing"}),
            status_code=400, mimetype="application/json", headers=_CORS_HEADERS_POST)

    ok, reason, updated = await unlock_ticker(
        _profile_repo, user_key, profile, ticker, usage_logger=_usage_logger,
    )
    payload = {"success": ok, "reason": reason}
    if updated is not None:
        payload["points_balance"] = updated.points_balance
    status = 200 if ok else 402 if reason == "insufficient_points" else 400
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=status, mimetype="application/json", headers=_CORS_HEADERS_POST,
    )


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
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Telegram-Init-Data",
    "Access-Control-Max-Age": "3600",
}

_CORS_HEADERS_POST = _CORS_HEADERS  # alias for clarity at POST endpoints


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

            # LLM 호출 절감 — read v2.json totals (commentary_hit count)
            llm_calls_saved = 0
            try:
                v2_blob = svc.get_blob_client("dashboard", "v2.json")
                v2_stream = await v2_blob.download_blob()
                v2_body = await v2_stream.readall()
                v2_doc = json.loads(v2_body)
                totals = v2_doc.get("totals", {})
                llm_calls_saved = int(totals.get("llm_calls_saved_total", 0))
            except Exception:
                # No v2 yet — fallback to 0
                llm_calls_saved = 0
    finally:
        await creds.close()

    payload = {
        "cumulative_users": cumulative_users,
        "active_today": active_today,
        "mau": mau,
        "llm_calls_saved": llm_calls_saved,
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


@app.route(route="deepseek_balance", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "OPTIONS"])
async def deepseek_balance(req: func.HttpRequest) -> func.HttpResponse:
    """Operator-only: query DeepSeek's /user/balance endpoint with our API key.
    Returns the OpenAI-compat balance object. Cached 30 min server-side.
    """
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=_CORS_HEADERS)
    await _bootstrap()
    if not _check_dashboard_key(req):
        return func.HttpResponse(
            json.dumps({"error": "forbidden"}),
            status_code=403, mimetype="application/json", headers=_CORS_HEADERS,
        )

    api_key = (_config.deepseek_api_key if _config else "") or ""
    if not api_key:
        return func.HttpResponse(
            json.dumps({"error": "DEEPSEEK_API_KEY not configured"}),
            status_code=500, mimetype="application/json", headers=_CORS_HEADERS,
        )

    # Process-local 30-min cache to avoid hammering DeepSeek
    import time
    global _balance_cache
    try:
        _balance_cache  # noqa: F823
    except NameError:
        _balance_cache = {"ts": 0.0, "data": None}
    if time.time() - _balance_cache["ts"] < 1800 and _balance_cache["data"] is not None:
        cached_data = _balance_cache["data"]
        headers = dict(_CORS_HEADERS)
        headers["Cache-Control"] = "public, max-age=600"
        headers["X-Cache-Source"] = "memory"
        return func.HttpResponse(
            json.dumps(cached_data, ensure_ascii=False),
            status_code=200, mimetype="application/json", headers=headers,
        )

    import aiohttp
    url = "https://api.deepseek.com/user/balance"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    err_body = await resp.text()
                    logger.warning("DeepSeek balance HTTP %d: %s", resp.status, err_body[:200])
                    return func.HttpResponse(
                        json.dumps({"error": f"deepseek http {resp.status}"}),
                        status_code=502, mimetype="application/json", headers=_CORS_HEADERS,
                    )
                body = await resp.json()
    except Exception as exc:
        logger.exception("DeepSeek balance fetch failed")
        return func.HttpResponse(
            json.dumps({"error": str(exc)[:200]}),
            status_code=502, mimetype="application/json", headers=_CORS_HEADERS,
        )

    _balance_cache = {"ts": time.time(), "data": body}
    headers = dict(_CORS_HEADERS)
    headers["Cache-Control"] = "public, max-age=600"
    headers["X-Cache-Source"] = "origin"
    return func.HttpResponse(
        json.dumps(body, ensure_ascii=False),
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
