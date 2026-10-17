"""Real Google Drive Provider Adapter using official Google Drive API v3."""

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
            id=f"gdrive_{file_id}",
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

            response = await asyncio.to_thread(_execute_search)
            files = response.get("files", [])
            results = [self._normalize_drive_item(f) for f in files]
            _gdrive_cache[cache_key] = (now, results)
            return results
        except Exception as e:
            logger.warning(f"Google Drive search error: {e}")
            return []

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
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

            response = await asyncio.to_thread(_execute_list)
            files = response.get("files", [])
            results = [self._normalize_drive_item(f) for f in files]
            _gdrive_cache[cache_key] = (now, results)
            return results
        except Exception as e:
            logger.error(f"Google Drive list error: {e}")
            raise

    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        try:
            service = self._build_service(credentials)
            clean_id = file_id.removeprefix("gdrive_")
            fields = "id, name, mimeType, size, modifiedTime, webViewLink, md5Checksum"
            item = await asyncio.to_thread(lambda: service.files().get(fileId=clean_id, fields=fields).execute())
            return self._normalize_drive_item(item)
        except Exception as e:
            logger.error(f"Google Drive metadata error: {e}")
            raise

    async def get_file_content(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        try:
            data, _, mime = await self.download_file(file_id, credentials)
            return data[:max_bytes].decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Google Drive content reading error: {e}")
            return ""

    async def download_file(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        try:
            service = self._build_service(credentials)
            clean_id = file_id.removeprefix("gdrive_")
            meta = service.files().get(fileId=clean_id, fields="name, mimeType").execute()
            filename = meta.get("name", "downloaded_file")
            mime = meta.get("mimeType", "application/octet-stream")

            if mime.startswith("application/vnd.google-apps"):
                export_mime = "application/pdf"
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"
                request = service.files().export_media(fileId=clean_id, mimeType=export_mime)
                mime = export_mime
            else:
                request = service.files().get_media(fileId=clean_id)

            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            return buffer.getvalue(), filename, mime
        except Exception as e:
            logger.error(f"Google Drive download error: {e}")
            raise

    async def get_storage_quota(
        self,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            service = self._build_service(credentials)
            return service.about().get(fields="storageQuota, user").execute()
        except Exception as e:
            logger.error(f"Google Drive quota error: {e}")
            return {}

