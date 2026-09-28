"""MassageSessionAgent — сессия массажа (ADR-044).

Beachhead = массажист = автор. Первый агент для Founder-First.
JTBD: таймер + RAG по клиенту + диктовка + отчёт.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CLIENTS_DIR = Path.home() / ".config" / "aura" / "massage_clients"


def _client_file(client: str) -> Path:
    CLIENTS_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in client if c.isalnum() or c in "_-").lower()
    return CLIENTS_DIR / f"{safe}.md"


def _client_append(client: str, line: str) -> None:
    f = _client_file(client)
    with open(f, "a", encoding="utf-8") as fp:
        fp.write(line + chr(10))


def _client_read(client: str, tail: int = 10) -> str:
    f = _client_file(client)
    if not f.exists():
        return ""
    lines = f.read_text(encoding="utf-8").splitlines()
    return chr(10).join(lines[-tail:])


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
        """Сохранить заметку в файл клиента (Bug C: не в RAG)."""
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            _client_append(client, f"- [{ts}] {text}")
            return True
        except Exception:
            return False

    def _rag_read(self, client: str) -> str:
        """Прочитать последние записи клиента (Bug C)."""
        try:
            content = _client_read(client, tail=5)
            return content
        except Exception as e:
            return f"Ошибка: {e}"

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
        # Bug F: ASR слышит "тс" вместо "Тест" + "тридцать" вместо "30"
        from aura.agents.time_agent import _parse_int
        # Ищем "сессия <имя>" затем число (цифрой или словом)
        m = re.search(r"(?:сессия|массаж)\s+([а-яa-z_]+)", text)
        if not m:
            return AgentResponse.ok(
                "Скажи: «сессия Иванов 50 минут»", self.name
            )
        client = m.group(1).title()
        n = _parse_int(text)
        if not n:
            return AgentResponse.ok(
                f"Не услышала длительность. Скажи: «сессия {client} 50»", self.name
            )
        duration = n
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

    def _export_md(self, client: str) -> Path:
        """Экспорт истории клиента в отдельный MD."""
        from aura.agents.massage import _client_file
        src = _client_file(client)
        if not src.exists():
            return src
        out_dir = Path.home() / "aura_private" / "massage_reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        out = out_dir / f"{client}_{ts}.md"
        header = "# Сессии: " + client + chr(10) + chr(10)
        out.write_text(header + src.read_text(encoding="utf-8"), encoding="utf-8")
        return out

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
