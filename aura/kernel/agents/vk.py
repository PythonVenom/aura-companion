"""VK Agent — управление через VK API."""
import logging
import os

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.vk")


class VKAgent:
    name = "vk"
    version = "0.1.0"

    def __init__(self, token: str = ""):
        self.ctx = None
        self._running = False
        self.token = token or os.environ.get("AURA_VK_TOKEN", "")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("vk.send", self._on_send)
        log.info("vk started (token=%s)", "yes" if self.token else "no")
        event_log.append("agent.started",
                         {"name": self.name, "token": bool(self.token)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_send(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        peer_id = p.get("peer_id", "")
        if not text or not peer_id or not self.token:
            return
        try:
            import requests
            r = requests.post(
                "https://api.vk.com/method/messages.send",
                data={"peer_id": peer_id, "message": text,
                      "access_token": self.token, "v": "5.199"},
                timeout=5,
            )
            event_log.append("vk.sent",
                             {"status": r.status_code}, src=self.name)
        except Exception as e:
            log.warning("vk send failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "token": bool(self.token)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("vk.send", [])):
                self.ctx.bus.unsubscribe("vk.send", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
