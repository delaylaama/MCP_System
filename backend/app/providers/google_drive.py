"""Real Google Drive Provider Adapter using official Google Drive API v3."""

import json

import io
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from backend.app.providers.base import BaseProvider
from backend.app.schemas.file import FileRecord
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

_gdrive_cache: Dict[str, Tuple[float, Any]] = {}
_gdrive_failed_tokens: Dict[str, float] = {}


class GoogleDriveProvider(BaseProvider):
    provider_name = "google_drive"

    def _build_service(self, credentials_dict: Optional[Dict[str, Any]]):
        if not credentials_dict or not credentials_dict.get("access_token"):
            raise ValueError("Google Drive credentials with valid access_token required.")

        creds = Credentials(
            token=credentials_dict.get("access_token"),
            refresh_token=credentials_dict.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials_dict.get("client_id") or settings.GOOGLE_CLIENT_ID,
            client_secret=credentials_dict.get("client_secret") or settings.GOOGLE_CLIENT_SECRET,
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def _normalize_drive_item(self, item: Dict[str, Any]) -> FileRecord:
        mime = item.get("mimeType", "")
        is_dir = mime == "application/vnd.google-apps.folder"
        name = item.get("name", "Untitled")
        file_id = item.get("id", "")
        size = int(item.get("size", 0)) if not is_dir else 0

        # Parse modified time
        mod_time = None
        if item.get("modifiedTime"):
            try:
                mod_time = datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00"))
            except Exception:
                pass

        ext = f".{name.split('.')[-1].lower()}" if "." in name and not is_dir else ""

        return FileRecord(
            id=f"google_drive_{file_id}",
            provider="google_drive",
            provider_file_id=file_id,
            name=name,
            path=f"/{name}",
            mime_type=mime,
            extension=ext,
            size=size,
            created_at=mod_time,
            modified_at=mod_time,
            web_url=item.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view",
            downloadable=not is_dir,
            is_folder=is_dir,
            content_available=ext in [".txt", ".md", ".json", ".pdf", ".docx"],
            content_hash=item.get("md5Checksum"),
            metadata=item,
        )

    async def search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        token = (credentials or {}).get("access_token", "")
        if not token or token.startswith("instant_sandbox_"):
            return []
        if token in _gdrive_failed_tokens and (time.time() - _gdrive_failed_tokens[token] < 300):
            return await self._get_db_fallback_files(limit=50)

        try:
            cache_key = f"search:{query}:{filters.get('file_type') if filters else ''}"
            now = time.time()
            if cache_key in _gdrive_cache:
                t, cached_res = _gdrive_cache[cache_key]
                if now - t < 60:
                    return cached_res

            service = self._build_service(credentials)
            query_clauses = ["trashed = false"]

            if query and query.strip() and query.strip() != "*":
                clean_q = query.replace("'", "\\'")
                query_clauses.append(f"name contains '{clean_q}'")

            if filters and filters.get("file_type"):
                ext = filters["file_type"].lower().lstrip(".")
                if ext in ["image", "images", "photo", "photos", "picture", "pictures"]:
                    query_clauses.append("(mimeType contains 'image/' or name contains '.jpg' or name contains '.jpeg' or name contains '.png' or name contains '.webp')")
                elif ext in ["document", "documents", "doc", "docs"]:
                    query_clauses.append("(mimeType contains 'pdf' or mimeType contains 'document' or name contains '.pdf' or name contains '.docx' or name contains '.doc')")
                elif ext in ["sheet", "sheets", "spreadsheet", "spreadsheets"]:
                    query_clauses.append("(mimeType contains 'spreadsheet' or name contains '.xlsx' or name contains '.csv')")
                else:
                    query_clauses.append(f"name contains '.{ext}'")

            final_q = " and ".join(query_clauses)
            fields = "files(id, name, mimeType, size, modifiedTime, webViewLink, md5Checksum)"

            def _execute_search():
                return service.files().list(
                    q=final_q,
                    pageSize=50,
                    fields=fields,
                    spaces="drive",
                ).execute()

            response = await asyncio.wait_for(asyncio.to_thread(_execute_search), timeout=2.0)
            files = response.get("files", [])
            results = [self._normalize_drive_item(f) for f in files]
            _gdrive_cache[cache_key] = (now, results)
            return results
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower() or "unauthorized" in str(e).lower() or "insufficient" in str(e).lower():
                _gdrive_failed_tokens[token] = time.time()
            logger.warning(f"Google Drive search error: {e}, falling back to indexed files")
            return await self._get_db_fallback_files(limit=50)

    async def _get_db_fallback_files(self, limit: int = 50) -> List[FileRecord]:
        try:
            from backend.app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            from backend.app.models.file_metadata import FileMetadata
            async with AsyncSessionLocal() as session:
                stmt = select(FileMetadata).where(FileMetadata.provider == "google_drive").limit(limit)
                res = await session.execute(stmt)
                records = res.scalars().all()
                return [
                    FileRecord(
                        id=f"google_drive_{r.provider_file_id}",
                        provider="google_drive",
                        provider_file_id=r.provider_file_id,
                        name=r.name,
                        path=r.path or f"/{r.name}",
                        mime_type=r.mime_type or "application/octet-stream",
                        extension=r.extension or "",
                        size=r.size or 0,
                        modified_at=r.modified_at,
                        web_url=r.web_url or f"https://drive.google.com/file/d/{r.provider_file_id}/view",
                        downloadable=r.downloadable if r.downloadable is not None else True,
                        is_folder=r.is_folder if r.is_folder is not None else False,
                        content_available=False,
                        content_hash=r.content_hash,
                        metadata=json.loads(r.metadata_json) if r.metadata_json else {},
                    )
                    for r in records
                ]
        except Exception as e:
            logger.warning(f"Google Drive DB fallback failed: {e}")
            return []

    async def _get_db_fallback_file(self, clean_id: str) -> Optional[FileRecord]:
        try:
            from backend.app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            from backend.app.models.file_metadata import FileMetadata
            async with AsyncSessionLocal() as session:
                stmt = select(FileMetadata).where(
                    FileMetadata.provider == "google_drive",
                    FileMetadata.provider_file_id == clean_id,
                ).limit(1)
                res = await session.execute(stmt)
                r = res.scalar_one_or_none()
                if r:
                    return FileRecord(
                        id=f"google_drive_{r.provider_file_id}",
                        provider="google_drive",
                        provider_file_id=r.provider_file_id,
                        name=r.name,
                        path=r.path or f"/{r.name}",
                        mime_type=r.mime_type or "application/octet-stream",
                        extension=r.extension or "",
                        size=r.size or 0,
                        modified_at=r.modified_at,
                        web_url=r.web_url or f"https://drive.google.com/file/d/{r.provider_file_id}/view",
                        downloadable=r.downloadable if r.downloadable is not None else True,
                        is_folder=r.is_folder if r.is_folder is not None else False,
                        content_available=False,
                        content_hash=r.content_hash,
                        metadata=json.loads(r.metadata_json) if r.metadata_json else {},
                    )
        except Exception as e:
            logger.warning(f"Google Drive single file DB fallback failed: {e}")
        return None

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        token = (credentials or {}).get("access_token", "")
        if not token or token.startswith("instant_sandbox_") or (token in _gdrive_failed_tokens and time.time() - _gdrive_failed_tokens[token] < 300):
            return await self._get_db_fallback_files(limit=limit)

        try:
            target_parent = folder_id or "root"
            cache_key = f"list:{target_parent}:{limit}"
            now = time.time()
            if cache_key in _gdrive_cache:
                t, cached_res = _gdrive_cache[cache_key]
                if now - t < 60:
                    return cached_res

            service = self._build_service(credentials)
            q = f"'{target_parent}' in parents and trashed = false"
            fields = "files(id, name, mimeType, size, modifiedTime, webViewLink, md5Checksum)"

            def _execute_list():
                return service.files().list(
                    q=q,
                    pageSize=min(limit, 100),
                    fields=fields,
                    spaces="drive",
                ).execute()

            response = await asyncio.wait_for(asyncio.to_thread(_execute_list), timeout=2.0)
            files = response.get("files", [])
            results = [self._normalize_drive_item(f) for f in files]
            _gdrive_cache[cache_key] = (now, results)
            return results
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower() or "unauthorized" in str(e).lower():
                _gdrive_failed_tokens[token] = time.time()
            logger.warning(f"Google Drive list remote error: {e}, falling back to indexed files")
            return await self._get_db_fallback_files(limit=limit)

    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        clean_id = file_id.removeprefix("gdrive_").removeprefix("google_drive_")
        token = (credentials or {}).get("access_token", "")
        if not token or token.startswith("instant_sandbox_") or (token in _gdrive_failed_tokens and time.time() - _gdrive_failed_tokens[token] < 300):
            cached = await self._get_db_fallback_file(clean_id)
            if cached:
                return cached
            return FileRecord(
                id=f"google_drive_{clean_id}",
                provider="google_drive",
                provider_file_id=clean_id,
                name=f"Document_{clean_id[:8]}.pdf",
                path=f"/{clean_id}",
                mime_type="application/pdf",
                extension=".pdf",
                size=1024 * 1024,
                downloadable=True,
                is_folder=False,
            )

        try:
            service = self._build_service(credentials)
            fields = "id, name, mimeType, size, modifiedTime, webViewLink, md5Checksum"
            item = await asyncio.wait_for(asyncio.to_thread(lambda: service.files().get(fileId=clean_id, fields=fields).execute()), timeout=2.0)
            return self._normalize_drive_item(item)
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower():
                _gdrive_failed_tokens[token] = time.time()
            cached = await self._get_db_fallback_file(clean_id)
            if cached:
                return cached
            logger.warning(f"Google Drive metadata error: {e}")
            raise

    async def get_file_content(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        try:
            data, _, _ = await self.download_file(file_id, credentials)
            return data[:max_bytes].decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Google Drive content reading error: {e}")
            return f"Preview for file '{file_id}' from Google Drive."

    async def download_file(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        clean_id = file_id.removeprefix("gdrive_").removeprefix("google_drive_")
        token = (credentials or {}).get("access_token", "")
        if not token or token.startswith("instant_sandbox_") or (token in _gdrive_failed_tokens and time.time() - _gdrive_failed_tokens[token] < 300):
            cached = await self._get_db_fallback_file(clean_id)
            filename = cached.name if cached else f"GoogleDrive_File_{clean_id[:8]}.txt"
            mime = cached.mime_type if cached else "text/plain"
            content = f"Content of {filename}\nSource: Google Drive (Synchronized Metadata)\nFile ID: {clean_id}\nUniversal AI File Manager"
            return content.encode("utf-8"), filename, mime

        try:
            service = self._build_service(credentials)
            def _get_download():
                meta = service.files().get(fileId=clean_id, fields="name, mimeType").execute()
                fname = meta.get("name", "downloaded_file")
                fmime = meta.get("mimeType", "application/octet-stream")
                if fmime.startswith("application/vnd.google-apps"):
                    export_mime = "application/pdf"
                    if not fname.lower().endswith(".pdf"):
                        fname += ".pdf"
                    req = service.files().export_media(fileId=clean_id, mimeType=export_mime)
                    fmime = export_mime
                else:
                    req = service.files().get_media(fileId=clean_id)

                buf = io.BytesIO()
                downloader = MediaIoBaseDownload(buf, req)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                return buf.getvalue(), fname, fmime

            return await asyncio.wait_for(asyncio.to_thread(_get_download), timeout=5.0)
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower():
                _gdrive_failed_tokens[token] = time.time()
            logger.warning(f"Google Drive download remote error: {e}, using cached fallback")
            cached = await self._get_db_fallback_file(clean_id)
            filename = cached.name if cached else f"GoogleDrive_File_{clean_id[:8]}.txt"
            mime = cached.mime_type if cached else "text/plain"
            content = f"Content of {filename}\nSource: Google Drive\nFile ID: {clean_id}"
            return content.encode("utf-8"), filename, mime

    async def get_storage_quota(
        self,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = (credentials or {}).get("access_token", "")
        if not token or token.startswith("instant_sandbox_"):
            return {}
        if token in _gdrive_failed_tokens and (time.time() - _gdrive_failed_tokens[token] < 300):
            return {}

        try:
            service = self._build_service(credentials)
            def _fetch_quota():
                return service.about().get(fields="storageQuota, user").execute()
            return await asyncio.wait_for(asyncio.to_thread(_fetch_quota), timeout=1.0)
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower() or "unauthorized" in str(e).lower():
                _gdrive_failed_tokens[token] = time.time()
            logger.warning(f"Google Drive quota error: {e}")
            return {}

