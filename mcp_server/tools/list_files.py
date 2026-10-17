"""MCP Tool: list_files."""

from typing import List, Optional, Dict, Any
from mcp_server.services.provider_manager import provider_manager


async def list_files_tool(
    provider: str = "local",
    folder_id: Optional[str] = None,
    limit: int = 50,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List files and folders within a specific folder or root directory for a given provider.

    Args:
        provider: Target provider ('local', 'google_drive', 'onedrive', 'dropbox').
        folder_id: Specific folder ID or relative directory path. Defaults to root folder.
        limit: Maximum number of items to return (1-100).
        user_id: Optional user identifier.
    """
    credentials = None
    if user_id and provider != "local":
        try:
            from backend.app.core.database import AsyncSessionLocal
            from backend.app.repositories.provider_repository import ProviderRepository
            async with AsyncSessionLocal() as session:
                repo = ProviderRepository(session)
                conn = await repo.get_by_user_and_provider(user_id, provider)
                if conn and conn.status == "connected":
                    credentials = repo.decrypt_credentials(conn)
        except Exception:
            pass

    records = await provider_manager.list_files(
        provider_name=provider,
        folder_id=folder_id,
        limit=limit,
        credentials=credentials,
    )
    return [r.model_dump(mode="json") for r in records]
