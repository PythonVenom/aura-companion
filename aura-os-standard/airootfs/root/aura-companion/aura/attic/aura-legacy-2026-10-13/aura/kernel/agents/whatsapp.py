"""WhatsApp Agent — через whatsapp-web или Cloud API."""
import logging
import os

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.whatsapp")


class WhatsAppAgent:
    name = "whatsapp"
    version = "0.1.0"

    def __init__(self, token: str = ""):
        self.ctx = None
        self._running = False
        self.token = token or os.environ.get("AURA_WA_TOKEN", "")
        self.phone_id = os.environ.get("AURA_WA_PHONE_ID", "")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("wa.send", self._on_send)
        log.info("whatsapp started (token=%s)", "yes" if self.token else "no")
        event_log.append("agent.started",
                         {"name": self.name, "token": bool(self.token)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_send(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        to = p.get("to", "")
        if not text or not to or not self.token:
            return
        try:
            import requests
            url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                json={"messaging_product": "whatsapp",
                      "to": to, "type": "text",
                      "text": {"body": text}},
                timeout=5,
            )
            event_log.append("wa.sent",
                             {"status": r.status_code}, src=self.name)
        except Exception as e:
            log.warning("whatsapp send failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "token": bool(self.token)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("wa.send", [])):
                self.ctx.bus.unsubscribe("wa.send", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
