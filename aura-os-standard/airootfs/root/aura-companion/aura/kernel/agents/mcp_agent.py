"""Агент MCP для вызова внешних инструментов."""
import asyncio
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.mcp.client import MCPClient

class AgentMCP(BaseAgent):
    name = "mcp"
    MODULE_ALWAYS = True

    def __init__(self):
        self.client = MCPClient(["python3", "aura/mcp/test_server.py"])
        self._started = False

    async def _ensure_started(self):
        if not self._started:
            await self.client.start()
            self._started = True

    def can_handle(self, request: AgentRequest) -> bool:
        return "эхо" in request.text.lower() or "mcp" in request.text.lower()

    async def handle(self, request: AgentRequest) -> AgentResponse:
        await self._ensure_started()
        # Извлекаем текст для эха (все, что после "эхо")
        text = request.text.lower().replace("эхо", "").strip()
        if not text:
            return AgentResponse.ok("Что сказать в эхо?", self.name)
        
        try:
            result = await self.client.call_tool("echo", {"text": text})
            return AgentResponse.ok(f"🔌 MCP: {result}", self.name)
        except Exception as e:
            return AgentResponse.ok(f"❌ Ошибка MCP: {e}", self.name)

    async def stop(self):
        await self.client.stop()

__all__ = ["AgentMCP"]
