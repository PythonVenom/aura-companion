"""WhatsApp agent. T041 — отправка/чтение через Firefox bridge.

content_whatsapp.js уже готов в extension. Агент — тонкая обёртка.
"""
from __future__ import annotations

from aura.core.bridge import error_text, send_command
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentWhatsApp(BaseAgent):
    name = "whatsapp"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "whatsapp", "ватсап", "вацап",
        "напиши в whatsapp", "отправь в whatsapp",
        "прочитай whatsapp",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "прочитай" in t or "что пишут" in t:
            return self._read_last()
        if "найди" in t or "открой чат" in t:
            return self._find(request.text)
        if "напиши" in t or "отправь" in t:
            return self._send(request.text)
        if "чаты" in t or "список" in t:
            return self._list()
        return AgentResponse.ok(
            text="WhatsApp готов. Скажи: 'напиши в whatsapp <кому> <что>'.",
            agent_name=self.name,
        )

    def _read_last(self) -> AgentResponse:
        r = send_command({"action": "wa_read_last"})
        if not r or r.get("error"):
            return AgentResponse.ok(error_text(r), agent_name=self.name)
        msg = (r.get("data") or {}).get("text", "")
        return AgentResponse.ok(
            text=f"📱 WhatsApp: {msg[:200]}" if msg else "📱 WhatsApp: пусто",
            agent_name=self.name,
        )

    def _list(self) -> AgentResponse:
        r = send_command({"action": "wa_list_chats"})
        if not r or r.get("error"):
            return AgentResponse.ok(error_text(r), agent_name=self.name)
        chats = (r.get("data") or [])
        if not chats:
            return AgentResponse.ok(text="📱 WhatsApp: нет чатов", agent_name=self.name)
        lines = ["📱 WhatsApp:"] + [
            f"  {i}. {c.get('name','?')[:40]}" for i, c in enumerate(chats[:10], 1)
        ]
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    def _find(self, text: str) -> AgentResponse:
        for kw in ("найди в whatsapp ", "открой чат "):
            if kw in text.lower():
                q = text.lower().split(kw, 1)[1].strip()[:30]
                r = send_command({"action": "wa_find_chat", "query": q})
                if r and not r.get("error"):
                    return AgentResponse.ok(
                        text=f"📱 WhatsApp: {q}", agent_name=self.name)
                return AgentResponse.ok(
                    text=f"❌ WhatsApp: {q} не найден", agent_name=self.name)
        return AgentResponse.ok(
            text="Скажи: 'найди в whatsapp <имя>'", agent_name=self.name)

    def _send(self, text: str) -> AgentResponse:
        t = text.lower()
        for kw in ("напиши в whatsapp ", "отправь в whatsapp ",
                   "напиши в ватсап ", "напиши в вацап "):
            if kw in t:
                rest = text[len(kw):]
                parts = rest.split(" ", 1)
                if len(parts) < 2:
                    return AgentResponse.ok(
                        text="Скажи: 'напиши в whatsapp <кому> <что>'",
                        agent_name=self.name,
                    )
                target, msg = parts[0], parts[1]
                send_command({"action": "wa_find_chat", "query": target})
                r = send_command({"action": "wa_send_message", "text": msg})
                if r and not r.get("error"):
                    send_command({"action": "wa_send_finalize"})
                    return AgentResponse.ok(
                        text=f"📱 WhatsApp {target}: «{msg[:40]}»",
                        agent_name=self.name,
                    )
                return AgentResponse.ok(
                    text="⚠️ WhatsApp send error", agent_name=self.name)
        return AgentResponse.ok(
            text="Скажи: 'напиши в whatsapp <кому> <что>'",
            agent_name=self.name)
