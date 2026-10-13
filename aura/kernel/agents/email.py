"""Email Agent — IMAP/SMTP для elder-care."""
import logging
import os
import smtplib
from email.mime.text import MIMEText

from aura.contracts.agent import AgentContext, Event
from aura.kernel.log import event_log
from aura.kernel.payload import get_payload

log = logging.getLogger("aura.agents.email")


class EmailAgent:
    name = "email"
    version = "0.1.0"

    def __init__(self):
        self.ctx = None
        self._running = False
        self.smtp_host = os.environ.get("AURA_SMTP_HOST", "")
        self.smtp_port = int(os.environ.get("AURA_SMTP_PORT", "587"))
        self.user = os.environ.get("AURA_EMAIL_USER", "")
        self.password = os.environ.get("AURA_EMAIL_PASS", "")

    async def start(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self._running = True
        ctx.bus.subscribe("email.send", self._on_send)
        log.info("email started (smtp=%s)", self.smtp_host or "no")
        event_log.append("agent.started",
                         {"name": self.name,
                          "smtp": bool(self.smtp_host)},
                         src=self.name)

    async def handle(self, event: Event) -> None:
        pass

    async def _on_send(self, event) -> None:
        p = get_payload(event)
        text = p.get("text", "")
        to = p.get("to", "")
        subject = p.get("subject", "Aura")
        if not text or not to or not self.smtp_host:
            return
        try:
            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = self.user
            msg["To"] = to
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
                s.starttls()
                s.login(self.user, self.password)
                s.send_message(msg)
            event_log.append("email.sent", {"to": to}, src=self.name)
        except Exception as e:
            log.warning("email send failed: %s", e)

    async def health(self) -> dict:
        return {"status": "ok" if self._running else "stopped",
                "smtp": bool(self.smtp_host)}

    async def stop(self) -> None:
        self._running = False
        if self.ctx:
            for h in list(self.ctx.bus._subs.get("email.send", [])):
                self.ctx.bus.unsubscribe("email.send", h)
        event_log.append("agent.stopped", {"name": self.name}, src=self.name)
