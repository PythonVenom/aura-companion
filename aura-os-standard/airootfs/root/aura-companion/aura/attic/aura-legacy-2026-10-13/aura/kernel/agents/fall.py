"""Fall Agent v1.1 — kernel-адаптер над AgentFall.
Разрываем прямую связь fall → sos. Теперь: fall.detected → шина.
Наука: Adapter Pattern + Actor Model (Hewitt 1973).
"""
import logging

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.fall")


class FallAgent:
    name = "fall"
    version = "1.1.0"

    def __init__(self):
        self.ctx: AgentContext | None = None
        self._running = False
        self._legacy = None

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        from aura.agents.fall import AgentFall
        self._legacy = AgentFall()
        ctx.bus.subscribe("fall.trigger", self._on_trigger)
        ctx.bus.subscribe("fall.check", self._on_check)
        log.info("fall adapter started")
        event_log.append("agent.started",
                         {"name": self.name, "v": self.version,
                          "legacy": "AgentFall"},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_trigger(self, event) -> None:
        """Триггер 'упал' → проверяем legacy.can_handle → публикуем fall.detected.
        НЕ вызываем legacy.handle — чтобы разорвать прямую связь с sos.
        """
        p = get_payload(event)
        text = p.get("text", "")
        if not text:
            return
        from aura.core.protocol import AgentRequest
        req = AgentRequest(text=text, user_id="batya", source="kernel")
        if not self._legacy.can_handle(req):
            log.debug("fall: not a fall trigger: %s", text)
            return
        # Логируем падение через legacy (публичный побочный эффект)
        try:
            self._legacy._log_fall(text)
        except Exception as e:
            log.warning("fall log failed: %s", e)
        event_log.append("fall.detected",
                         {"text": text[:100]}, src=self.name)
        if self.ctx:
            await self.ctx.bus.publish("fall.detected",
                                       {"text": text, "source": "trigger"})

    async def _on_check(self, event) -> None:
        """Проверка состояния (для health)."""
        event_log.append("fall.check", {}, src=self.name)

    async def health(self) -> dict:
        return {
            "status": "ok" if self._running else "stopped",
            "version": self.version,
            "legacy": self._legacy is not None,
        }

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for topic in ("fall.trigger", "fall.check"):
                for h in list(self.ctx.bus._subs.get(topic, [])):
                    self.ctx.bus.unsubscribe(topic, h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
