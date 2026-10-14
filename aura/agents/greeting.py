"""AgentGreeting — приветствия и smalltalk для elder-care.

Без LLM. Фиксированные фразы. Всегда работает.
"""
from __future__ import annotations

from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentGreeting(BaseAgent):
    """Приветствия, ответы на smalltalk — elder-care must-have."""

    name = "greeting"
    MODULE_NAME = "greeting"

    GREETINGS = (
        "привет", "здравствуй", "здравствуйте", "доброе утро",
        "добрый день", "добрый вечер", "доброй ночи", "аура привет",
    )
    HOW_ARE_YOU = (
        "как дела", "как ты", "как жизнь", "как здоровье",
        "как ты себя", "как самочувствие",
    )
    THANKS = ("спасибо", "благодарю", "спс")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower().strip()
        if not t:
            return False
        # Не ловим если есть ключевое слово другого агента
        skip = ("таблетк", "лекарств", "позвони", "упал", "плохо",
                "напомни", "запиши", "врач", "час", "число", "погода")
        if any(s in t for s in skip):
            return False
        return any(g in t for g in self.GREETINGS + self.HOW_ARE_YOU + self.THANKS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        from aura.lore.persona import speak_line
        t = request.text.lower()

        # Спасибо
        if any(w in t for w in self.THANKS):
            return AgentResponse.ok(
                text=speak_line("how_are_you"),
                agent_name=self.name,
            )

        # Как дела
        if any(w in t for w in self.HOW_ARE_YOU):
            return AgentResponse.ok(
                text=speak_line("how_are_you"),
                agent_name=self.name,
            )

        # Приветствие — по времени суток
        hour = datetime.now().hour
        if 5 <= hour < 12:
            key = "morning"
        elif 12 <= hour < 18:
            key = "day"
        elif 18 <= hour < 23:
            key = "evening"
        else:
            key = "night"

        # afternoon_greeting может не быть — fallback на evening
        try:
            text = speak_line(key)
        except Exception:
            text = speak_line("morning")

        return AgentResponse.ok(text=text, agent_name=self.name)
