"""AT-SPI адаптер — доступ к интерфейсам Linux для незрячих."""
from __future__ import annotations
from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse

class AgentAtSpi(MicroAgent):
    """Доступ к AT-SPI (accessibility) для чтения интерфейсов."""
    KEYWORDS = ("прочитай экран", "что на экране", "озвучь")
    
    def __init__(self):
        super().__init__("at_spi", "AT-SPI адаптер")
        self.ready = False
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi
            self.Atspi = Atspi
            self.ready = True
        except Exception:
            pass
    
    def can_handle(self, request: AgentRequest) -> bool:
        return any(kw in request.text.lower() for kw in self.KEYWORDS)
    
    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.ready:
            return AgentResponse.ok("AT-SPI не установлен", self.name)
        return AgentResponse.ok("AT-SPI: готов", self.name)

__all__ = ["AgentAtSpi"]
