"""MCP Client для Aura (Model Context Protocol).

Позволяет подключать внешние инструменты (серверы MCP)
и отдавать их Aura как единый интерфейс.
"""
import logging

logger = logging.getLogger("aura.mcp")

class MCPClient:
    def __init__(self):
        self.servers = []

    def register_server(self, name: str, command: list[str]):
        """Регистрация внешнего MCP-сервера (stdio)."""
        logger.info(f"Регистрация MCP-сервера: {name}")
        self.servers.append({"name": name, "command": command})

    async def list_tools(self):
        """Запросить список инструментов у всех подключенных серверов."""
        # В будущем: JSON-RPC вызов к серверам
        return []
