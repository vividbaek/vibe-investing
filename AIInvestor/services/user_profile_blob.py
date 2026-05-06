"""Blob Storage backed UserProfileRepo with in-instance memory cache (TTL 5min).

Layout:
    container "users"
      └── users/<anon[:2]>/<anon>.json     # one blob per user, partitioned by hash prefix

Cache:
    process-local dict; entries evicted after 5 minutes.
    ETag stored alongside the cached profile so concurrent updates from another
    Functions instance are detected on the next read (412 Precondition Failed).

Public surface matches the SQLite UserProfileRepo so handlers don't change.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timezone

from azure.core import MatchConditions
from azure.core.exceptions import ResourceNotFoundError, ResourceModifiedError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

from .user_profile import UserProfile, _now_iso, make_anon_user_id

logger = logging.getLogger(__name__)

CONTAINER = "users"
DEFAULT_TTL_SECONDS = 300  # 5 minutes


def _blob_path(anon_user_id: str) -> str:
    return f"{anon_user_id[:2]}/{anon_user_id}.json"


class BlobUserProfileRepo:
    """Blob-backed repo with TTL 5min memory cache.

    Same public surface as `services.user_profile.UserProfileRepo`.
    Construction is async-friendly: pass an account name + a credential
    or pass a connection string for local emulator testing.
    """

    def __init__(
        self,
        account_url: str,
        salt: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        credential=None,
    ) -> None:
        self._account_url = account_url
        self._salt = salt
        self._ttl = ttl_seconds
        self._credential = credential or DefaultAzureCredential()
        self._service: BlobServiceClient | None = None

        # cache[user_key] = (expires_at_monotonic, profile, etag)
        self._cache: dict[str, tuple[float, UserProfile, str | None]] = {}
        self._lock = asyncio.Lock()

    async def _client(self) -> BlobServiceClient:
        if self._service is None:
            self._service = BlobServiceClient(account_url=self._account_url, credential=self._credential)
        return self._service

    async def aclose(self) -> None:
        if self._service is not None:
            await self._service.close()
            self._service = None
        if hasattr(self._credential, "close"):
            await self._credential.close()

    # ------------------------------------------------------------
    # Public API — mirrors UserProfileRepo
    # ------------------------------------------------------------

    async def get_or_create(
        self,
        user_key: str,
        default_language: str,
        default_persona: str,
    ) -> UserProfile:
        cached = self._cache_get(user_key)
        if cached is not None:
            return cached

        anon = make_anon_user_id(user_key, self._salt)
        path = _blob_path(anon)

        async with self._lock:
            cached = self._cache_get(user_key)  # double-check inside lock
            if cached is not None:
                return cached

            try:
                profile, etag = await self._download(path)
            except ResourceNotFoundError:
                profile = UserProfile(
                    user_key=user_key,
                    anon_user_id=anon,
                    persona_key=default_persona,
                    language=default_language,
                    intro_seen=False,
                    research_consent=False,
                    onboarding_step="greeting",
                    interest_tags=[],
                    watchlist_tickers=[],
                    created_at=_now_iso(),
                    updated_at=_now_iso(),
                )
                etag = await self._upload(path, profile, if_none_match="*")

            self._cache_put(user_key, profile, etag)
            return profile

    async def update(self, user_key: str, **fields) -> UserProfile:
        async with self._lock:
            current = self._cache.get(user_key)
            if current is None:
                # fall back to a read; preserves user_key→anon mapping
                anon = make_anon_user_id(user_key, self._salt)
                profile, etag = await self._download(_blob_path(anon))
            else:
                _, profile, etag = current

            for k, v in fields.items():
                if hasattr(profile, k):
                    setattr(profile, k, v)
            profile.updated_at = _now_iso()

            try:
                etag = await self._upload(_blob_path(profile.anon_user_id), profile, if_match=etag)
            except ResourceModifiedError:
                # Another instance wrote first — re-read and retry once.
                profile, etag = await self._download(_blob_path(profile.anon_user_id))
                for k, v in fields.items():
                    if hasattr(profile, k):
                        setattr(profile, k, v)
                profile.updated_at = _now_iso()
                etag = await self._upload(_blob_path(profile.anon_user_id), profile, if_match=etag)

            self._cache_put(user_key, profile, etag)
            return profile

    async def get(self, user_key: str) -> UserProfile:
        cached = self._cache_get(user_key)
        if cached is not None:
            return cached
        anon = make_anon_user_id(user_key, self._salt)
        profile, etag = await self._download(_blob_path(anon))
        self._cache_put(user_key, profile, etag)
        return profile

    async def delete(self, user_key: str) -> bool:
        anon = make_anon_user_id(user_key, self._salt)
        client = (await self._client()).get_blob_client(CONTAINER, _blob_path(anon))
        try:
            await client.delete_blob()
            removed = True
        except ResourceNotFoundError:
            removed = False
        self._cache.pop(user_key, None)
        return removed

    # ------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------

    def _cache_get(self, user_key: str) -> UserProfile | None:
        entry = self._cache.get(user_key)
        if entry is None:
            return None
        expires_at, profile, _etag = entry
        if expires_at < time.monotonic():
            self._cache.pop(user_key, None)
            return None
        return profile

    def _cache_put(self, user_key: str, profile: UserProfile, etag: str | None) -> None:
        self._cache[user_key] = (time.monotonic() + self._ttl, profile, etag)

    async def _download(self, path: str) -> tuple[UserProfile, str]:
        client = (await self._client()).get_blob_client(CONTAINER, path)
        download = await client.download_blob()
        body = await download.readall()
        etag = (await client.get_blob_properties()).etag
        data = json.loads(body)
        return UserProfile(**data), etag

    async def _upload(
        self,
        path: str,
        profile: UserProfile,
        if_match: str | None = None,
        if_none_match: str | None = None,
    ) -> str:
        client = (await self._client()).get_blob_client(CONTAINER, path)
        body = json.dumps(asdict(profile), ensure_ascii=False).encode("utf-8")
        kwargs: dict = {"overwrite": True, "content_type": "application/json"}
        # azure-storage-blob requires MatchConditions enum, not raw strings.
        # IfNotModified = If-Match: <etag>     (overwrite only if unchanged)
        # IfMissing     = If-None-Match: *     (create only if blob absent)
        if if_match:
            kwargs["etag"] = if_match
            kwargs["match_condition"] = MatchConditions.IfNotModified
        elif if_none_match == "*":
            # Concurrent-create guard. overwrite=True conflicts with IfMissing
            # because the SDK interprets it as "always overwrite". Drop it.
            kwargs["overwrite"] = False
            kwargs["match_condition"] = MatchConditions.IfMissing
        result = await client.upload_blob(body, **kwargs)
        return result["etag"]
