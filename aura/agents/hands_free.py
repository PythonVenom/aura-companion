"""AgentHandsFree — управление режимом без активации (ADR-095)."""
from __future__ import annotations

from aura.core import hands_free
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentHandsFree(BaseAgent):
    name = "handsfree"
    MODULE_ALWAYS = True
    ON_KEYWORDS = ("слушай без активации", "слушай без аура",
                   "режим свободных рук", "handsfree on",
                   "режим слушания", "не требуй активации")
    OFF_KEYWORDS = ("выключи слушание", "handsfree off",
                    "хватит слушать", "режим свободных рук выкл")
    STATUS_KEYWORDS = ("режим слушания?", "handsfree status",
                       "сколько осталось слушания")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        all_kw = self.ON_KEYWORDS + self.OFF_KEYWORDS + self.STATUS_KEYWORDS
        return any(kw in text for kw in all_kw)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        if any(kw in text for kw in self.OFF_KEYWORDS):
            hands_free.disable()
            return AgentResponse.ok("Режим свободных рук выключен", self.name)
        if any(kw in text for kw in self.STATUS_KEYWORDS):
            if hands_free.is_active():
                return AgentResponse.ok(
                    f"Слушаю, осталось {int(hands_free.remaining())} сек",
                    self.name,
                )
            return AgentResponse.ok("Не слушаю без активации", self.name)
        # Включение
        hands_free.enable(seconds=300)
        return AgentResponse.ok(
            "Слушаю без активации 5 минут. Скажи 'хватит слушать' чтобы выключить",
            self.name,
        )


__all__ = ["AgentHandsFree"]
