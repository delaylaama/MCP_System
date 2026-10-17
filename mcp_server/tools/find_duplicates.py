"""MCP Tool: find_duplicates."""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from mcp_server.services.provider_manager import provider_manager


async def find_duplicates_tool(
    provider: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Identifies duplicate files across connected storage providers by matching SHA-256 cryptographic hashes.

    Args:
        provider: Optional provider filter, or leave empty to compare across ALL connected cloud & local providers.
        user_id: Optional user identifier.
    """
    target_providers = [provider] if provider and provider != "all" else None
    all_files = await provider_manager.search_all(
        query="",
        target_providers=target_providers,
    )

    hash_groups = defaultdict(list)
    for record in all_files:
        if not record.is_folder and record.content_hash:
            hash_groups[record.content_hash].append(record)

    duplicates = []
    for content_hash, files in hash_groups.items():
        if len(files) > 1:
            duplicates.append({
                "content_hash": content_hash,
                "size": files[0].size,
                "count": len(files),
                "files": [f.model_dump(mode="json") for f in files],
            })

    return duplicates
