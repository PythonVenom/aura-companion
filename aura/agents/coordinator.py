"""AgentCoordinator — арбитр 107 агентов (рой / стая).

Наука:
- Blackboard Architecture (Hayes-Roth 1985)
- Stigmergy (Grasse 1959) — координация через следы
- Consensus (Lamport 1982) — приоритеты и разрешение конфликтов

Роль координатора НЕ командовать, а:
- читать blackboard (следы других агентов),
- собирать контекст (сектор, тревоги, активные задачи),
- давать сводку при запросе «что происходит / рой / статус».

Это «капитанский мостик» AURA.
"""
from __future__ import annotations

from aura.core import blackboard as bb
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentCoordinator(BaseAgent):
    """Координатор роя: собирает состояние blackboard."""

    name = "coordinator"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "что происходит", "рой", "стая", "обстановка",
        "что делают агенты", "статус роя", "сводка",
        "бортовой журнал", "что нового у экипажа",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        snap = bb.snapshot()
        sector = snap.get("sector", "unknown")
        alerts = bb.recent_alerts(window_sec=300)
        tasks = bb.active_tasks()
        facts = snap.get("facts", {})

        # Критичные тревоги — в приоритете
        critical = [a for a in alerts if a.get("level") == "critical"]

        lines = [f"🛸 Бортовой журнал. Сектор: {sector}."]
        if critical:
            lines.append(f"⚠️ КРИТИЧНО: {len(critical)} тревог(и).")
            for a in critical[:3]:
                lines.append(f"  • {a['agent']}: {a['text'][:60]}")
        if tasks:
            lines.append(f"📋 Активных задач: {len(tasks)}.")
            for t in tasks[:3]:
                lines.append(f"  • {t['agent']}: {t['text'][:50]} ({t['status']})")
        if facts:
            keys = ", ".join(list(facts.keys())[:5])
            lines.append(f"🧠 Общие факты: {keys}.")
        if not critical and not tasks:
            lines.append("📊 Все системы в норме. Экипаж дежурит.")

        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)


__all__ = ["AgentCoordinator"]
