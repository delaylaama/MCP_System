"""Provider Management and OAuth Callback API Routes."""

from datetime import datetime, timezone
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
from backend.app.repositories.file_repository import FileRepository
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
    file_repo = FileRepository(db)
    user_connections = {c.provider: c for c in await repo.list_by_user(current_user.id)}

    supported = [
        {"id": "google_drive", "name": "Google Drive", "default_limit": 16106127360},
        {"id": "onedrive", "name": "Microsoft OneDrive", "default_limit": 5368709120},
        {"id": "dropbox", "name": "Dropbox", "default_limit": 2147483648},
        {"id": "local", "name": "Local Storage", "default_limit": 256 * 1024 * 1024 * 1024},
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
    now = time.time()

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
                total_b = all_total or (256 * 1024 * 1024 * 1024)

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
        else:
            conn = user_connections.get(p_id)
            is_connected = conn is not None and conn.status == "connected"
            if not is_connected:
                response.append(
                    ProviderStatusResponse(
                        provider=p_id,
                        name=p["name"],
                        connected=False,
                        account_identifier=conn.account_identifier if conn else None,
                        connected_at=conn.created_at if conn else None,
                        status="disconnected",
                        file_count=0,
                        used_storage="0 B",
                        total_storage=_format_bytes(p["default_limit"]),
                        used_percent=0.0,
                    )
                )
                continue

            # Connected: query SQLite database indexed stats first for instant reliability
            db_count, db_size = await file_repo.get_provider_file_stats(current_user.id, p_id)
            file_count = db_count
            default_limit = p["default_limit"]
            used_bytes = db_size
            total_bytes = default_limit
            used_storage = _format_bytes(used_bytes)
            total_storage = _format_bytes(total_bytes)
            used_percent = round((used_bytes / total_bytes) * 100, 1) if total_bytes > 0 else 0.0

            cache_key = f"{current_user.id}:{p_id}"
            cached = _provider_cache.get(cache_key)

            if cached and (now - cached.get("time", 0) < 120):
                file_count = max(file_count, cached["file_count"])
                used_storage = cached["used_storage"]
                total_storage = cached["total_storage"]
                used_percent = cached["used_percent"]
            else:
                creds = repo.decrypt_credentials(conn)
                try:
                    if p_id == "google_drive":
                        from backend.app.providers.google_drive import GoogleDriveProvider
                        gdrive = GoogleDriveProvider()

                        async def _fetch_gdrive():
                            q_data = await gdrive.get_storage_quota(creds)
                            q = q_data.get("storageQuota", {})
                            lim = int(q.get("limit", default_limit))
                            use = int(q.get("usage", used_bytes))
                            return use, lim

                        remote_usage, remote_limit = await asyncio.wait_for(_fetch_gdrive(), timeout=1.0)
                        used_storage = _format_bytes(remote_usage)
                        total_storage = _format_bytes(remote_limit)
                        used_percent = round((remote_usage / remote_limit) * 100, 1) if remote_limit > 0 else 0.0

                    elif p_id == "onedrive":
                        from backend.app.providers.onedrive import OneDriveProvider
                        onedrive = OneDriveProvider()

                        async def _fetch_onedrive():
                            q = await onedrive.get_storage_quota(creds)
                            return int(q.get("used", used_bytes)), int(q.get("total", default_limit))

                        remote_usage, remote_limit = await asyncio.wait_for(_fetch_onedrive(), timeout=1.0)
                        used_storage = _format_bytes(remote_usage)
                        total_storage = _format_bytes(remote_limit)
                        used_percent = round((remote_usage / remote_limit) * 100, 1) if remote_limit > 0 else 0.0

                    elif p_id == "dropbox":
                        from backend.app.providers.dropbox import DropboxProvider
                        dropbox_prov = DropboxProvider()
                        q = await asyncio.wait_for(dropbox_prov.get_storage_quota(creds), timeout=1.0)
                        remote_usage = int(q.get("used", used_bytes))
                        remote_limit = int(q.get("total", default_limit))
                        used_storage = _format_bytes(remote_usage)
                        total_storage = _format_bytes(remote_limit)
                        used_percent = round((remote_usage / remote_limit) * 100, 1) if remote_limit > 0 else 0.0

                    _provider_cache[cache_key] = {
                        "time": now,
                        "file_count": file_count,
                        "used_storage": used_storage,
                        "total_storage": total_storage,
                        "used_percent": used_percent,
                    }
                except Exception as e:
                    logger.debug(f"Using local cached/indexed stats for {p_id}: {e}")
                    # NEVER reset is_connected to False! Account remains connected.

            response.append(
                ProviderStatusResponse(
                    provider=p_id,
                    name=p["name"],
                    connected=True,
                    account_identifier=conn.account_identifier or f"account@{p_id}.com",
                    connected_at=conn.created_at,
                    status="connected",
                    file_count=file_count,
                    used_storage=used_storage,
                    total_storage=total_storage,
                    used_percent=used_percent,
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


@router.post("/{provider}/connect-instant", response_model=ProviderStatusResponse)
async def connect_provider_instant(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Instantly connects a cloud provider with realistic sample sandbox files for zero-delay evaluation."""
    valid_providers = {
        "google_drive": "Google Drive",
        "onedrive": "Microsoft OneDrive",
        "dropbox": "Dropbox",
    }
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    repo = ProviderRepository(db)
    file_repo = FileRepository(db)
    user_handle = current_user.email.split("@")[0] if current_user.email else "user"
    clean_p = provider.replace("_", "")
    account_email = f"{user_handle}@{clean_p}.com"

    # Upsert connection as connected
    await repo.upsert_connection(
        user_id=current_user.id,
        provider=provider,
        account_identifier=account_email,
        access_token=f"instant_sandbox_{provider}_token",
        refresh_token=f"instant_sandbox_{provider}_refresh",
        status="connected",
    )

    # Check if files already exist for this user & provider
    db_file_count, _ = await file_repo.get_provider_file_stats(current_user.id, provider)

    if db_file_count == 0:
        from backend.app.schemas.file import FileRecord
        now = datetime.now(timezone.utc)

        sample_files_map = {
            "google_drive": [
                {"name": "2026_Project_Architecture_Specification.pdf", "path": "/Docs/2026_Project_Architecture_Specification.pdf", "mime": "application/pdf", "ext": ".pdf", "size": 3481200},
                {"name": "Financial_Budget_Projection_Q3.xlsx", "path": "/Finance/Financial_Budget_Projection_Q3.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ext": ".xlsx", "size": 1824000},
                {"name": "Executive_Summary_AI_Platform.docx", "path": "/Docs/Executive_Summary_AI_Platform.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "ext": ".docx", "size": 945200},
                {"name": "System_Design_Diagram_HD.png", "path": "/Design/System_Design_Diagram_HD.png", "mime": "image/png", "ext": ".png", "size": 2410800},
                {"name": "Meeting_Notes_Quarterly_Strategy.md", "path": "/Notes/Meeting_Notes_Quarterly_Strategy.md", "mime": "text/markdown", "ext": ".md", "size": 42100},
            ],
            "onedrive": [
                {"name": "Enterprise_Cloud_Migration_Plan.docx", "path": "/Strategy/Enterprise_Cloud_Migration_Plan.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "ext": ".docx", "size": 1540000},
                {"name": "Operational_Cost_Analysis_2026.xlsx", "path": "/Finance/Operational_Cost_Analysis_2026.xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ext": ".xlsx", "size": 2210000},
                {"name": "Security_Compliance_Review.pdf", "path": "/Audit/Security_Compliance_Review.pdf", "mime": "application/pdf", "ext": ".pdf", "size": 4120000},
                {"name": "OneDrive_Team_Shared_Assets.zip", "path": "/Archives/OneDrive_Team_Shared_Assets.zip", "mime": "application/zip", "ext": ".zip", "size": 12800000},
            ],
            "dropbox": [
                {"name": "Dropbox_Backup_Dataset_2026.json", "path": "/Data/Dropbox_Backup_Dataset_2026.json", "mime": "application/json", "ext": ".json", "size": 892000},
                {"name": "Marketing_Campaign_Creative_Brief.pdf", "path": "/Marketing/Marketing_Campaign_Creative_Brief.pdf", "mime": "application/pdf", "ext": ".pdf", "size": 2740000},
                {"name": "User_Research_Interview_Notes.docx", "path": "/Research/User_Research_Interview_Notes.docx", "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "ext": ".docx", "size": 650000},
            ],
        }

        samples = sample_files_map.get(provider, [])
        for i, s in enumerate(samples):
            rec = FileRecord(
                id=f"{provider}_sandbox_{i+1}",
                provider=provider,
                provider_file_id=f"sandbox_{i+1}",
                name=s["name"],
                path=s["path"],
                mime_type=s["mime"],
                extension=s["ext"],
                size=s["size"],
                created_at=now,
                modified_at=now,
                web_url=f"https://{clean_p}.com/sample/{s['name']}",
                downloadable=True,
                is_folder=False,
                content_available=True,
                content_hash=f"hash_{provider}_{i+1}",
                metadata={"sandbox": True},
            )
            await file_repo.sync_record(current_user.id, rec)

    # Invalidate cache
    _provider_cache.pop(f"{current_user.id}:{provider}", None)

    # Calculate stats
    db_file_count, db_used_bytes = await file_repo.get_provider_file_stats(current_user.id, provider)
    limits = {"google_drive": 16106127360, "onedrive": 5368709120, "dropbox": 2147483648}
    limit = limits.get(provider, 10737418240)
    percent = round((db_used_bytes / limit) * 100, 1) if limit > 0 else 0.0

    def _fmt(b: int) -> str:
        curr = float(b)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if curr < 1024.0:
                return f"{curr:.1f} {unit}" if unit in ['GB', 'TB'] else f"{int(curr)} {unit}"
            curr /= 1024.0
        return f"{curr:.1f} PB"

    return ProviderStatusResponse(
        provider=provider,
        name=valid_providers[provider],
        connected=True,
        account_identifier=account_email,
        connected_at=datetime.now(timezone.utc),
        status="connected",
        file_count=db_file_count,
        used_storage=_fmt(db_used_bytes),
        total_storage=_fmt(limit),
        used_percent=percent,
    )



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
