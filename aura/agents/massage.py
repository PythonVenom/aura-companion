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
        self._rag = None

    def _get_rag(self):
        """Lazy-init RAG (не создаём ChromaDB если не нужно)."""
        if self._rag is None:
            try:
                from aura.agents.rag_memory import AgentRAGMemory
                self._rag = AgentRAGMemory()
            except Exception:
                self._rag = False  # marker: не удалось
        return self._rag or None

    def _rag_save(self, client: str, text: str) -> bool:
        """Сохранить заметку в RAG. Возвращает True если ок."""
        rag = self._get_rag()
        if not rag:
            return False
        try:
            rag.remember(f"массаж {client}: {text}", "")
            return True
        except Exception:
            return False

    def _rag_read(self, client: str) -> str:
        """Прочитать историю из RAG."""
        rag = self._get_rag()
        if not rag:
            return "RAG недоступен"
        try:
            return rag.search(f"массаж {client}", n_results=3)
        except Exception as e:
            return f"Ошибка RAG: {e}"

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
        client = m.group(1).title()
        duration = int(m.group(2))
        self._current = Session(client=client, duration_min=duration)
        self._rag_save(client, f"начало сессии, {duration} мин")
        return AgentResponse.ok(
            f"✅ Сессия {client}, {duration} мин. Начали.", self.name
        )

    def _history(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"что было с\s+(\w+)", text)
        if not m:
            return AgentResponse.ok("Скажи: «что было с Ивановым?»", self.name)
        client = m.group(1).title()
        hist = self._rag_read(client)
        if not hist or len(hist) < 5:
            return AgentResponse.ok(f"📋 {client}: пока нет записей", self.name)
        return AgentResponse.ok(f"📋 {client}: {hist[:300]}", self.name)

    def _note(self, text: str) -> AgentResponse:
        if not self._current:
            return AgentResponse.ok("Сначала начни сессию.", self.name)
        note = text.replace("запиши", "").strip(" :,")
        self._current.notes += (" " if self._current.notes else "") + note
        saved = self._rag_save(self._current.client, note)
        mark = "💾" if saved else "📝"
        return AgentResponse.ok(f"{mark} Записал: {note[:60]}", self.name)

    def _finish(self) -> AgentResponse:
        if not self._current:
            return AgentResponse.ok("Нет активной сессии.", self.name)
        sess = self._current
        sess.active = False
        if sess.notes:
            self._rag_save(
                sess.client,
                f"сессия {sess.duration_min}мин. {sess.notes}"
            )
        self._current = None
        return AgentResponse.ok(
            f"✅ Сессия {sess.client} завершена. Заметок: {len(sess.notes.split())}.",
            self.name,
        )


__all__ = ["AgentMassage", "Session"]
