"""Time Agent v1.0 — kernel-версия.
Первый живой орган в новом ядре. Образец для speaker и elder-care.
Наука: Actor Model + AgentBehaviour contract.
"""
import logging
from datetime import datetime

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.time")


class TimeAgent:
    name = "time"
    version = "1.0.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        # Подписываемся на запросы времени
        ctx.bus.subscribe("time.ask", self._on_time_ask)
        log.info("time agent started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        """Прямая обработка события (если кто-то вызовет)."""
        if event.topic == "time.ask":
            await self._on_time_ask(event)

    async def _on_time_ask(self, event) -> None:
        payload = get_payload(event)
        fmt = payload.get("format", "%H:%M")
        now = datetime.now().strftime(fmt)
        log.info("time.ask → %s", now)
        event_log.append("time.answer", {"time": now}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("time.answer", {"time": now})

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "time": datetime.now().strftime("%H:%M:%S"),
        }

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            self.ctx.bus.unsubscribe("time.ask", self._on_time_ask)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
