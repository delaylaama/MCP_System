"""
AI & LLM Service supporting intelligent tool selection, parameter generation, and natural-language synthesis.
Interacts with the Model Context Protocol (MCP) Client layer.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.mcp.client import mcp_client
from backend.app.mcp.tool_manager import ToolManager

settings = get_settings()


class BaseLLMProvider(ABC):
    @abstractmethod
    async def analyze_and_execute_search(
        self,
        query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Interprets user intent, determines tool call, executes tool, and returns response."""
        pass


class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def analyze_and_execute_search(
        self,
        query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the intelligent assistant for Universal AI File Manager. "
                    "Select and execute the appropriate MCP tool to satisfy the user's file query. "
                    "Extract relevant keywords, file types, and date constraints."
                ),
            },
            {"role": "user", "content": query},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": available_tools,
            "tool_choice": "auto",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API call failed: {resp.text}")
            data = resp.json()

        choice = data["choices"][0]["message"]
        tool_calls = choice.get("tool_calls", [])

        if not tool_calls:
            return {
                "intent": {"action": "direct_reply"},
                "ai_summary": choice.get("content", "No search tool required."),
                "results": [],
            }

        # Execute first tool call via MCP
        first_call = tool_calls[0]
        tool_name = first_call["function"]["name"]
        tool_args = json.loads(first_call["function"]["arguments"])
        if context and context.get("user_id"):
            tool_args["user_id"] = context.get("user_id")

        tool_results = await mcp_client.call_tool(tool_name, tool_args)

        # Synthesize final user-friendly summary
        summary = f"Retrieved {len(tool_results) if isinstance(tool_results, list) else 1} results using MCP tool '{tool_name}'."
        return {
            "intent": {"action": tool_name, "parameters": tool_args},
            "ai_summary": summary,
            "results": tool_results if isinstance(tool_results, list) else [tool_results],
        }


class HeuristicReasoningAgent(BaseLLMProvider):
    """
    Autonomous heuristic reasoning agent.
    Performs NLP intent classification, entity extraction, file extension mapping, and time resolution
    when no external commercial API key is provided, ensuring zero downtime for demonstrations.
    """

    async def analyze_and_execute_search(
        self,
        query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query_lower = query.lower()

        # 1. Detect duplicate check intent
        if "duplicate" in query_lower or "duplicates" in query_lower:
            dup_results = await mcp_client.call_tool("find_duplicates", {})
            return {
                "intent": {"action": "find_duplicates", "parameters": {}},
                "ai_summary": f"Analyzed files across connected storage and found {len(dup_results)} duplicate clusters.",
                "results": dup_results,
            }

        # 2. Detect listing intent
        if query_lower.startswith("list") or "show all" in query_lower:
            list_results = await mcp_client.call_tool("list_files", {"limit": 50})
            return {
                "intent": {"action": "list_files", "parameters": {"limit": 50}},
                "ai_summary": f"Retrieved directory listing with {len(list_results)} items.",
                "results": list_results,
            }

        # 3. Target provider extraction
        provider = None
        if "google drive" in query_lower or "gdrive" in query_lower:
            provider = "google_drive"
        elif "onedrive" in query_lower:
            provider = "onedrive"
        elif "dropbox" in query_lower:
            provider = "dropbox"
        elif "local" in query_lower or "system" in query_lower:
            provider = "local"

        if not provider and context and context.get("providers") and len(context["providers"]) == 1:
            provider = context["providers"][0]

        # 4. File type extraction
        file_type = context.get("file_type") if context else None
        if not file_type:
            for ext in ["pdf", "docx", "doc", "txt", "csv", "xlsx", "md", "png", "jpg", "zip", "py"]:
                if ext in query_lower:
                    file_type = ext
                    break

        # 5. Semantic keyword extraction using NLP query parser
        from backend.app.utils.query_parser import clean_query_text, is_recency_query

        clean_query = clean_query_text(query)
        if not clean_query:
            clean_query = "*"

        user_id = context.get("user_id") if context else None
        tool_args = {"query": clean_query}
        if is_recency_query(query):
            tool_args["sort"] = "modified_desc"
        if user_id:
            tool_args["user_id"] = user_id
        if provider:
            tool_args["provider"] = provider
        if file_type:
            tool_args["file_type"] = file_type

        # Dispatch via MCP Client
        search_results = await mcp_client.call_tool("search_files", tool_args)

        count = len(search_results) if isinstance(search_results, list) else 0
        ai_summary = (
            f"Understood request for '{clean_query}'. "
            f"Invoked MCP tool 'search_files' across connected providers and retrieved {count} matching files."
        )

        return {
            "intent": {"action": "search_files", "parameters": tool_args},
            "ai_summary": ai_summary,
            "results": search_results if isinstance(search_results, list) else [],
        }


class OllamaLLMProvider(BaseLLMProvider):
    """
    Local tool-calling LLM provider using Ollama (default: qwen2.5:7b).
    Checks that Ollama is installed and model is pulled.
    Does NOT install silently; prints instructions if missing and falls back to HeuristicReasoningAgent.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback = HeuristicReasoningAgent()

    async def check_availability(self) -> tuple[bool, str]:
        """Verifies Ollama server is running and model is pulled."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False, f"Ollama returned HTTP {resp.status_code}"
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                model_base = self.model.split(":")[0]
                matched = any(self.model in m or m.startswith(model_base) for m in models)
                if not matched:
                    return False, f"Model '{self.model}' is not pulled in Ollama. Available: {models}"
                return True, "Ready"
        except Exception as e:
            return False, f"Cannot connect to Ollama at {self.base_url}: {e}"

    async def analyze_and_execute_search(
        self,
        query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ready, msg = await self.check_availability()
        if not ready:
            print("\n" + "=" * 70)
            print(f"[Ollama LLM Notice] {msg}")
            print(f"To use Ollama ({self.model}) as the tool-calling model:")
            print("  1. Download and install Ollama from: https://ollama.ai")
            print(f"  2. Pull the model in your terminal: ollama pull {self.model}")
            print("  3. Ensure Ollama service is active.")
            print("Falling back to local heuristic search engine.")
            print("=" * 70 + "\n")
            logger.warning(f"Ollama unavailable ({msg}). Falling back to HeuristicReasoningAgent.")
            return await self.fallback.analyze_and_execute_search(query, available_tools, context)

        # Call Ollama OpenAI-compatible chat endpoint
        url = f"{self.base_url}/v1/chat/completions"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the intelligent assistant for MCP Drivers. "
                    "Select and execute the appropriate search_files MCP tool to find the user's files. "
                    "Set sort='modified_desc' if the user asks for latest, newest, or recent. "
                    "Set file_types=['pdf','docx'] for resumes/docs, or ['png','jpg','jpeg','webp'] for images."
                ),
            },
            {"role": "user", "content": query},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": available_tools,
            "tool_choice": "auto",
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"Ollama chat error: {resp.text}, using heuristic fallback")
                    return await self.fallback.analyze_and_execute_search(query, available_tools, context)
                data = resp.json()

            choice = data["choices"][0]["message"]
            tool_calls = choice.get("tool_calls", [])
            if not tool_calls:
                return await self.fallback.analyze_and_execute_search(query, available_tools, context)

            first_call = tool_calls[0]
            tool_name = first_call["function"]["name"]
            raw_args = first_call["function"]["arguments"]
            tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            if context and context.get("user_id"):
                tool_args["user_id"] = context.get("user_id")

            tool_results = await mcp_client.call_tool(tool_name, tool_args)
            count = len(tool_results) if isinstance(tool_results, list) else 1
            summary = f"Retrieved {count} results via Ollama ({self.model}) calling '{tool_name}'."
            return {
                "intent": {"action": tool_name, "parameters": tool_args},
                "ai_summary": summary,
                "results": tool_results if isinstance(tool_results, list) else [tool_results],
            }
        except Exception as e:
            logger.warning(f"Ollama call exception: {e}, falling back to heuristic")
            return await self.fallback.analyze_and_execute_search(query, available_tools, context)


class AIService:
    def __init__(self):
        if settings.LLM_PROVIDER == "ollama":
            logger.info(f"Initializing AIService with OllamaLLMProvider ({settings.OLLAMA_MODEL})")
            self.provider = OllamaLLMProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
        elif settings.OPENAI_API_KEY:
            logger.info("Initializing AIService with OpenAILLMProvider")
            self.provider = OpenAILLMProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
        else:
            logger.info("Initializing AIService with Autonomous HeuristicReasoningAgent")
            self.provider = HeuristicReasoningAgent()

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        openai_tools = await ToolManager.get_openai_tools()
        return await self.provider.analyze_and_execute_search(query, openai_tools, context)


ai_service = AIService()
