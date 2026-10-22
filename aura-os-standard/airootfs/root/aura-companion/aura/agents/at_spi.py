"""AT-SPI адаптер — accessibility для незрячих."""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentAtSpi(MicroAgent):
    KEYWORDS = ("прочитай экран", "что на экране", "озвучь",
                "что в окне", "найти кнопку", "нажми на")

    def __init__(self):
        super().__init__("at_spi", "AT-SPI адаптер")
        self.ready = False
        self.Atspi = None
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi
            self.Atspi = Atspi
            self.ready = True
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.at_spi').debug(
                'at_spi error: %s', e)

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        if not self.ready:
            return AgentResponse.ok(
                "AT-SPI не установлен: sudo pacman -S at-spi2-core python-gobject",
                self.name,
            )
        text = request.text.lower()
        if "прочитай" in text or "что на экране" in text:
            return AgentResponse.ok(self._read_focused(), self.name)
        if "кнопку" in text:
            return AgentResponse.ok(self._list_buttons(), self.name)
        return AgentResponse.ok("AT-SPI: команда не распознана", self.name)

    def _read_focused(self) -> str:
        try:
            desktop = self.Atspi.get_desktop(0)
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app is None:
                    continue
                for j in range(app.get_child_count()):
                    win = app.get_child_at_index(j)
                    if win and win.get_name():
                        return f"📖 {win.get_name()}"
            return "📖 Пусто"
        except Exception as e:
            return f"❌ AT-SPI: {e}"

    def _list_buttons(self) -> str:
        try:
            desktop = self.Atspi.get_desktop(0)
            buttons = []
            for i in range(desktop.get_child_count()):
                app = desktop.get_child_at_index(i)
                if app is None:
                    continue
                for j in range(app.get_child_count()):
                    win = app.get_child_at_index(j)
                    if win is None:
                        continue
                    for k in range(min(win.get_child_count(), 30)):
                        ch = win.get_child_at_index(k)
                        if ch is None:
                            continue
                        if "button" in (ch.get_role_name() or "").lower():
                            n = ch.get_name() or ""
                            if n:
                                buttons.append(n[:40])
                                if len(buttons) >= 10:
                                    break
            return "🔘 " + (", ".join(buttons) if buttons else "нет")
        except Exception as e:
            return f"❌ AT-SPI: {e}"


__all__ = ["AgentAtSpi"]
