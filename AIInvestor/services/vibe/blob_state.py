"""§Vibe — Blob 영속화 helper.

ARDS-X 의 히스테리시스 상태 등 cron 호출 간에 살아남아야 하는 작은 JSON 을
Azure Blob 에 저장. 대시보드 산출물(latest.json) 등 큰 객체는 별도 writer 사용.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

CONTAINER = "vibe"


async def load_json(account_name: str, path: str, *, default: Any = None,
                    credential=None) -> Any:
    """Blob 에서 JSON 로드. 없으면 default 반환 (raise X)."""
    from azure.core.exceptions import ResourceNotFoundError
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient

    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            bc = svc.get_blob_client(CONTAINER, path)
            try:
                body = await (await bc.download_blob()).readall()
            except ResourceNotFoundError:
                return default
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        logger.warning("vibe.blob_state: %s corrupt, returning default", path)
        return default


async def save_json(account_name: str, path: str, payload: Any,
                    credential=None) -> None:
    """JSON 을 Blob 에 overwrite 저장. 컨테이너 없으면 생성."""
    from azure.identity.aio import DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    creds = credential or DefaultAzureCredential()
    try:
        async with BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=creds,
        ) as svc:
            container = svc.get_container_client(CONTAINER)
            try:
                await container.create_container()
            except Exception:
                pass
            await container.get_blob_client(path).upload_blob(body, overwrite=True)
    finally:
        if credential is None and hasattr(creds, "close"):
            await creds.close()
