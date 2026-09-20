"""
Агент функций (AgentFunctions).

Возвращает список доступных функций Ауры.

Мигрирован из agents/functions.py (монолит).
Изменения при миграции:
- Контракт BaseAgent: can_handle / handle
- Логика НЕ менялась — статический текст
- Текст устарел (там «сделай скриншот», «покажи память» — этих
  функций в модуле нет). Обновление — отдельная задача.

Наука:
- Агент не знает про оркестратор
- Никаких import __main__
"""

from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentFunctions(BaseAgent):
    """
    Список функций Ауры.

    Обрабатывает запросы:
    - "какие есть функции"
    - "что ты умеешь"
    - "список функций"
    - "покажи функции"
    - "что ты можешь"
    """

    name = "functions"

    # Ключевые слова для can_handle
    KEYWORDS = (
        "какие есть функции",
        "какие функции",
        "что ты умеешь",
        "что ты можешь",
        "список функций",
        "покажи функции",
        "твои функции",
    )

    # Текст — как в монолите, не меняем (устаревший, отдельная задача)
    FUNCTIONS_TEXT = (
        "Доступные функции:\n"
        "1. Время — скажи 'сколько времени'\n"
        "2. Обновления — скажи 'проверь обновления'\n"
        "3. Обновить систему — скажи 'обнови систему'\n"
        "4. Поиск в интернете — скажи 'найди [запрос]'\n"
        "5. Открыть приложение — скажи 'открой браузер'\n"
        "6. Скриншот — скажи 'сделай скриншот'\n"
        "7. VK Музыка — скажи 'включи музыку'\n"
        "8. Память и контекст — скажи 'покажи память'"
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.ok(
            text=self.FUNCTIONS_TEXT,
            agent_name=self.name,
        )


__all__ = ["AgentFunctions"]
