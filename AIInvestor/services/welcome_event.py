"""§T2E-N — Welcome BTC mini-event (30-minute price guess for new invitees).

Triggered when an invited user completes signup. They get 30 minutes to
guess BTC's price; correct guess (within ±0.3%) earns +500 P. Participation
alone gives +50 P. The event is intentionally HARDER than the regular
hourly BTC mission (±0.5%) because the reward is much bigger (16× the
participation reward instead of 6×) — reflects the spec's "first 5 minutes
matter most" UX principle.

Storage:
    events/welcome_mini/{user_id}/{event_id}.json
    events/welcome_mini/_resolved/{event_id}.json   (audit trail)
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from .gamification_config import POINTS
from .point_ledger import add_points

logger = logging.getLogger(__name__)

CONTAINER = "events"
EVENT_DURATION_MIN = 30
TOLERANCE_PCT = 0.3
PARTICIPATION_PTS = POINTS["welcome_event_participate"]
CORRECT_PTS = POINTS["welcome_event_correct"]


@dataclass
class WelcomeEvent:
    event_id: str
    user_id: str
    anon_user_id: str
    inviter_anon: str
    started_btc_price: float
    started_at: str
    target_at: str
    user_prediction: float | None = None
    submitted_at: str = ""
    resolved: bool = False
    actual_price: float | None = None
    correct: bool = False
    resolved_at: str = ""
    status: str = "open"   # open | predicted | resolved | expired


async def trigger_welcome_event(
    storage_account_name: str,
    user_key: str,
    anon_user_id: str,
    inviter_anon: str,
    btc_price_now: float,
    *,
    credential=None,
) -> str | None:
    """Create a fresh welcome event for the invitee. Returns event_id, or
    None if one already exists (idempotent — only one welcome event per user lifetime)."""
    user_short = user_key.replace("tg:", "")
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(CONTAINER)
            try:
                await container.create_container()
            except ResourceExistsError:
                pass

            # Existence check — only one welcome event per user
            prefix = f"welcome_mini/{user_short}/"
            async for _ in container.list_blobs(name_starts_with=prefix):
                return None  # already triggered

            now = datetime.now(timezone.utc)
            event_id = uuid.uuid4().hex[:12]
            target_at = now + timedelta(minutes=EVENT_DURATION_MIN)
            evt = WelcomeEvent(
                event_id=event_id,
                user_id=user_key,
                anon_user_id=anon_user_id,
                inviter_anon=inviter_anon,
                started_btc_price=btc_price_now,
                started_at=now.isoformat(timespec="seconds"),
                target_at=target_at.isoformat(timespec="seconds"),
                status="open",
            )
            blob = svc.get_blob_client(CONTAINER, f"{prefix}{event_id}.json")
            await blob.upload_blob(
                json.dumps(asdict(evt), ensure_ascii=False).encode(),
                overwrite=False, content_type="application/json",
            )
            return event_id
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()


async def submit_welcome_prediction(
    storage_account_name: str,
    user_key: str,
    predicted_price: float,
    *,
    repo,
    usage_logger=None,
    credential=None,
) -> tuple[bool, str, dict | None]:
    """Submit the user's BTC guess. Returns (ok, error, payload).
    Errors: no_active_event | already_predicted | deadline_passed | invalid_price"""
    if predicted_price <= 0 or predicted_price > 10_000_000:
        return False, "invalid_price", None

    user_short = user_key.replace("tg:", "")
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(CONTAINER)
            prefix = f"welcome_mini/{user_short}/"
            target_blob = None
            async for blob in container.list_blobs(name_starts_with=prefix):
                client = container.get_blob_client(blob.name)
                stream = await client.download_blob()
                evt = WelcomeEvent(**json.loads(await stream.readall()))
                if evt.status == "open":
                    target_blob = (client, evt)
                    break

            if not target_blob:
                return False, "no_active_event", None

            client, evt = target_blob
            target_dt = datetime.fromisoformat(evt.target_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= target_dt:
                return False, "deadline_passed", None
            if evt.user_prediction is not None:
                return False, "already_predicted", None

            evt.user_prediction = float(predicted_price)
            evt.submitted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            evt.status = "predicted"
            await client.upload_blob(
                json.dumps(asdict(evt), ensure_ascii=False).encode(),
                overwrite=True, content_type="application/json",
            )
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()

    # Award participation points immediately
    await add_points(
        repo, user_key, PARTICIPATION_PTS,
        reason="welcome_event_participate", ref=evt.event_id,
        usage_logger=usage_logger,
    )

    # §T2E-C — first-mission completion may unlock inviter's verified bonus
    try:
        from .invite_service import maybe_validate_first_mission
        await maybe_validate_first_mission(repo, user_key, usage_logger=usage_logger)
    except Exception:
        logger.exception("invite validation hook failed (non-fatal)")

    return True, "", {
        "event_id": evt.event_id,
        "started_btc_price": evt.started_btc_price,
        "predicted_price": predicted_price,
        "participation_points": PARTICIPATION_PTS,
        "potential_correct_points": CORRECT_PTS,
        "tolerance_pct": TOLERANCE_PCT,
        "resolves_at": evt.target_at,
    }


async def get_active_welcome_event(
    storage_account_name: str,
    user_key: str,
    *,
    credential=None,
) -> WelcomeEvent | None:
    """Return the user's currently active (or recently completed) welcome event.

    'Active' means status ∈ {open, predicted} AND target_at hasn't passed yet,
    OR it has passed and is settled (we still return for 1 hour after settle so
    the user sees the result).
    """
    user_short = user_key.replace("tg:", "")
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(CONTAINER)
            prefix = f"welcome_mini/{user_short}/"
            try:
                async for blob in container.list_blobs(name_starts_with=prefix):
                    client = container.get_blob_client(blob.name)
                    stream = await client.download_blob()
                    evt = WelcomeEvent(**json.loads(await stream.readall()))
                    # Show if still open/predicted, OR resolved within last 1h
                    if evt.status in ("open", "predicted"):
                        return evt
                    if evt.status == "resolved" and evt.resolved_at:
                        try:
                            rdt = datetime.fromisoformat(evt.resolved_at.replace("Z", "+00:00"))
                            if (datetime.now(timezone.utc) - rdt) < timedelta(hours=1):
                                return evt
                        except (ValueError, AttributeError):
                            pass
            except ResourceNotFoundError:
                pass
            return None
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()


async def settle_pending_welcome_events(
    storage_account_name: str,
    *,
    repo,
    usage_logger=None,
    credential=None,
) -> dict[str, int]:
    """Resolve all welcome events whose target_at has passed. Returns
    {anon_user_id: points_awarded} for telemetry."""
    creds = credential or DefaultAzureCredential()
    awarded: dict[str, int] = {}
    now = datetime.now(timezone.utc)

    # Lazy-import yfinance only when settling
    import yfinance as yf
    import asyncio as _asyncio
    actual_price = None
    try:
        info = await _asyncio.to_thread(lambda: yf.Ticker("BTC-USD").fast_info)
        actual_price = float(info.last_price) if info and info.last_price else None
    except Exception:
        logger.exception("BTC price fetch failed")
    if not actual_price:
        return {}

    try:
        async with BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(CONTAINER)
            try:
                await container.create_container()
            except ResourceExistsError:
                pass
            async for blob in container.list_blobs(name_starts_with="welcome_mini/"):
                if blob.name.startswith("welcome_mini/_"):
                    continue  # internal
                client = container.get_blob_client(blob.name)
                try:
                    stream = await client.download_blob()
                    evt = WelcomeEvent(**json.loads(await stream.readall()))
                except Exception:
                    continue

                if evt.status not in ("open", "predicted"):
                    continue
                target_dt = datetime.fromisoformat(evt.target_at.replace("Z", "+00:00"))
                if now < target_dt:
                    continue

                evt.actual_price = actual_price
                evt.resolved = True
                evt.resolved_at = now.isoformat(timespec="seconds")

                if evt.user_prediction is not None:
                    err_pct = abs(evt.user_prediction - actual_price) / actual_price * 100
                    evt.correct = err_pct <= TOLERANCE_PCT
                    if evt.correct:
                        try:
                            await add_points(
                                repo, evt.user_id, CORRECT_PTS,
                                reason="welcome_event_correct", ref=evt.event_id,
                                usage_logger=usage_logger,
                            )
                            awarded[evt.anon_user_id] = CORRECT_PTS
                        except Exception:
                            logger.exception("welcome event award failed user=%s", evt.user_id)
                    evt.status = "resolved"
                else:
                    evt.status = "expired"  # never predicted — no payout

                await client.upload_blob(
                    json.dumps(asdict(evt), ensure_ascii=False).encode(),
                    overwrite=True, content_type="application/json",
                )
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()

    return awarded
