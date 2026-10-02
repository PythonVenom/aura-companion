"""AgentFocus — управление режимом фокуса (ADR-097)."""
from __future__ import annotations
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core import focus


class AgentFocus(BaseAgent):
    name = "focus_mode"
    MODULE_ALWAYS = True
    ON_KEYWORDS = ("фокус", "не отвлекай", "не отвлекать",
                   "режим работы", "тишина на")
    OFF_KEYWORDS = ("выключи фокус", "хватит фокуса", "отвлекай",
                    "фокус выкл")
    STATUS_KEYWORDS = ("фокус активен", "фокус статус", "сколько фокуса")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        all_kw = self.ON_KEYWORDS + self.OFF_KEYWORDS + self.STATUS_KEYWORDS
        return any(kw in text for kw in all_kw)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        if any(kw in text for kw in self.OFF_KEYWORDS):
            focus.disable()
            return AgentResponse.ok("Фокус выключен", self.name)
        if any(kw in text for kw in self.STATUS_KEYWORDS):
            if focus.is_active():
                return AgentResponse.ok(
                    f"Фокус активен, осталось {int(focus.remaining() // 60)} мин",
                    self.name,
                )
            return AgentResponse.ok("Фокус не активен", self.name)
        focus.enable(seconds=3600)
        return AgentResponse.ok(
            "Фокус 60 минут. Не отвлекаю. Скажи 'выключи фокус' если что",
            self.name,
        )


__all__ = ["AgentFocus"]
