"""Car/Bike Agent — OBD-II через ELM327.
Наука: OBD-II (SAE J1979), Disruptive Innovation (Christensen).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.obd")


class OBDAgent:
    name = "obd"
    version = "0.1.0"

    def __init__(self, port: str = "/dev/ttyUSB0"):
        self.ctx = None
        self._running = False
        self.port = port
        self._connected = False

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx  # type: ignore[assignment]
        self._running = True
        ctx.bus.subscribe("obd.status", self._on_status)
        ctx.bus.subscribe("obd.dtc", self._on_dtc)
        ctx.bus.subscribe("obd.fuel", self._on_fuel)
        log.info("obd started (port=%s)", self.port)
        event_log.append("agent.started",
                         {"name": self.name, "port": self.port},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_status(self, event) -> None:
        text = "Машина: OBD-II не подключён. Подключи ELM327."
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def _on_dtc(self, event) -> None:
        """TODO: python-OBD читает коды P0xxx."""
        text = "Ошибки: не могу прочитать без адаптера."
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def _on_fuel(self, event) -> None:
        text = "Топливо: нет данных."
        if self.ctx:
            await self.ctx.bus.publish("speaker.say", {"text": text})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "port": self.port, "connected": self._connected}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("obd.status", "obd.dtc", "obd.fuel"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
