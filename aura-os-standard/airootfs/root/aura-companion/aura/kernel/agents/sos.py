"""SOS Agent v1.1 — kernel-адаптер над AgentSOS.
Разрываем прямую связь sos → telegram. Теперь: sos.trigger → legacy → sos.answer.
Наука: Adapter Pattern + Actor Model.
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.sos")


class SOSAgent:
    name = "sos"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.sos import AgentSOS
        self._legacy = AgentSOS()
        ctx.bus.subscribe("sos.trigger", self._on_trigger)
        log.info("sos adapter started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentSOS"},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_trigger(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "помогите")
        from aura.core.protocol import AgentRequest
        try:
            req = AgentRequest(text=text, user_id="batya", source="kernel")
            resp = await self._legacy.handle(req)
            out = resp.text if resp else "SOS: нет ответа"
            event_log.append("sos.triggered",
                             {"text": text[:80], "result": out[:200]},
                             src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("sos.answer", {"text": out})
        except Exception as e:
            log.exception("sos failed: %s", e)
            event_log.append("sos.error", {"error": str(e)}, src=self.name)
            if self.ctx:
                await self.ctx.bus.publish("sos.answer",
                                           {"text": f"SOS ошибка: {e}"})

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "legacy": self._legacy is not None,
        }

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for topic in ("sos.trigger",):
                for h in list(self.ctx.bus._subs.get(topic, [])):
                    self.ctx.bus.unsubscribe(topic, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
