"""MCP Tool: download_file."""

import base64
from typing import Dict, Any, Optional
from mcp_server.services.provider_manager import provider_manager


async def download_file_tool(
    file_id: str,
    provider: str = "local",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve binary file contents encoded in Base64 along with filename and MIME type.

    Args:
        file_id: Provider file identifier.
        provider: Provider name ('local', 'google_drive', 'onedrive', 'dropbox').
        user_id: Optional user identifier.
    """
    data, filename, mime_type = await provider_manager.download_file(
        provider_name=provider,
        file_id=file_id,
    )
    return {
        "filename": filename,
        "mime_type": mime_type,
        "size_bytes": len(data),
        "data_base64": base64.b64encode(data).decode("utf-8"),
    }
