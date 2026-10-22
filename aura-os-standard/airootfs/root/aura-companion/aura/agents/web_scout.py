"""AgentWebScout — сканирует новости по секторам инфокосмоса.

Наука: News Aggregation (Google News, 2002), RSS/Atom.
Лор: AURA летит по секторам, сканирует сигналы.
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentWebScout(BaseAgent):
    """Сканирует новости/сигналы по секторам."""

    name = "web_scout"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "сканируй новости", "просканируй", "что нового в",
            "новости про", "сигналы из",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        return AgentResponse.ok(
            text="🛸 Сканирую сектор... Сигналов: 0 (задел для RSS/API).",
            agent_name=self.name,
        )


__all__ = ["AgentWebScout"]
