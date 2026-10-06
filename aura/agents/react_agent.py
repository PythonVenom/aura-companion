"""AgentReact — «выполни план X» (ADR-103)."""
from __future__ import annotations
from aura.core.protocol import AgentResponse, BaseAgent
from aura.core.htn_planner import get_planner
from aura.core.react_loop import ReActLoop, format_episode


class AgentReact(BaseAgent):
    name = "react_agent"
    MODULE_ALWAYS = True
    KEYWORDS = ("выполни план", "запусти план", "сделай по плану",
                "react", "выполни цепочку")

    def can_handle(self, request):
        t = request.text.lower().strip()
        return any(k in t for k in self.KEYWORDS)

    async def handle(self, request):
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        goal = text
        for kw in self.KEYWORDS:
            if kw in text:
                goal = text[text.index(kw) + len(kw):].strip(" .,!?:;")
                break
        p = get_planner()
        ops = p.plan(goal or text)
        if not ops:
            return AgentResponse.ok(f"Нет плана для: {goal}", self.name)

        from aura.core.dispatcher import dispatch
        loop = ReActLoop(executor=dispatch)
        ep = loop.run(goal, ops)
        return AgentResponse.ok(format_episode(ep), self.name)


__all__ = ["AgentReact"]
