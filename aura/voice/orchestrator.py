"""VoiceOrchestrator — говорит и сканирует параллельно.

Пока Ирина произносит фразу (5-8 сек), в фоне летит диагностика:
ruff, pytest, git status, состояние модулей. Голос = экран загрузки.

Паттерн Licklider 1960: симбиоз вместо ожидания.
"""

from __future__ import annotations

from typing import Any, Callable

from aura.agents.speaker import AgentSpeaker
from aura.lore.persona import speak_line


class VoiceOrchestrator:
    """Собирает фразу, запускает голос, параллельно сканирует корабль."""

    def __init__(self, speaker: AgentSpeaker | None = None):
        self.speaker = speaker or AgentSpeaker()

    def speak_and_scan(
        self,
        event: str,
        scan_fn: Callable[[], Any] | None = None,
        **ctx: Any,
    ) -> Any:
        """Говорит фразу события и параллельно сканирует.

        Args:
            event: ключ из LINES (например, "fix_success").
            scan_fn: функция диагностики. Если None — просто говорит.
            **ctx: параметры для подстановки в шаблон.

        Returns:
            Результат scan_fn() или None.
        """
        line = speak_line(event, **ctx)
        self.speaker.say(line)

        result = None
        if scan_fn is not None:
            try:
                result = scan_fn()
            except Exception as e:
                result = {"error": str(e)}

        self.speaker.wait()
        return result

    def say(self, event: str, **ctx: Any) -> None:
        """Просто говорит фразу, без сканирования."""
        line = speak_line(event, **ctx)
        self.speaker.say(line)
        self.speaker.wait()
