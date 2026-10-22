"""#140 AgentPlanner — автономные цепочки задач через ReAct.

Наука:
- ReAct (Yao 2022) — Reasoning + Acting
- Plan-and-Solve (Wang 2023) — планирование перед действием
- HuggingGPT (Shen 2023) — LLM как контроллер

Отличие от AgentReact:
- React — один запрос → один цикл
- Planner — сложная цель → цепочка шагов + recall_log

Пример:
  «Найди рецепт борща и добавь продукты в список»
  → шаг 1: internet: «рецепт борща»
  → шаг 2: parse: извлечь ингредиенты
  → шаг 3: checklist: добавить в список
"""
from __future__ import annotations

import contextlib

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.react_loop import react_loop
from aura.core.recall_log import record


class AgentPlanner(BaseAgent):
    """Автономный планировщик цепочек."""

    name = "planner"

    TRIGGERS = (
        "план", "спланируй", "сделай цепочку", "выполни по шагам",
        "сначала", "потом", "автономно", "сделай за меня",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.strip()
        result = self._run_plan(text)

        # Запись в recall_log (#141)
        with contextlib.suppress(Exception):
            record(
                agent=self.name,
                action="plan",
                detail=f"{text[:100]} → {result.get('answer', '')[:100]}",
            )

        answer = result.get("answer", "Не смогла спланировать")
        steps = result.get("steps", [])
        iters = result.get("iterations", 0)

        # Формат вывода
        lines = [f"🎯 {answer}", ""]
        if steps:
            lines.append(f"📋 Шагов: {len(steps)} (итераций: {iters})")
            for i, s in enumerate(steps[:5], 1):
                act = s.get("action", "?")
                args = s.get("args", {})
                lines.append(f"  {i}. [{act}] {args}")

        return AgentResponse.ok(
            text="\n".join(lines),
            agent_name=self.name,
        )

    def _run_plan(self, text: str) -> dict:
        """Запустить ReAct loop. Fallback при ошибке."""
        try:
            return react_loop(text, max_iterations=5)
        except Exception as e:
            return {
                "answer": f"❌ Планирование не удалось: {e}",
                "steps": [],
                "iterations": 0,
            }


__all__ = ["AgentPlanner"]
