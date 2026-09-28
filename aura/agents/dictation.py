"""DictationAgent — диктовка в файл (ADR-044 шаг 5).

Сценарий: руки заняты → «Аура, диктовка спина L4-L5» → строка в файл дня.
Файл: ~/aura_private/dictation/YYYY-MM-DD.md (append).

Стриминговый ASR (AgentListener) подключается отдельно — здесь только
API для приёма текста и управления сессией.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


DICTATION_DIR = Path.home() / "aura_private" / "dictation"


def _today_file() -> Path:
    DICTATION_DIR.mkdir(parents=True, exist_ok=True)
    return DICTATION_DIR / (datetime.now().strftime("%Y-%m-%d") + ".md")


class AgentDictation(BaseAgent):
    """Диктовка в файл дня.

    Команды:
      - «диктовка <текст>»    — append строку
      - «диктовка»            — открыть сессию (создать файл)
      - «стоп диктовка»       — закрыть сессию
      - «диктовка файл»       — показать путь к текущему файлу
    """

    name = "dictation"
    MODULE_ALWAYS = True
    KEYWORDS = ("диктовка", "записать текст", "стоп диктовк", "конец диктовк")

    def __init__(self) -> None:
        super().__init__()
        self._active = False
        self._count = 0

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.strip()
        low = text.lower()

        # «стоп диктовка»
        if "стоп" in low or "конец" in low:
            return self._stop()

        # «диктовка файл» — показать путь
        if low.rstrip().endswith("файл") or low.rstrip() == "диктовка файл":
            return AgentResponse.ok(f"📄 Файл: {_today_file()}", self.name)

        # Извлечь текст после слова «диктовка»
        payload = self._extract_payload(text)
        if payload:
            return self._append(payload)

        # «диктовка» без текста — открыть сессию
        return self._start()

    @staticmethod
    def _extract_payload(text: str) -> str:
        """Вернуть текст после 'диктовка' (или 'записать текст')."""
        low = text.lower()
        for kw in ("диктовка", "записать текст"):
            if kw in low:
                idx = low.index(kw) + len(kw)
                tail = text[idx:].strip(" :,-")
                if tail:
                    return tail
        return ""

    def _start(self) -> AgentResponse:
        f = _today_file()
        if not f.exists():
            f.write_text(
                "# Диктовка " + datetime.now().strftime("%Y-%m-%d") + chr(10) + chr(10),
                encoding="utf-8",
            )
        self._active = True
        return AgentResponse.ok(
            f"🎤 Диктовка открыта. Файл: {f.name}", self.name
        )

    def _append(self, payload: str) -> AgentResponse:
        f = _today_file()
        ts = datetime.now().strftime("%H:%M")
        line = "- [" + ts + "] " + payload + chr(10)
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(line)
        self._active = True
        self._count += 1
        return AgentResponse.ok(f"📝 +{payload[:60]}", self.name)

    def _stop(self) -> AgentResponse:
        if not self._active and self._count == 0:
            return AgentResponse.ok("Диктовка не была открыта.", self.name)
        f = _today_file()
        self._active = False
        n = self._count
        self._count = 0
        return AgentResponse.ok(
            f"✅ Диктовка закрыта. Строк: {n}. Файл: {f.name}", self.name
        )


__all__ = ["AgentDictation", "DICTATION_DIR"]
