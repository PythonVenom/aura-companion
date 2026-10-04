"""AgentCapabilities — «что ты умеешь» (ADR-101)."""
from __future__ import annotations
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.capability_graph import get_graph


class AgentCapabilities(BaseAgent):
    name = "capabilities"
    MODULE_ALWAYS = True
    KEYWORDS = ("что ты умеешь", "твои возможности", "список функций",
                "что можешь", "capabilities")

    def can_handle(self, request):
        t = request.text.lower().strip()
        return any(k in t for k in self.KEYWORDS)

    async def handle(self, request):
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        g = get_graph()
        # Группировка по префиксу
        groups = {}
        for n in g.all_names():
            prefix = n.split(".")[0]
            groups.setdefault(prefix, []).append(n.split(".", 1)[1])
        lines = [f"Возможности ({len(g.all_names())}):"]
        for prefix, items in sorted(groups.items()):
            lines.append(f"  {prefix}: {', '.join(items)}")
        return AgentResponse.ok("\n".join(lines), self.name)


__all__ = ["AgentCapabilities"]
