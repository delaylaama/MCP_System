"""Tests for MCP server tools, schema serialization, and tool dispatch."""

import pytest
from mcp_server.tools.search_files import search_files_tool
from mcp_server.tools.list_files import list_files_tool
from mcp_server.tools.get_file_metadata import get_file_metadata_tool
from mcp_server.tools.find_duplicates import find_duplicates_tool


@pytest.mark.asyncio
async def test_mcp_search_files_tool():
    results = await search_files_tool(query="invoice")
    assert isinstance(results, list)
    for r in results:
        assert "name" in r
        assert "provider" in r
        assert "downloadable" in r


@pytest.mark.asyncio
async def test_mcp_list_files_tool():
    results = await list_files_tool(provider="local", limit=10)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_mcp_find_duplicates_tool():
    duplicates = await find_duplicates_tool(provider="local")
    assert isinstance(duplicates, list)
