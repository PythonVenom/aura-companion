"""Telegram Agent — управление Aura через бота."""
import logging
import os

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.telegram")


class TelegramAgent:
    name = "telegram"
    version = "0.1.0"

    def __init__(self, token: str = ""):
        self.ctx = None
        self._running = False
        self.token = token or os.environ.get("AURA_TG_TOKEN", "")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("telegram.send", self._on_send)
        log.info("telegram started (token=%s)", "yes" if self.token else "no")
        event_log.append("agent.started",
                         {"name": self.name, "token": bool(self.token)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_send(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        chat_id = p.get("chat_id", "")
        if not text or not chat_id:
            return
        if not self.token:
            event_log.append("telegram.no_token", {"text": text[:40]}, src=self.name)
            return
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
            event_log.append("telegram.sent", {"status": r.status_code}, src=self.name)
        except Exception as e:
            log.warning("telegram send failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "token": bool(self.token)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("telegram.send", [])):
                self.ctx.bus.unsubscribe("telegram.send", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
