"""Provider Management and OAuth Callback API Routes."""

from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.config import get_settings
from backend.app.core.security import generate_oauth_state, verify_oauth_state
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.repositories.provider_repository import ProviderRepository
from backend.app.schemas.provider import ProviderStatusResponse, ProviderConnectResponse
from backend.app.oauth.google import GoogleOAuthHandler
from backend.app.oauth.microsoft import MicrosoftOAuthHandler
from backend.app.oauth.dropbox import DropboxOAuthHandler
from backend.app.core.logging import logger
import time
import asyncio

_provider_cache: Dict[str, Any] = {}

settings = get_settings()
router = APIRouter(prefix="/providers", tags=["Storage Providers"])


@router.get("", response_model=List[ProviderStatusResponse])
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    user_connections = {c.provider: c for c in await repo.list_by_user(current_user.id)}

    supported = [
        {"id": "google_drive", "name": "Google Drive"},
        {"id": "onedrive", "name": "Microsoft OneDrive"},
        {"id": "dropbox", "name": "Dropbox"},
        {"id": "local", "name": "Local Storage"},
    ]

    def _format_bytes(b: int) -> str:
        if b <= 0:
            return "0 B"
        curr = float(b)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if curr < 1024.0:
                return f"{curr:.1f} {unit}" if unit in ['GB', 'TB'] else f"{int(curr)} {unit}"
            curr /= 1024.0
        return f"{curr:.1f} PB"

    response = []
    for p in supported:
        p_id = p["id"]
        if p_id == "local":
            import shutil
            from backend.app.providers.local import LocalFileProvider
            drives = LocalFileProvider.get_system_drives()
            all_total = sum(d["total_bytes"] for d in drives)
            drive_names = ", ".join(d["drive"] for d in drives)
            local_path = Path(settings.LOCAL_STORAGE_ROOT).resolve()
            local_files = [f for f in local_path.rglob("*") if f.is_file()]
            local_size = sum(f.stat().st_size for f in local_files)
            try:
                total_b, _, _ = shutil.disk_usage(local_path)
            except Exception:
                total_b = all_total or 256 * 1024 * 1024 * 1024

            percent = round((local_size / total_b) * 100, 1) if total_b > 0 else 0.0
            response.append(
                ProviderStatusResponse(
                    provider="local",
                    name="Local Storage",
                    connected=True,
                    account_identifier=f"Drives: {drive_names}" if drive_names else settings.LOCAL_STORAGE_ROOT,
                    status="connected",
                    file_count=len(local_files),
                    used_storage=_format_bytes(local_size),
                    total_storage=_format_bytes(total_b),
                    used_percent=percent,
                )
            )
        elif p_id == "google_drive":
            conn = user_connections.get(p_id)
            is_connected = conn is not None and conn.status == "connected"
            file_count = 0
            used_storage = "0 B"
            total_storage = "15 GB"
            used_percent = 0.0

            cache_key = f"{current_user.id}:{p_id}"
            now = time.time()
            cached = _provider_cache.get(cache_key)

            if is_connected and cached and (now - cached.get("time", 0) < 60):
                file_count = cached["file_count"]
                used_storage = cached["used_storage"]
                total_storage = cached["total_storage"]
                used_percent = cached["used_percent"]
            elif is_connected:
                creds = repo.decrypt_credentials(conn)
                try:
                    from backend.app.providers.google_drive import GoogleDriveProvider
                    gdrive = GoogleDriveProvider()

                    async def _fetch_gdrive_info():
                        quota_data = await gdrive.get_storage_quota(creds)
                        quota = quota_data.get("storageQuota", {})
                        limit = int(quota.get("limit", 16106127360))
                        usage = int(quota.get("usage", 0))

                        service = gdrive._build_service(creds)
                        count_resp = await asyncio.to_thread(
                            lambda: service.files().list(q="trashed = false", pageSize=100, fields="files(id)").execute()
                        )
                        count = len(count_resp.get("files", []))
                        return usage, limit, count

                    usage, limit, file_count = await asyncio.wait_for(_fetch_gdrive_info(), timeout=3.5)
                    used_storage = _format_bytes(usage)
                    total_storage = _format_bytes(limit)
                    used_percent = round((usage / limit) * 100, 1) if limit > 0 else 0.0

                    _provider_cache[cache_key] = {
                        "time": now,
                        "file_count": file_count,
                        "used_storage": used_storage,
                        "total_storage": total_storage,
                        "used_percent": used_percent,
                    }
                except Exception as e:
                    logger.warning(f"Error fetching Google Drive storage details: {e}")
                    if cached:
                        file_count = cached.get("file_count", 0)
                        used_storage = cached.get("used_storage", "0 B")
                        total_storage = cached.get("total_storage", "15 GB")
                        used_percent = cached.get("used_percent", 0.0)
                    else:
                        is_connected = False
            
            response.append(
                ProviderStatusResponse(
                    provider=p_id,
                    name=p["name"],
                    connected=is_connected,
                    account_identifier=conn.account_identifier if conn else None,
                    connected_at=conn.created_at if conn else None,
                    status="connected" if is_connected else "disconnected",
                    file_count=file_count,
                    used_storage=used_storage,
                    total_storage=total_storage,
                    used_percent=used_percent,
                )
            )
        elif p_id == "onedrive":
            conn = user_connections.get(p_id)
            is_connected = conn is not None and conn.status == "connected"
            file_count = 0
            used_storage = "0 B"
            total_storage = "5 GB"
            used_percent = 0.0
            if is_connected:
                creds = repo.decrypt_credentials(conn)
                try:
                    from backend.app.providers.onedrive import OneDriveProvider
                    onedrive = OneDriveProvider()
                    quota = await onedrive.get_storage_quota(creds)
                    used_b = int(quota.get("used", 0))
                    total_b = int(quota.get("total", 5368709120))
                    used_storage = _format_bytes(used_b)
                    total_storage = _format_bytes(total_b)
                    used_percent = round((used_b / total_b) * 100, 1) if total_b > 0 else 0.0

                    items = await onedrive.list_files(limit=100, credentials=creds)
                    file_count = len(items)
                except Exception as e:
                    logger.warning(f"Error fetching OneDrive storage details: {e}")
                    is_connected = False

            response.append(
                ProviderStatusResponse(
                    provider=p_id,
                    name=p["name"],
                    connected=is_connected,
                    account_identifier=conn.account_identifier if conn else None,
                    connected_at=conn.created_at if conn else None,
                    status="connected" if is_connected else "disconnected",
                    file_count=file_count,
                    used_storage=used_storage,
                    total_storage=total_storage,
                    used_percent=used_percent,
                )
            )
        elif p_id == "dropbox":
            conn = user_connections.get(p_id)
            is_connected = conn is not None and conn.status == "connected"
            file_count = 0
            used_storage = "0 B"
            total_storage = "2 GB"
            used_percent = 0.0
            if is_connected:
                creds = repo.decrypt_credentials(conn)
                try:
                    from backend.app.providers.dropbox import DropboxProvider
                    dropbox_prov = DropboxProvider()
                    quota = await dropbox_prov.get_storage_quota(creds)
                    used_b = int(quota.get("used", 0))
                    total_b = int(quota.get("total", 2147483648))
                    used_storage = _format_bytes(used_b)
                    total_storage = _format_bytes(total_b)
                    used_percent = round((used_b / total_b) * 100, 1) if total_b > 0 else 0.0

                    items = await dropbox_prov.list_files(limit=100, credentials=creds)
                    file_count = len(items)
                except Exception as e:
                    logger.warning(f"Error fetching Dropbox storage details: {e}")
                    is_connected = False

            response.append(
                ProviderStatusResponse(
                    provider=p_id,
                    name=p["name"],
                    connected=is_connected,
                    account_identifier=conn.account_identifier if conn else None,
                    connected_at=conn.created_at if conn else None,
                    status="connected" if is_connected else "disconnected",
                    file_count=file_count,
                    used_storage=used_storage,
                    total_storage=total_storage,
                    used_percent=used_percent,
                )
            )
        else:
            conn = user_connections.get(p_id)
            response.append(
                ProviderStatusResponse(
                    provider=p_id,
                    name=p["name"],
                    connected=conn is not None and conn.status == "connected",
                    account_identifier=conn.account_identifier if conn else None,
                    connected_at=conn.created_at if conn else None,
                    status=conn.status if conn else "disconnected",
                    file_count=0,
                    used_storage="0 B",
                    total_storage="0 B",
                    used_percent=0.0,
                )
            )

    return response


@router.get("/local/drives")
async def get_local_drives(
    current_user: User = Depends(get_current_user),
):
    """Returns detected system drives with volume info and formatted byte sizes."""
    from backend.app.providers.local import LocalFileProvider
    drives = LocalFileProvider.get_system_drives()

    def _format_bytes(b: int) -> str:
        if b <= 0:
            return "0 B"
        curr = float(b)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if curr < 1024.0:
                return f"{curr:.1f} {unit}" if unit in ['GB', 'TB'] else f"{int(curr)} {unit}"
            curr /= 1024.0
        return f"{curr:.1f} PB"

    return [
        {
            **d,
            "total_formatted": _format_bytes(d["total_bytes"]),
            "used_formatted": _format_bytes(d["used_bytes"]),
            "free_formatted": _format_bytes(d["free_bytes"]),
        }
        for d in drives
    ]


@router.get("/local/browse")
async def browse_local_filesystem(
    path: Optional[str] = Query(None, description="Path to browse, or 'root' for drives list"),
    current_user: User = Depends(get_current_user),
):
    """Browses directories and files on the local machine (drives or specific folders)."""
    from backend.app.providers.local import LocalFileProvider
    local_provider = LocalFileProvider()
    try:
        data = local_provider.browse_path(path)
        return data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error browsing local path {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider}/connect", response_model=ProviderConnectResponse)
async def connect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    state = generate_oauth_state(current_user.id)
    if provider == "google_drive":
        auth_url = GoogleOAuthHandler.get_authorization_url(state)
    elif provider == "onedrive":
        auth_url = MicrosoftOAuthHandler.get_authorization_url(state)
    elif provider == "dropbox":
        auth_url = DropboxOAuthHandler.get_authorization_url(state)
    else:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' does not support OAuth.")

    return ProviderConnectResponse(provider=provider, authorization_url=auth_url, state=state)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user_id = verify_oauth_state(state)
    if not user_id:
        logger.warning(f"Invalid or expired OAuth state parameter received for {provider}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/storage?error=invalid_state")

    repo = ProviderRepository(db)
    try:
        if provider == "google_drive":
            tokens = await GoogleOAuthHandler.exchange_code_for_tokens(code)
        elif provider == "onedrive":
            tokens = await MicrosoftOAuthHandler.exchange_code_for_tokens(code)
        elif provider == "dropbox":
            tokens = await DropboxOAuthHandler.exchange_code_for_tokens(code)
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")

        await repo.upsert_connection(
            user_id=user_id,
            provider=provider,
            account_identifier=tokens.get("email"),
            access_token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            status="connected",
        )
        logger.info(f"Successfully connected provider {provider} for user {user_id}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/storage?success={provider}")
    except Exception as e:
        logger.error(f"OAuth callback handling failed for {provider}: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/storage?error={provider}_auth_failed")


@router.delete("/{provider}")
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if provider == "local":
        raise HTTPException(status_code=400, detail="Local storage provider cannot be disconnected.")

    repo = ProviderRepository(db)
    deleted = await repo.delete_connection(current_user.id, provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider connection not found.")
    return {"message": f"Disconnected {provider} successfully."}
