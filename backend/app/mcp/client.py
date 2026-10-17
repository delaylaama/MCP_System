"""
Model Context Protocol (MCP) Client Service.
Communicates with the MCP Server using the official Python MCP SDK v2 Streamable HTTP transport.
"""

import json
from typing import List, Dict, Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.providers.manager import provider_manager

settings = get_settings()


class MCPClientService:
    """Manages MCP client connections, tool discovery, and tool execution."""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or settings.MCP_SERVER_URL
        self._last_failure = 0.0

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Discover tools exposed by the MCP server."""
        import asyncio
        import time
        if time.time() - self._last_failure < 5.0:
            return self._fallback_tool_definitions()

        async def _fetch():
            async with streamable_http_client(self.server_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                        for tool in tools_result.tools
                    ]
        try:
            return await asyncio.wait_for(_fetch(), timeout=1.0)
        except Exception as e:
            self._last_failure = time.time()
            logger.warning(f"MCP server list_tools unavailable ({e}), using fallback registry.")
            return self._fallback_tool_definitions()

    async def _call_remote(self, name: str, arguments: Dict[str, Any]) -> Any:
        async with streamable_http_client(self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name=name, arguments=arguments)

                if result.is_error:
                    error_msg = result.content[0].text if result.content else "Tool call failed"
                    raise RuntimeError(f"MCP tool '{name}' returned error: {error_msg}")

                # Prefer structured_content if available
                if getattr(result, "structured_content", None) is not None:
                    return result.structured_content

                if result.content:
                    parsed_items = []
                    for item in result.content:
                        if hasattr(item, "text"):
                            try:
                                parsed = json.loads(item.text)
                                if isinstance(parsed, list):
                                    parsed_items.extend(parsed)
                                else:
                                    parsed_items.append(parsed)
                            except Exception:
                                parsed_items.append(item.text)
                    if len(parsed_items) == 1 and not isinstance(parsed_items[0], (dict, list)):
                        return parsed_items[0]
                    return parsed_items

                return None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes an MCP tool on the server with fast timeout and seamless fallback."""
        import asyncio
        import time
        logger.info(f"Invoking MCP tool '{name}' with arguments: {arguments}")
        if time.time() - self._last_failure < 5.0:
            return await self._execute_fallback_tool(name, arguments)
        try:
            return await asyncio.wait_for(self._call_remote(name, arguments), timeout=1.0)
        except Exception as e:
            self._last_failure = time.time()
            logger.warning(f"MCP remote call to '{name}' unavailable or timed out ({e}). Executing local provider fallback.")
            return await self._execute_fallback_tool(name, arguments)

    def _fallback_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "search_files",
                "description": "Search files across connected storage providers.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "provider": {"type": "string"},
                        "file_type": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "list_files",
                "description": "List files and subfolders within a directory or cloud folder.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "provider": {"type": "string"},
                        "folder_id": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            },
            {
                "name": "get_file_metadata",
                "description": "Retrieve standardized file metadata.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "provider": {"type": "string"},
                    },
                    "required": ["file_id"],
                },
            },
            {
                "name": "get_file_content",
                "description": "Extract readable text content from a document.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "provider": {"type": "string"},
                    },
                    "required": ["file_id"],
                },
            },
        ]

    async def _execute_fallback_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Direct fallback executing through ProviderManager if MCP server daemon is disconnected."""
        if name == "search_files":
            query = args.get("query", "")
            provider = args.get("provider")
            user_id = args.get("user_id")
            targets = [provider] if provider and provider != "all" else None
            filters = {"file_type": args.get("file_type")} if args.get("file_type") else None
            credentials_map = {}
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
            records = await provider_manager.search_all(
                query=query,
                target_providers=targets,
                filters=filters,
                credentials_map=credentials_map,
            )
            return [r.model_dump(mode="json") for r in records]
        elif name == "list_files":
            records = await provider_manager.list_files(
                provider_name=args.get("provider", "local"),
                folder_id=args.get("folder_id"),
                limit=args.get("limit", 50),
            )
            return [r.model_dump(mode="json") for r in records]
        elif name == "get_file_metadata":
            record = await provider_manager.get_file_metadata(
                provider_name=args.get("provider", "local"),
                file_id=args.get("file_id", ""),
            )
            return record.model_dump(mode="json")
        elif name == "get_file_content":
            return await provider_manager.get_file_content(
                provider_name=args.get("provider", "local"),
                file_id=args.get("file_id", ""),
            )
        raise ValueError(f"Unknown fallback tool '{name}'")


mcp_client = MCPClientService()
