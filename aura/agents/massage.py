"""MassageSessionAgent — сессия массажа (ADR-044).

Beachhead = массажист = автор. Первый агент для Founder-First.
JTBD: таймер + RAG по клиенту + диктовка + отчёт.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


@dataclass
class Session:
    """Одна сессия массажа."""
    client: str
    duration_min: int = 50
    started_at: float = field(default_factory=time.time)
    notes: str = ""
    active: bool = True

    @property
    def ends_at(self) -> float:
        return self.started_at + self.duration_min * 60

    @property
    def remaining_min(self) -> int:
        return max(0, int((self.ends_at - time.time()) / 60))


class AgentMassage(BaseAgent):
    """Голосовые сессии массажа.

    Команды:
      - «сессия Иванов 50 минут»
      - «что было с Ивановым?»
      - «запиши: спина, L4-L5, напряжение»
      - «закончить сессию»
    """

    name = "massage"
    MODULE_ALWAYS = True
    KEYWORDS = (
        "сессия", "клиент", "массаж",
        "что было с", "запиши",
    )

    def __init__(self) -> None:
        super().__init__()
        self._current: Session | None = None

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        # Старт сессии
        if "сессия" in text or "массаж" in text:
            return self._start(text)

        # Запрос истории
        if "что было с" in text:
            return self._history(text)

        # Заметка
        if "запиши" in text:
            return self._note(text)

        # Завершить
        if "закончить" in text or "конец сессии" in text:
            return self._finish()

        return AgentResponse.not_handled(self.name)

    def _start(self, text: str) -> AgentResponse:
        import re
        # Ищем имя + минуты
        m = re.search(r"(?:сессия|массаж)\s+(\w+)\s+(\d+)", text)
        if not m:
            return AgentResponse.ok(
                "Скажи: «сессия Иванов 50 минут»", self.name
            )
        client = m.group(1).capitalize()
        duration = int(m.group(2))
        self._current = Session(client=client, duration_min=duration)
        return AgentResponse.ok(
            f"✅ Сессия {client}, {duration} мин. Начали.", self.name
        )

    def _history(self, text: str) -> AgentResponse:
        # TODO шаг 3: RAG
        import re
        m = re.search(r"что было с\s+(\w+)", text)
        if not m:
            return AgentResponse.ok("Скажи: «что было с Ивановым?»", self.name)
        client = m.group(1).capitalize()
        return AgentResponse.ok(
            f"📋 История {client}: RAG пока не подключён (шаг 3).", self.name
        )

    def _note(self, text: str) -> AgentResponse:
        if not self._current:
            return AgentResponse.ok("Сначала начни сессию.", self.name)
        note = text.replace("запиши", "").strip(" :,")
        self._current.notes += (" " if self._current.notes else "") + note
        return AgentResponse.ok(f"📝 Записал: {note[:60]}", self.name)

    def _finish(self) -> AgentResponse:
        if not self._current:
            return AgentResponse.ok("Нет активной сессии.", self.name)
        s = self._current
        s.active = False
        # TODO шаг 3: сохранить в RAG
        self._current = None
        return AgentResponse.ok(
            f"✅ Сессия {s.client} завершена. Заметок: {len(s.notes.split())}.",
            self.name,
        )


__all__ = ["AgentMassage", "Session"]
