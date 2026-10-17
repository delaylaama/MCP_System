"""MCP Tool: get_file_metadata."""

from typing import Dict, Any, Optional
from mcp_server.services.provider_manager import provider_manager


async def get_file_metadata_tool(
    file_id: str,
    provider: str = "local",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve normalized metadata for a specific file by its provider ID.

    Args:
        file_id: Provider-native or normalized file identifier.
        provider: Provider name ('local', 'google_drive', 'onedrive', 'dropbox').
        user_id: Optional user identifier.
    """
    record = await provider_manager.get_file_metadata(
        provider_name=provider,
        file_id=file_id,
    )
    return record.model_dump(mode="json")
