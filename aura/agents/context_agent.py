"""AgentContextMemory — «что делал?» (ADR-096)."""
from __future__ import annotations

from aura.core.context import get_context
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentRecentActivity(BaseAgent):
    name = "context_recent"
    MODULE_ALWAYS = True
    KEYWORDS = ("что я делал", "что делал", "чем занимался",
                "последние действия", "недавно делал")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        ctx = get_context()
        return AgentResponse.ok(ctx.summary(minutes=10), self.name)


__all__ = ["AgentRecentActivity"]
