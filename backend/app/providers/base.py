"""Abstract Base Provider for cloud storage and local filesystem adapters."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from backend.app.schemas.file import FileRecord


class BaseProvider(ABC):
    """
    Standard interface that all storage providers must implement.
    MCP tools and the backend search orchestrator interact exclusively via this contract.
    """

    provider_name: str

    @abstractmethod
    async def search_files(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        """Search files within this provider matching the query string and optional filters."""
        pass

    @abstractmethod
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> List[FileRecord]:
        """List files and folders within a given folder or the root directory."""
        pass

    @abstractmethod
    async def get_file_metadata(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        """Fetch metadata for a single file by its provider ID."""
        pass

    @abstractmethod
    async def get_file_content(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        max_bytes: int = 1048576,
    ) -> str:
        """Extract text representation of the file content (up to max_bytes)."""
        pass

    @abstractmethod
    async def download_file(
        self,
        file_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, str, str]:
        """Download binary content. Returns (file_bytes, filename, mime_type)."""
        pass
