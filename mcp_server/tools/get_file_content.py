"""MCP Tool: get_file_content."""

from typing import Optional
from mcp_server.services.provider_manager import provider_manager


async def get_file_content_tool(
    file_id: str,
    provider: str = "local",
    max_bytes: int = 500000,
    user_id: Optional[str] = None,
) -> str:
    """
    Extract readable text content from a document (PDF, DOCX, TXT, Markdown, code, JSON) for analysis or summarization.

    Args:
        file_id: Provider file identifier.
        provider: Provider name ('local', 'google_drive', 'onedrive', 'dropbox').
        max_bytes: Maximum number of characters/bytes to return (default 500,000).
        user_id: Optional user identifier.
    """
    return await provider_manager.get_file_content(
        provider_name=provider,
        file_id=file_id,
        max_bytes=max_bytes,
    )
