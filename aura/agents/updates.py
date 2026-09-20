"""
Агент обновлений системы (AgentUpdates).

Проверяет доступные обновления через `checkupdates`.

Мигрирован из agents/update_checker.py (монолит).
Изменения при миграции:
- Контракт BaseAgent: can_handle / handle
- Имя: "updates" (как в монолите — в словаре AuraCore был 'updates')
- Логика НЕ менялась

Наука:
- Агент не знает про оркестратор
- Никаких import __main__
- Опасные вызовы (subprocess) — только в handle, тесты на моках
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentUpdates(BaseAgent):
    """
    Проверка обновлений системы.

    Обрабатывает запросы:
    - "проверь обновления"
    - "есть обновления"
    - "обновления"
    """

    name = "updates"

    # Ключевые слова для can_handle
    KEYWORDS = (
        "проверь обновления",
        "проверить обновления",
        "есть обновления",
        "доступные обновления",
        "обновления системы",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        try:
            result = subprocess.run(
                "checkupdates 2>/dev/null | wc -l",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            count = result.stdout.strip()
            if count and int(count) > 0:
                return AgentResponse.ok(
                    text=f"⚠️ Доступно {count} обновлений",
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text="✅ Система обновлена",
                agent_name=self.name,
            )
        except Exception:
            return AgentResponse.ok(
                text="❌ Не удалось проверить обновления",
                agent_name=self.name,
            )


__all__ = ["AgentUpdates"]
