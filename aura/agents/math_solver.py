"""AgentMathSolver — детерминированная арифметика (не LLM).

Stiennon 2020: не мучаем LLM арифметикой. Python eval() с whitelist.
"""
from __future__ import annotations

import re

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentMathSolver(BaseAgent):
    name = "math_solver"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in (
            "сколько будет", "вычисли", "посчитай",
            "умножить на", "плюс", "минус",
        ))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        m = re.search(r"(?:сколько будет|вычисли|посчитай)\s+(.+)", text)
        if m:
            expr = m.group(1)
        else:
            expr = text
        expr = (expr
            .replace("умножить на", "*").replace("умножить", "*")
            .replace("плюс", "+").replace("минус", "-")
            .replace("разделить на", "/").replace("делить на", "/")
        )
        expr = re.sub(r"[^0-9+\-*/().\s]", "", expr).strip()
        if not expr:
            return AgentResponse.not_handled(self.name)
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return AgentResponse.ok(text=f"📊 {expr} = {result}", agent_name=self.name)
        except Exception:
            return AgentResponse.not_handled(self.name)


__all__ = ["AgentMathSolver"]
