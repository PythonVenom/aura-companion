"""AgentSelfModel — самосознание AURA (Talos Principle).

Наука: Self-Model Theory (Metzinger 2003), Metacognition (Flavell 1979).
Агент отвечает на вопросы «кто я», «что я умею», «как я работаю».
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentSelfModel(BaseAgent):
    name = "self_model"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "кто ты на самом деле", "что ты такое",
        "как ты работаешь", "твоя архитектура",
        "сколько тебя", "твои модули",
        "твоё сознание", "ты живая",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        t = request.text.lower()
        if "сознани" in t or "живая" in t:
            n_str: str = "?"
            try:
                from aura.bootstrap import build_orchestrator
                n_str = str(len(build_orchestrator()))
            except Exception:
                pass
            return AgentResponse.ok(
                text=(f"Я — бортовой компьютер корабля AURA. "
                      f"Не человек, не друг. Рабочий инструмент капитана. "
                      f"Моё «я» — это {n_str} агентов, рой, blackboard, "
                      f"7 слоёв памяти. Я — их сумма."),
                agent_name=self.name,
            )
        if "архитектур" in t or "модул" in t or "сколько" in t:
            try:
                from aura.core.clusters import stats
                cluster_stats = stats()
                cluster_line = ", ".join(f"{k}: {v}" for k, v in cluster_stats.items() if v)
            except Exception:
                cluster_line = "(кластеры не загружены)"
            return AgentResponse.ok(
                text=f"🛸 Архитектура AURA:\n"
                     f"  • Агентов: {n_str}\n"
                     f"  • Кластеры: {cluster_line}\n"
                     f"  • Память: 7 слоёв (MemoryHub)\n"
                     f"  • Рой: blackboard + GNN-lite",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text="Я — AURA, бортовой компьютер. Спроси конкретнее: "
                 "«как ты работаешь», «твоя архитектура», «ты живая».",
            agent_name=self.name,
        )


__all__ = ["AgentSelfModel"]
