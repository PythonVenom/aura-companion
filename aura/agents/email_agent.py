"""Email agent. T044 — отправка/чтение email.

Наука: RFC 5321 (SMTP), RFC 3501 (IMAP4rev1), RFC 2822 (msg format).
Пароль: keyring (freedesktop Secret Service) — не в plaintext.
"""
from __future__ import annotations
import smtplib
import imaplib
import email as emaillib
from email.message import EmailMessage
from email.header import decode_header
from email.utils import parseaddr

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


KEYRING_SERVICE = "aura-email"


class AgentEmail(MicroAgent):
    name = "email"

    TRIGGERS = ("почта", "email", "письмо", "входящие",
                "напиши письмо", "отправь письмо", "проверь почту")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "отправь" in t or "напиши" in t:
            return self._send(request.text)
        if "прочитай" in t or "проверь" in t or "входящие" in t:
            return self._read()
        return AgentResponse.ok(
            text="Email. Скажи: 'отправь письмо <кому> <текст>' или 'проверь почту'.",
            agent_name=self.name,
        )

    def _creds(self):
        try:
            import keyring
            addr = keyring.get_password(KEYRING_SERVICE, "address")
            pwd = keyring.get_password(KEYRING_SERVICE, "password")
            if addr and pwd:
                return addr, pwd
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.email_agent').debug(
                'email_agent error: %s', e)
        return None

    def _send(self, text: str) -> AgentResponse:
        creds = self._creds()
        if not creds:
            return AgentResponse.ok(
                text="Email: нет кредов. keyring set aura-email address / password.",
                agent_name=self.name,
            )
        addr, pwd = creds
        rest = text.lower().split("письмо", 1)[-1].strip()
        parts = rest.split(" ", 1) if rest else []
        if len(parts) < 2 or "@" not in parts[0]:
            return AgentResponse.ok(
                text="Формат: 'отправь письмо <email> <текст>'",
                agent_name=self.name,
            )
        to_addr, body = parts[0], parts[1]
        try:
            msg = EmailMessage()
            msg["From"] = addr
            msg["To"] = to_addr
            msg["Subject"] = "Сообщение от Aura"
            msg.set_content(body)
            host = f"smtp.{addr.split('@')[1]}"
            with smtplib.SMTP_SSL(host, 465, timeout=15) as s:
                s.login(addr, pwd)
                s.send_message(msg)
            return AgentResponse.ok(text=f"📧 Отправлено: {to_addr}", agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(text=f"⚠️ Email send: {e}", agent_name=self.name)

    def _read(self) -> AgentResponse:
        creds = self._creds()
        if not creds:
            return AgentResponse.ok(text="Email: нет кредов.", agent_name=self.name)
        addr, pwd = creds
        try:
            host = f"imap.{addr.split('@')[1]}"
            with imaplib.IMAP4_SSL(host, 993) as m:
                m.login(addr, pwd)
                m.select("INBOX")
                typ, data = m.search(None, "UNSEEN")
                ids = data[0].split() if data and data[0] else []
                if not ids:
                    return AgentResponse.ok(text="📧 Непрочитанных нет.", agent_name=self.name)
                lines = [f"📧 Непрочитанных: {len(ids)}"]
                for i in ids[-5:]:
                    typ, d = m.fetch(i, "(RFC822.HEADER)")
                    if not d or not d[0]:
                        continue
                    msg = emaillib.message_from_bytes(d[0][1])
                    subj_raw = msg.get("Subject", "?")
                    subj, enc = decode_header(subj_raw)[0]
                    if isinstance(subj, bytes):
                        subj = subj.decode(enc or "utf-8", errors="replace")
                    frm = parseaddr(msg.get("From", "?"))[1]
                    lines.append(f"  • {frm[:25]}: {subj[:50]}")
                return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(text=f"⚠️ Email read: {e}", agent_name=self.name)
