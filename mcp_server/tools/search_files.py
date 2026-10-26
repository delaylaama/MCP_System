"""MCP Tool: search_files integrating Local AI Hybrid Search."""

from typing import List, Optional, Dict, Any
from backend.search.search import search_files as local_ai_search
from mcp_server.services.provider_manager import provider_manager
from mcp_server.schemas.file import FileRecord


async def search_files_tool(
    query: str,
    file_types: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    sort: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
    provider: Optional[str] = None,
    file_type: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search files across connected sources using local AI hybrid search (FTS5 + MiniLM + CLIP).

    Args:
        query: Natural language query (e.g. "latest resume", "leaf png", "June invoice").
        file_types: File extensions (e.g. ["pdf", "docx"] for documents, ["png", "jpg"] for images).
        sources: Filter by sources (e.g. ["local", "google_drive", "onedrive", "dropbox"]).
        sort: "relevance" (default) or "modified_desc" for "latest/newest/recent" requests.
        date_from: Filter files modified on or after this ISO date.
        date_to: Filter files modified on or before this ISO date.
        limit: Max number of files to return (default 10).
    """
    # Normalize legacy arguments
    eff_sources = sources or ([provider] if provider and provider != "all" else None)
    eff_types = file_types or ([file_type] if file_type else None)

    # 1. Execute local hybrid AI search
    try:
        results = local_ai_search(
            query=query,
            file_types=eff_types,
            sources=eff_sources,
            sort=sort,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        if results:
            return results
    except Exception:
        pass

    # 2. Fallback to live provider crawl if index has no results yet
    filters: Dict[str, Any] = {}
    if eff_types:
        filters["file_type"] = eff_types[0]

    credentials_map: Dict[str, Dict[str, Any]] = {}
    if user_id:
        try:
            from backend.app.core.database import AsyncSessionLocal
            from backend.app.repositories.provider_repository import ProviderRepository
            async with AsyncSessionLocal() as session:
                repo = ProviderRepository(session)
                conns = await repo.list_by_user(user_id)
                for conn in conns:
                    if conn.status == "connected":
                        credentials_map[conn.provider] = repo.decrypt_credentials(conn)
        except Exception:
            pass

    records: List[FileRecord] = []
    try:
        import asyncio
        records = await asyncio.wait_for(
            provider_manager.search_all(
                query=query,
                target_providers=eff_sources,
                filters=filters,
                credentials_map=credentials_map,
            ),
            timeout=2.0,
        )
    except Exception:
        pass

    if not records and user_id:
        try:
            from backend.app.core.database import AsyncSessionLocal
            from backend.app.repositories.file_repository import FileRepository
            async with AsyncSessionLocal() as session:
                file_repo = FileRepository(session)
                records = await file_repo.search_user_files(
                    user_id=user_id,
                    query=query,
                    providers=eff_sources,
                    file_type=eff_types[0] if eff_types else None,
                    limit=limit,
                )
        except Exception:
            pass

    if sort in ("modified_desc", "latest", "recent"):
        records.sort(key=lambda r: str(r.modified_at or ""), reverse=True)

    return [r.model_dump(mode="json") for r in records[:limit]]
