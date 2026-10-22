"""Менеджер MCP-серверов."""
import json, logging
from pathlib import Path
from .client import StdioMCPClient

log = logging.getLogger("aura.mcp.manager")
CONFIG_PATH = Path.home() / ".config/aura/mcp_servers.json"

class MCPManager:
    def __init__(self):
        self.clients: dict[str, StdioMCPClient] = {}
        self.tools: dict[str, dict] = {}

    async def load_all(self):
        if not CONFIG_PATH.exists(): return
        conf = json.loads(CONFIG_PATH.read_text())
        for name, cfg in conf.get("servers", {}).items():
            try:
                client = StdioMCPClient(cfg["command"], cfg.get("env"))
                await client.start()
                tools = await client.list_tools()
                self.clients[name] = client
                for t in tools:
                    t_name = t["name"]
                    self.tools[t_name] = {"client": client, "schema": t}
                    log.info("MCP: registered tool %s from %s", t_name, name)
            except Exception as e:
                log.error("Failed to start MCP server %s: %s", name, e)

    async def call(self, tool_name: str, arguments: dict):
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        return await self.tools[tool_name]["client"].call_tool(tool_name, arguments)

    async def close_all(self):
        """Корректное завершение всех MCP-серверов."""
        for client in self.clients.values():
            try:
                await client.stop()
            except Exception:
                pass
        self.clients.clear()
        self.tools.clear()
