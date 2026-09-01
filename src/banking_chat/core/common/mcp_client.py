"""Official Streamable HTTP MCP Client for querying remote MCP servers over JSON-RPC 2.0."""

from __future__ import annotations

import json
from typing import Any

import httpx

from banking_chat.core.common.exceptions import ToolExecutionError


class StreamableMCPClient:
    """Client for communicating with Streamable HTTP MCP Microservices using the MCP Protocol."""

    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def list_tools(self) -> list[dict[str, Any]]:
        """Query tools/list over MCP protocol."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/mcp", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    tools_list = data.get("result", {}).get("tools", [])
                    if isinstance(tools_list, list):
                        return [t for t in tools_list if isinstance(t, dict)]
        except Exception as err:
            raise ToolExecutionError("list_tools", f"Failed to connect to MCP at {self.base_url}: {err}") from err
        return []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Invoke a tool via MCP tools/call JSON-RPC standard."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/mcp", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if "error" in data:
                        raise ToolExecutionError(name, str(data["error"]))

                    # Extract content from MCP result schema
                    result = data.get("result", {})
                    content_blocks = result.get("content", [])
                    if content_blocks and isinstance(content_blocks, list):
                        first_block = content_blocks[0]
                        if isinstance(first_block, dict) and "text" in first_block:
                            text_val = first_block["text"]
                            try:
                                return json.loads(text_val)
                            except Exception:
                                return text_val
                    return result
        except ToolExecutionError:
            raise
        except Exception as err:
            raise ToolExecutionError(name, f"Failed executing MCP tool {name}: {err}") from err

        raise ToolExecutionError(name, f"MCP Server returned HTTP {resp.status_code}")
