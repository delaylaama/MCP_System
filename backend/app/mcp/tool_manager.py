"""Tool Manager translating MCP tool schemas into LLM function specifications."""

from typing import List, Dict, Any
from backend.app.mcp.client import mcp_client


class ToolManager:
    """Manages MCP tool definitions and transforms them for LLM function calling."""

    @staticmethod
    async def get_openai_tools() -> List[Dict[str, Any]]:
        """Formats MCP tools into OpenAI function calling schema."""
        tools = await mcp_client.list_tools()
        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
                },
            })
        return openai_tools

    @staticmethod
    async def execute_tool(name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches tool execution through the MCP Client."""
        return await mcp_client.call_tool(name, arguments)
