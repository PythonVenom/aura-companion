"""Stop Control — «Аура стоп» и «Аура продолжи».
Наука: Push-to-stop, Emergency Protocol.
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log

log = logging.getLogger("aura.agents.stop_control")


class StopControlAgent:
    name = "stop_control"
    version = "1.0.0"

    def __init__(self):
        self.ctx = None
        self._running = False

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("stop.speaking", self._on_stop)
        ctx.bus.subscribe("resume.audio", self._on_resume)
        log.info("stop_control started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_stop(self, event) -> None:
        """«Аура стоп» — прекратить говорить + duck отменить."""
        log.info("STOP: прекращаю говорить")
        event_log.append("stop.triggered", {}, src=self.name)
        if self.ctx:
            # 1. Остановить speaker
            await self.ctx.bus.publish("speaker.stop", {})
            # 2. Снять ducking (вернуть музыку)
            await self.ctx.bus.publish("ducker.resume", {})
            # 3. Подтвердить
            await self.ctx.bus.publish("speaker.say", {"text": "Стоп."})

    async def _on_resume(self, event) -> None:
        """«Аура продолжи» — вернуть музыку."""
        log.info("RESUME: возвращаю звук")
        event_log.append("resume.triggered", {}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("ducker.resume", {})
            await self.ctx.bus.publish("speaker.say", {"text": "Продолжаю."})

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "version": self.version}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for t in ("stop.speaking", "resume.audio"):
                for h in list(self.ctx.bus._subs.get(t, [])):
                    self.ctx.bus.unsubscribe(t, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
