"""Real Microsoft OneDrive Provider Adapter using Microsoft Graph API v1.0."""

import httpx
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from backend.app.providers.base import BaseProvider
from backend.app.schemas.file import FileRecord
from backend.app.core.logging import logger

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class OneDriveProvider(BaseProvider):
    provider_name = "onedrive"

    def _get_headers(self, credentials_dict: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if not credentials_dict or not credentials_dict.get("access_token"):
            raise ValueError("Microsoft OneDrive credentials with valid access_token required.")
        token = credentials_dict["access_token"]
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _normalize_item(self, item: Dict[str, Any]) -> FileRecord:
        name = item.get("name", "Untitled")
        item_id = item.get("id", "")
        size = item.get("size", 0)
        is_dir = "folder" in item

        mime = None
        if "file" in item and "mimeType" in item["file"]:
            mime = item["file"]["mimeType"]
        elif is_dir:
            mime = "inode/directory"

        ext = f".{name.split('.')[-1].lower()}" if "." in name and not is_dir else ""

        mod_time = None
        if item.get("lastModifiedDateTime"):
            try:
                mod_time = datetime.fromisoformat(item["lastModifiedDateTime"].replace("Z", "+00:00"))
            except Exception:
                pass

        hashes = item.get("file", {}).get("hashes", {})
        content_hash = hashes.get("sha256Hash") or hashes.get("quickXorHash")

        return FileRecord(
            id=f"onedrive_{item_id}",
            provider="onedrive",
            provider_file_id=item_id,
            name=name,
            path=item.get("parentReference", {}).get("path", "") + f"/{name}",
            mime_type=mime or "application/octet-stream",
            extension=ext,
            size=size,
            created_at=mod_time,
            modified_at=mod_time,
            web_url=item.get("webUrl"),
            downloadable=not is_dir,
            is_folder=is_dir,
            content_available=ext in [".txt", ".md", ".json", ".pdf", ".docx"],
            content_hash=content_hash,
            metadata=item,
        )

    async def _refresh_token(self, credentials_dict: Optional[Dict[str, Any]]) -> Optional[str]:
        if not credentials_dict or not credentials_dict.get("refresh_token"):
            return None
        from backend.app.core.config import get_settings
        settings = get_settings()
        tenant = credentials_dict.get("tenant_id") or settings.MICROSOFT_TENANT_ID or "common"
        client_id = credentials_dict.get("client_id") or settings.MICROSOFT_CLIENT_ID
        client_secret = credentials_dict.get("client_secret") or settings.MICROSOFT_CLIENT_SECRET
        url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": credentials_dict["refresh_token"],
            "grant_type": "refresh_token",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, data=data)
                if res.status_code == 200:
                    payload = res.json()
                    new_token = payload.get("access_token")
                    if new_token:
                        credentials_dict["access_token"] = new_token
                        if payload.get("refresh_token"):
                            credentials_dict["refresh_token"] = payload["refresh_token"]
                        logger.info("Successfully refreshed Microsoft OneDrive access token")
                        return new_token
        except Exception as e:
            logger.warning(f"OneDrive token refresh error: {e}")
        return None

    async def search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        try:
            if not query or query.strip() == "*":
                return await self.list_files(credentials=credentials, limit=50)

            headers = self._get_headers(credentials)
            async with httpx.AsyncClient(timeout=20.0) as client:
                url = f"{GRAPH_BASE}/me/drive/root/search(q='{query}')"
                response = await client.get(url, headers=headers)
                if response.status_code == 401:
                    new_token = await self._refresh_token(credentials)
                    if new_token:
                        headers = self._get_headers(credentials)
                        response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    logger.warning(f"OneDrive search returned {response.status_code}, falling back to list_files")
                    return await self.list_files(credentials=credentials, limit=50)

                data = response.json()
                items = data.get("value", [])
                results = [self._normalize_item(i) for i in items]

                if filters and filters.get("file_type"):
                    ext = filters["file_type"].lower().lstrip(".")
                    results = [r for r in results if r.name.lower().endswith(f".{ext}")]

                return results
        except Exception as e:
            logger.warning(f"OneDrive search error: {e}")
            return []

    async def get_storage_quota(
        self,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            headers = self._get_headers(credentials)
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(f"{GRAPH_BASE}/me/drive", headers=headers)
                if resp.status_code == 401:
                    new_token = await self._refresh_token(credentials)
                    if new_token:
                        headers = self._get_headers(credentials)
                        resp = await client.get(f"{GRAPH_BASE}/me/drive", headers=headers)
                if resp.status_code == 200:
                    return resp.json().get("quota", {})
            return {}
        except Exception as e:
            logger.warning(f"OneDrive quota error: {e}")
            return {}

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        try:
            headers = self._get_headers(credentials)
            is_root = not folder_id or folder_id in ("root", "default", "/")
            endpoint = f"{GRAPH_BASE}/me/drive/root/children" if is_root else f"{GRAPH_BASE}/me/drive/items/{folder_id}/children"
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{endpoint}?$top={min(limit, 100)}", headers=headers)
                if response.status_code == 401:
                    new_token = await self._refresh_token(credentials)
                    if new_token:
                        headers = self._get_headers(credentials)
                        response = await client.get(f"{endpoint}?$top={min(limit, 100)}", headers=headers)

                if response.status_code != 200:
                    logger.warning(f"OneDrive list returned {response.status_code}: {response.text}")
                    return []
                items = response.json().get("value", [])
                return [self._normalize_item(i) for i in items]
        except Exception as e:
            logger.warning(f"OneDrive list error: {e}")
            return []

    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        try:
            headers = self._get_headers(credentials)
            clean_id = file_id.removeprefix("onedrive_")
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(f"{GRAPH_BASE}/me/drive/items/{clean_id}", headers=headers)
                if response.status_code != 200:
                    raise FileNotFoundError(f"OneDrive item {clean_id} not found: {response.text}")
                return self._normalize_item(response.json())
        except Exception as e:
            logger.error(f"OneDrive metadata error: {e}")
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
        headers = self._get_headers(credentials)
        clean_id = file_id.removeprefix("onedrive_")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            meta_res = await client.get(f"{GRAPH_BASE}/me/drive/items/{clean_id}", headers=headers)
            filename = meta_res.json().get("name", "downloaded_file")
            mime = meta_res.json().get("file", {}).get("mimeType", "application/octet-stream")

            content_res = await client.get(f"{GRAPH_BASE}/me/drive/items/{clean_id}/content", headers=headers)
            if content_res.status_code != 200:
                raise RuntimeError(f"OneDrive download failed with status {content_res.status_code}")
            return content_res.content, filename, mime
