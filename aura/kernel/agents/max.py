"""MAX Agent — российский мессенджер (max.ru)."""
import logging
import os

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.max")


class MaxAgent:
    name = "max"
    version = "0.1.0"

    def __init__(self, token: str = ""):
        self.ctx = None
        self._running = False
        self.token = token or os.environ.get("AURA_MAX_TOKEN", "")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx  # type: ignore[assignment]
        self._running = True
        ctx.bus.subscribe("max.send", self._on_send)
        log.info("max started (token=%s)", "yes" if self.token else "no")
        event_log.append("agent.started",
                         {"name": self.name, "token": bool(self.token)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_send(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        if not text or not self.token:
            return
        # TODO: MAX API endpoint (уточнить у max.ru)
        log.info("max: %s", text[:60])
        event_log.append("max.sent", {"text": text[:60]}, src=self.name)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "token": bool(self.token)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("max.send", [])):
                self.ctx.bus.unsubscribe("max.send", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
