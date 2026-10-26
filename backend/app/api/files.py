"""File Details, Preview, Streaming Download, and Duplicate Detection API Routes."""

import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.schemas.file import FileRecord, DuplicateGroup
from backend.app.mcp.client import mcp_client
from backend.app.providers.manager import provider_manager
from backend.app.repositories.provider_repository import ProviderRepository
from backend.app.core.logging import logger

router = APIRouter(prefix="/files", tags=["Files"])


def _extract_provider_and_native_id(file_id: str) -> tuple[str, str]:
    """Helper decomposing internal ID prefix (e.g. 'local_...', 'gdrive_...', 'google_drive_...')."""
    if file_id.startswith("local_"):
        return "local", file_id.removeprefix("local_")
    elif file_id.startswith("google_drive_"):
        return "google_drive", file_id.removeprefix("google_drive_")
    elif file_id.startswith("gdrive_"):
        return "google_drive", file_id.removeprefix("gdrive_")
    elif file_id.startswith("onedrive_"):
        return "onedrive", file_id.removeprefix("onedrive_")
    elif file_id.startswith("dropbox_"):
        return "dropbox", file_id.removeprefix("dropbox_")
    return "local", file_id


@router.get("/duplicates", response_model=List[DuplicateGroup])
async def find_duplicates(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    duplicates = await mcp_client.call_tool("find_duplicates", {"provider": provider})
    return duplicates if isinstance(duplicates, list) else []


@router.get("/{id}", response_model=FileRecord)
async def get_file_metadata(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider_name, native_id = _extract_provider_and_native_id(id)
    credentials = None
    if provider_name != "local":
        repo = ProviderRepository(db)
        conn = await repo.get_by_user_and_provider(current_user.id, provider_name)
        if not conn:
            raise HTTPException(status_code=403, detail=f"Provider '{provider_name}' is not connected.")
        credentials = repo.decrypt_credentials(conn)

    try:
        record = await provider_manager.get_file_metadata(
            provider_name=provider_name,
            file_id=native_id,
            credentials=credentials,
        )
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error retrieving file metadata {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/content")
async def get_file_content_preview(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider_name, native_id = _extract_provider_and_native_id(id)
    credentials = None
    if provider_name != "local":
        repo = ProviderRepository(db)
        conn = await repo.get_by_user_and_provider(current_user.id, provider_name)
        if not conn:
            raise HTTPException(status_code=403, detail=f"Provider '{provider_name}' is not connected.")
        credentials = repo.decrypt_credentials(conn)

    try:
        content = await provider_manager.get_file_content(
            provider_name=provider_name,
            file_id=native_id,
            credentials=credentials,
        )
        return {"id": id, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file content: {e}")


@router.get("/{id}/download")
async def download_file(
    id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    provider_name, native_id = _extract_provider_and_native_id(id)
    credentials = None
    if provider_name != "local":
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required for cloud downloads.")
        repo = ProviderRepository(db)
        conn = await repo.get_by_user_and_provider(current_user.id, provider_name)
        if not conn:
            raise HTTPException(status_code=403, detail=f"Provider '{provider_name}' is not connected.")
        credentials = repo.decrypt_credentials(conn)

    try:
        file_bytes, filename, mime_type = await provider_manager.download_file(
            provider_name=provider_name,
            file_id=native_id,
            credentials=credentials,
        )
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=mime_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Download failed for {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")
