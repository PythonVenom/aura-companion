"""#150 AgentFDIR — статус FDIR."""
from __future__ import annotations

from aura.core.fdir import check_health, format_status
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentFDIR(BaseAgent):
    name = "fdir"

    TRIGGERS = ("статус системы", "fdir", "режим системы", "здоровье системы")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        check_health()
        return AgentResponse.ok(text=format_status(), agent_name=self.name)


__all__ = ["AgentFDIR"]
