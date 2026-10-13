"""Блок 7 — Wellness MVP: дыхательные практики.

Наука:
- 4-7-8 (Dr. Andrew Weil) — активация парасимпатической системы
- Box breathing (Navy SEAL) — снижение кортизола
- Zaccaro 2018 — Breathing & autonomic nervous system
- Balban 2023 — Cyclic sighing > mindfulness meditation (Stanford)

Практики:
- 4-7-8:    вдох 4с → задержка 7с → выдох 8с (от тревоги/бессонницы)
- Box:      4-4-4-4 (от стресса, фокус)
- Deep:     вдох 4с → выдох 6с (базовая релаксация)

Voice guide — через AgentSpeaker (опционально, если доступен).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


@dataclass
class Practice:
    name: str
    phases: list[tuple[str, int]]  # [("вдох", 4), ("задержка", 7), ("выдох", 8)]
    cycles: int = 4
    description: str = ""

    @property
    def total_seconds(self) -> int:
        return sum(d for _, d in self.phases) * self.cycles


# Предопределённые практики
PRACTICES: dict[str, Practice] = {
    "4-7-8": Practice(
        name="4-7-8",
        phases=[("вдох", 4), ("задержка", 7), ("выдох", 8)],
        cycles=4,
        description="От тревоги и бессонницы. Активирует парасимпатику.",
    ),
    "box": Practice(
        name="Box breathing",
        phases=[("вдох", 4), ("задержка", 4), ("выдох", 4), ("задержка", 4)],
        cycles=4,
        description="От стресса, для фокуса. Используется Navy SEAL.",
    ),
    "deep": Practice(
        name="Глубокое дыхание",
        phases=[("вдох", 4), ("выдох", 6)],
        cycles=6,
        description="Базовая релаксация. Подходит для начала.",
    ),
}


class AgentWellness(BaseAgent):
    """Агент wellness-практик (дыхание)."""

    name = "wellness"

    STRESS_KEYWORDS = (
        "стресс", "тревог", "паник", "успокой", "подышать",
        "дыхание", "дыхан", "дыхательную", "практику",
    )
    SLEEP_KEYWORDS = (
        "не могу уснуть", "бессонниц", "уснуть", "сон",
        "заснуть", "4-7-8",
    )
    BOX_KEYWORDS = ("box breathing", "квадрат", "фокус", "сосредоточ")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(
            kw in t
            for kw in (self.STRESS_KEYWORDS + self.SLEEP_KEYWORDS + self.BOX_KEYWORDS)
        )

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if any(kw in t for kw in self.SLEEP_KEYWORDS):
            practice = PRACTICES["4-7-8"]
        elif any(kw in t for kw in self.BOX_KEYWORDS):
            practice = PRACTICES["box"]
        elif "глубок" in t or "базов" in t:
            practice = PRACTICES["deep"]
        else:
            # По умолчанию — 4-7-8 при стрессе
            practice = PRACTICES["4-7-8"]

        return AgentResponse.ok(
            text=self._format(practice),
            agent_name=self.name,
        )

    @staticmethod
    def _format(p: Practice) -> str:
        lines = [
            f"🌬️ {p.name}",
            f"   {p.description}",
            "",
            f"   {p.cycles} цикла, ~{p.total_seconds} сек:",
        ]
        for phase, dur in p.phases:
            lines.append(f"     • {phase}: {dur} сек")
        lines.append("")
        lines.append("   Дыши вместе со мной. Расслабь плечи. Закрой глаза, если удобно.")
        return "\n".join(lines)

    def list_practices(self) -> str:
        """Список всех практик (для команды 'какие практики')."""
        lines = ["🌬️ Доступные практики:"]
        for key, p in PRACTICES.items():
            lines.append(f"  • {p.name} ({key}) — {p.total_seconds}с, {p.description}")
        return "\n".join(lines)


__all__ = ["AgentWellness", "Practice", "PRACTICES"]
