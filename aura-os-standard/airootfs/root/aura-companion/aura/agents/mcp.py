"""MCP адаптер — Model Context Protocol для внешних инструментов."""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentMcp(MicroAgent):
    """MCP: подключение к внешним серверам инструментов."""
    KEYWORDS = ("mcp", "внешний инструмент", "подключи сервер")

    def __init__(self):
        super().__init__("mcp", "MCP адаптер")
        self.servers = {}

    def can_handle(self, request: AgentRequest) -> bool:
        return any(kw in request.text.lower() for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.ok("MCP: заготовка", self.name)

__all__ = ["AgentMcp"]
