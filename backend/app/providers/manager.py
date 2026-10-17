"""Provider Manager coordinating all storage adapters."""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from backend.app.providers.base import BaseProvider
from backend.app.providers.local import LocalFileProvider
from backend.app.providers.google_drive import GoogleDriveProvider
from backend.app.providers.onedrive import OneDriveProvider
from backend.app.providers.dropbox import DropboxProvider
from backend.app.schemas.file import FileRecord
from backend.app.core.logging import logger


class ProviderManager:
    """Coordinates search, listing, and file retrieval across registered storage providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {
            "local": LocalFileProvider(),
            "google_drive": GoogleDriveProvider(),
            "onedrive": OneDriveProvider(),
            "dropbox": DropboxProvider(),
        }

    @staticmethod
    def _normalize_name(name: str) -> str:
        clean = (name or "").strip().lower()
        if clean in ("local", "local_storage", "local storage", "local files", "system", "drives"):
            return "local"
        if clean in ("google_drive", "google drive", "gdrive", "google"):
            return "google_drive"
        if clean in ("onedrive", "one_drive", "microsoft onedrive", "microsoft"):
            return "onedrive"
        if clean in ("dropbox", "drop box"):
            return "dropbox"
        return clean

    def get_provider(self, name: str) -> BaseProvider:
        key = self._normalize_name(name)
        if key not in self._providers:
            raise ValueError(f"Unknown provider '{name}'. Supported: {list(self._providers.keys())}")
        return self._providers[key]

    def list_supported_providers(self) -> List[str]:
        return list(self._providers.keys())

    async def search_all(
        self,
        query: str,
        target_providers: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        credentials_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[FileRecord]:
        """Executes concurrent file search across selected or all active providers."""
        credentials_map = credentials_map or {}
        if target_providers:
            providers_to_query = [self._normalize_name(p) for p in target_providers]
        else:
            providers_to_query = list(self._providers.keys())

        tasks = []
        queried_names = []

        for name in providers_to_query:
            if name in self._providers:
                # If cloud provider, only query if credentials exist
                if name != "local" and name not in credentials_map:
                    continue
                provider = self._providers[name]
                creds = credentials_map.get(name)
                tasks.append(provider.search_files(query=query, filters=filters, credentials=creds))
                queried_names.append(name)

        if not tasks:
            # Fallback to local if nothing else configured
            provider = self._providers["local"]
            return await provider.search_files(query=query, filters=filters)

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        aggregated: List[FileRecord] = []

        for p_name, res in zip(queried_names, results_lists):
            if isinstance(res, Exception):
                logger.error(f"Search failed on provider '{p_name}': {res}")
            elif isinstance(res, list):
                aggregated.extend(res)

        return aggregated

    async def list_files(
        self,
        provider_name: str,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        provider = self.get_provider(provider_name)
        return await provider.list_files(folder_id=folder_id, limit=limit, credentials=credentials)

    async def get_file_metadata(
        self,
        provider_name: str,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        provider = self.get_provider(provider_name)
        return await provider.get_file_metadata(file_id=file_id, credentials=credentials)

    async def get_file_content(
        self,
        provider_name: str,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        provider = self.get_provider(provider_name)
        return await provider.get_file_content(file_id=file_id, credentials=credentials, max_bytes=max_bytes)

    async def download_file(
        self,
        provider_name: str,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        provider = self.get_provider(provider_name)
        return await provider.download_file(file_id=file_id, credentials=credentials)


provider_manager = ProviderManager()
