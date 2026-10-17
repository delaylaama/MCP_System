"""
Model Context Protocol (MCP) Server Application.
Uses official MCP Python SDK v2 MCPServer with Streamable HTTP transport.
"""

import sys
import os
from pathlib import Path

# Ensure workspace root is in sys.path
root_path = Path(__file__).parent.parent.resolve()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import uvicorn
from mcp.server.mcpserver import MCPServer
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

from mcp_server.tools.search_files import search_files_tool
from mcp_server.tools.list_files import list_files_tool
from mcp_server.tools.get_file_metadata import get_file_metadata_tool
from mcp_server.tools.get_file_content import get_file_content_tool
from mcp_server.tools.download_file import download_file_tool
from mcp_server.tools.find_duplicates import find_duplicates_tool

settings = get_settings()

# Initialize MCPServer instance
mcp_server = MCPServer(
    name="universal-ai-file-manager",
    instructions="Universal AI File Manager MCP server providing cross-cloud search, listing, metadata, and retrieval tools across Google Drive, Microsoft OneDrive, Dropbox, and Local Storage.",
)

# Register MCP Tools
@mcp_server.tool(
    name="search_files",
    description="""Search files across local drives and connected cloud providers (Google Drive, OneDrive, Dropbox) using 100% local hybrid AI search (content text, metadata, and visual CLIP embeddings).

INSTRUCTIONS FOR THE LLM CALLING THIS TOOL:
- Set sort='modified_desc' whenever the user asks for 'latest', 'newest', 'recent', or recently modified files (e.g. 'give me my latest resume').
- Set file_types=['pdf', 'docx'] for resume, CV, invoice, contract, or document searches.
- Set file_types=['png', 'jpg', 'jpeg', 'webp'] for images, photos, drawings, screenshots, or visual queries (e.g. 'leaf png').
- Set sources=['dropbox'] (or ['google_drive'], ['onedrive'], ['local']) when the user names a specific source (e.g. 'in my Dropbox', 'on E drive').
- Query should contain descriptive keywords or visual concepts; search uses Reciprocal Rank Fusion of keyword FTS5 and neural embeddings.""",
)
async def search_files(
    query: str,
    file_types: list[str] | None = None,
    sources: list[str] | None = None,
    sort: str = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
    provider: str | None = None,
    file_type: str | None = None,
    user_id: str | None = None,
):
    return await search_files_tool(
        query=query,
        file_types=file_types,
        sources=sources,
        sort=sort,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        provider=provider,
        file_type=file_type,
        user_id=user_id,
    )


@mcp_server.tool(
    name="index_status",
    description="Retrieve the current status of the local AI search index, including file counts per source (Local, Google Drive, OneDrive, Dropbox), vector counts (text & visual), and whether background indexing is currently running.",
)
async def index_status():
    from backend.search.indexer import indexer
    from backend.search.db import db
    return {
        "status": indexer.get_status(),
        "stats": db.get_stats(),
    }


@mcp_server.tool(
    name="reindex",
    description="Trigger a full re-indexing pass of local directories and connected cloud drives into the local AI search engine.",
)
async def reindex(sources: list[str] | None = None):
    from backend.search.indexer import indexer
    indexer.run_full_index()
    return {
        "status": "indexing_started",
        "message": "Local AI indexer started background crawl across sources.",
    }


@mcp_server.tool(
    name="list_files",
    description="List files and subfolders within a directory or cloud folder.",
)
async def list_files(
    provider: str = "local",
    folder_id: str | None = None,
    limit: int = 50,
    user_id: str | None = None,
):
    return await list_files_tool(
        provider=provider,
        folder_id=folder_id,
        limit=limit,
        user_id=user_id,
    )


@mcp_server.tool(
    name="get_file_metadata",
    description="Retrieve standardized file metadata (size, dates, MIME type, URLs) for a specific file ID.",
)
async def get_file_metadata(
    file_id: str,
    provider: str = "local",
    user_id: str | None = None,
):
    return await get_file_metadata_tool(
        file_id=file_id,
        provider=provider,
        user_id=user_id,
    )


@mcp_server.tool(
    name="get_file_content",
    description="Extract textual content from a document (PDF, DOCX, TXT, Markdown, code) for analysis or summarization.",
)
async def get_file_content(
    file_id: str,
    provider: str = "local",
    max_bytes: int = 500000,
    user_id: str | None = None,
):
    return await get_file_content_tool(
        file_id=file_id,
        provider=provider,
        max_bytes=max_bytes,
        user_id=user_id,
    )


@mcp_server.tool(
    name="download_file",
    description="Download binary contents of a file encoded in Base64.",
)
async def download_file(
    file_id: str,
    provider: str = "local",
    user_id: str | None = None,
):
    return await download_file_tool(
        file_id=file_id,
        provider=provider,
        user_id=user_id,
    )


@mcp_server.tool(
    name="find_duplicates",
    description="Cross-compare files across all connected storage providers and detect duplicate groups based on SHA-256 hashes.",
)
async def find_duplicates(
    provider: str | None = None,
    user_id: str | None = None,
):
    return await find_duplicates_tool(
        provider=provider,
        user_id=user_id,
    )


# Streamable HTTP ASGI application
app = mcp_server.streamable_http_app()


def run():
    host = settings.MCP_SERVER_HOST
    port = settings.MCP_SERVER_PORT
    logger.info(f"Starting MCP Server on http://{host}:{port}/mcp (Streamable HTTP)")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run()
