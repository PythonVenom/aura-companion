"""Telegram адаптер — голосовое управление Telegram."""
from __future__ import annotations
from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

class AgentTelegram(MicroAgent):
    KEYWORDS = ("телеграм", "открой телеграм", "напиши в телеграм")
    
    def __init__(self):
        super().__init__("telegram", "Telegram адаптер")
    
    def can_handle(self, request: AgentRequest) -> bool:
        return any(kw in request.text.lower() for kw in self.KEYWORDS)
    
    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.ok("Telegram: заготовка", self.name)

__all__ = ["AgentTelegram"]
