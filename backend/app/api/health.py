"""Health check API Route."""

from fastapi import APIRouter
from backend.app.core.config import get_settings
from backend.app.mcp.client import mcp_client

settings = get_settings()
router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    # Verify MCP server tool responsiveness
    mcp_status = "connected"
    tool_count = 0
    try:
        tools = await mcp_client.list_tools()
        tool_count = len(tools)
    except Exception:
        mcp_status = "offline"

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "mcp_server": {
            "status": mcp_status,
            "url": settings.MCP_SERVER_URL,
            "tools_available": tool_count,
        },
    }
