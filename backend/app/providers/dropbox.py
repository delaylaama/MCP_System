"""Real Dropbox Provider Adapter using official Dropbox API v2."""

import dropbox
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from backend.app.providers.base import BaseProvider
from backend.app.schemas.file import FileRecord
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()


class DropboxProvider(BaseProvider):
    provider_name = "dropbox"

    def _get_client(self, credentials_dict: Optional[Dict[str, Any]]) -> dropbox.Dropbox:
        if not credentials_dict or not credentials_dict.get("access_token"):
            raise ValueError("Dropbox credentials with valid access_token required.")

        return dropbox.Dropbox(
            oauth2_access_token=credentials_dict.get("access_token"),
            oauth2_refresh_token=credentials_dict.get("refresh_token"),
            app_key=credentials_dict.get("app_key") or settings.DROPBOX_APP_KEY,
            app_secret=credentials_dict.get("app_secret") or settings.DROPBOX_APP_SECRET,
        )

    def _normalize_metadata(self, meta: Any) -> FileRecord:
        is_dir = isinstance(meta, dropbox.files.FolderMetadata)
        is_file = isinstance(meta, dropbox.files.FileMetadata)
        name = meta.name
        path = meta.path_display or meta.path_lower or f"/{name}"
        raw_id = getattr(meta, "id", path)
        clean_id = raw_id.removeprefix("id:")
        size = getattr(meta, "size", 0) if is_file else 0

        mod_time = getattr(meta, "server_modified", None)
        if mod_time and mod_time.tzinfo is None:
            mod_time = mod_time.replace(tzinfo=timezone.utc)

        ext = f".{name.split('.')[-1].lower()}" if "." in name and not is_dir else ""
        content_hash = getattr(meta, "content_hash", None)

        return FileRecord(
            id=f"dropbox_{clean_id}",
            provider="dropbox",
            provider_file_id=clean_id,
            name=name,
            path=path,
            mime_type="inode/directory" if is_dir else "application/octet-stream",
            extension=ext,
            size=size,
            created_at=mod_time,
            modified_at=mod_time,
            web_url=f"https://www.dropbox.com/home{path}",
            downloadable=is_file,
            is_folder=is_dir,
            content_available=ext in [".txt", ".md", ".json", ".pdf", ".docx"],
            content_hash=content_hash,
            metadata={"id": clean_id, "path": path},
        )

    async def search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        try:
            if not query or query.strip() == "*":
                return await self.list_files(limit=50, credentials=credentials)

            dbx = self._get_client(credentials)
            res = dbx.files_search_v2(query=query)
            results = []
            seen_ids = set()
            for match in res.matches:
                metadata = match.metadata.get_metadata()
                rec = self._normalize_metadata(metadata)
                if rec.id not in seen_ids:
                    seen_ids.add(rec.id)
                    results.append(rec)

            if filters and filters.get("file_type"):
                ext = filters["file_type"].lower().lstrip(".")
                image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
                if ext in ["image", "images", "photo", "photos", "picture", "pictures"]:
                    results = [r for r in results if any(r.name.lower().endswith(e) for e in image_exts)]
                elif ext in ["document", "documents", "doc", "docs"]:
                    doc_exts = {".pdf", ".docx", ".doc", ".txt", ".md"}
                    results = [r for r in results if any(r.name.lower().endswith(e) for e in doc_exts)]
                else:
                    results = [r for r in results if r.name.lower().endswith(f".{ext}")]

            return results
        except Exception as e:
            logger.error(f"Dropbox search error: {e}")
            raise

    async def get_storage_quota(
        self,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            dbx = self._get_client(credentials)
            usage = dbx.users_get_space_usage()
            used = usage.used
            total = 2 * 1024 * 1024 * 1024  # default 2 GB free tier
            if usage.allocation.is_individual():
                total = usage.allocation.get_individual().allocated
            elif usage.allocation.is_team():
                total = usage.allocation.get_team().allocated
            return {"used": used, "total": total}
        except Exception as e:
            logger.error(f"Dropbox quota error: {e}")
            return {"used": 0, "total": 2 * 1024 * 1024 * 1024}

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        try:
            dbx = self._get_client(credentials)
            path = folder_id if folder_id and folder_id != "root" else ""
            res = dbx.files_list_folder(path=path, limit=min(limit, 100))
            seen_ids = set()
            results = []
            for entry in res.entries:
                rec = self._normalize_metadata(entry)
                if rec.id not in seen_ids:
                    seen_ids.add(rec.id)
                    results.append(rec)
            return results
        except Exception as e:
            logger.error(f"Dropbox list error: {e}")
            raise

    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        try:
            dbx = self._get_client(credentials)
            clean_id = file_id.removeprefix("dropbox_")
            target = f"id:{clean_id}" if not clean_id.startswith("/") and not clean_id.startswith("id:") else clean_id
            meta = dbx.files_get_metadata(path=target)
            return self._normalize_metadata(meta)
        except Exception as e:
            logger.error(f"Dropbox metadata error: {e}")
            raise

    async def get_file_content(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        data, _, _ = await self.download_file(file_id, credentials)
        return data[:max_bytes].decode("utf-8", errors="replace")

    async def download_file(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        try:
            dbx = self._get_client(credentials)
            clean_id = file_id.removeprefix("dropbox_")
            target = f"id:{clean_id}" if not clean_id.startswith("/") and not clean_id.startswith("id:") else clean_id
            meta, response = dbx.files_download(path=target)
            return response.content, meta.name, "application/octet-stream"
        except Exception as e:
            logger.error(f"Dropbox download error: {e}")
            raise
