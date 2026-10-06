"""AgentPlanner — «как сделать X» через HTN (ADR-102)."""
from __future__ import annotations
from aura.core.protocol import AgentResponse, BaseAgent
from aura.core.htn_planner import get_planner


class AgentPlanner(BaseAgent):
    name = "planner"
    MODULE_ALWAYS = True
    KEYWORDS = ("как сделать", "план", "как выполнить",
                "покажи план", "что для этого нужно")

    def can_handle(self, request):
        t = request.text.lower().strip()
        # Не перехватывать «выполни план» — это AgentReact
        if "выполни план" in t or "запусти план" in t or "сделай по плану" in t:
            return False
        return any(k in t for k in self.KEYWORDS)

    async def handle(self, request):
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        # извлечь цель после "как сделать"
        goal = text
        for kw in self.KEYWORDS:
            if kw in text:
                goal = text[text.index(kw) + len(kw):].strip(" .,!?:;")
                break
        p = get_planner()
        ops = p.plan(goal or text)
        if not ops:
            return AgentResponse.ok(f"Нет плана для: {goal}", self.name)
        lines = [f"План для: {goal}", ""]
        for i, op in enumerate(ops, 1):
            lines.append(f"{i}. {op.description} → {op.capability}")
        return AgentResponse.ok("\n".join(lines), self.name)


__all__ = ["AgentPlanner"]
