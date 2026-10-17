"""End-to-end verification of MCP tools with Local AI Search."""

import asyncio
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp_server.tools.search_files import search_files_tool
from mcp_server.server import index_status


async def main():
    print("=" * 65)
    print("Testing MCP Tools with Local AI Hybrid Search Engine")
    print("=" * 65)

    # 1. Test index_status tool
    print("\n[TEST 1] Calling MCP tool: index_status")
    status_res = await index_status()
    print("  Index Status Response:")
    print(f"    - Indexing Status: {status_res['status']['status']}")
    print(f"    - Total Files in DB: {status_res['stats']['total_files']}")
    print(f"    - LanceDB Text Vectors: {status_res['stats']['text_vectors']}")
    print(f"    - LanceDB Image Vectors: {status_res['stats']['image_vectors']}")
    print(f"    - Sources Breakdown: {status_res['stats']['by_source']}")

    # 2. Test search_files tool: "give me my latest resume"
    print("\n[TEST 2] Calling MCP tool: search_files (query='give me my latest resume', sort='modified_desc')")
    resume_results = await search_files_tool(
        query="give me my latest resume",
        sort="modified_desc",
        file_types=["pdf", "docx"],
        limit=5,
    )
    print(f"  Retrieved {len(resume_results)} results:")
    for r in resume_results:
        print(f"    - {r.get('name')} | modified: {r.get('modified')} | score: {r.get('score')}")
    assert any("resume_latest_2026" in r.get("name", "") for r in resume_results), "Latest resume not found!"

    # 3. Test search_files tool: "leaf png" (Visual multimodal search)
    print("\n[TEST 3] Calling MCP tool: search_files (query='leaf png', file_types=['png', 'jpg'])")
    image_results = await search_files_tool(
        query="leaf png",
        file_types=["png", "jpg"],
        limit=5,
    )
    print(f"  Retrieved {len(image_results)} results:")
    for r in image_results:
        print(f"    - {r.get('name')} | mime: {r.get('mime')} | score: {r.get('score')}")
    assert any("leaf" in r.get("name", "").lower() for r in image_results), "Leaf image not found!"

    print("\n[SUCCESS] All MCP search and indexing tools verified end-to-end!")


if __name__ == "__main__":
    asyncio.run(main())
