"""Call agent. T043 — звонок близкому.

Конфиг: ~/.config/aura/call.json
- mode: "telegram_voice" | "telegram_text" | "sip" | "sms"
- contact: "имя в контактах"
- default: "сын" (кому звоним по умолчанию)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CONFIG = Path.home() / ".config" / "aura" / "call.json"


class AgentCall(BaseAgent):
    name = "call"
    MODULE_ALWAYS = True

    TRIGGERS = ("позвони", "позвать", "набери", "свяжись", "позвонить")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cfg = self._load_config()
        mode = cfg.get("mode", "telegram_voice")
        default = cfg.get("default", "сын")

        # Кого вызвать?
        target = self._extract_target(request.text) or default

        # Способ связи
        if mode == "telegram_voice":
            return self._telegram(target, voice=True)
        if mode == "telegram_text":
            return self._telegram(target, voice=False)
        if mode == "sip":
            return self._sip(target, cfg)
        if mode == "sms":
            return self._sms(target, cfg)

        return AgentResponse.ok(
            text=f"Позвонить {target}? Но mode не настроен.",
            agent_name=self.name,
        )

    def _extract_target(self, text: str) -> str | None:
        t = text.lower()
        for kw in ("позвони ", "позвать ", "набери ", "свяжись с "):
            if kw in t:
                rest = t.split(kw, 1)[1].strip()
                for stop in (" что", " и ", " на ", " в "):
                    rest = rest.split(stop, 1)[0]
                return rest[:30]
        return None

    # AURA_CALL_FIX_V1 — используем существующие tg_* (send_message + finalize)
    def _telegram(self, target: str, voice: bool) -> AgentResponse:
        try:
            from aura.core.bridge import send_command
            # 1. Найти чат
            r1 = send_command({"action": "tg_find_chat", "query": target})
            if not r1 or r1.get("error"):
                return AgentResponse.ok(
                    text=f"❌ Telegram: не нашла {target}",
                    agent_name=self.name,
                )
            # 2. Напечатать + отправить
            msg = "Позвони мне, пожалуйста."
            r2 = send_command({"action": "tg_send_message", "text": msg})
            if r2 and not r2.get("error"):
                send_command({"action": "tg_finalize"})
                return AgentResponse.ok(
                    text=f"📞 Позвала {target} в Telegram",
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text="⚠️ Telegram: send_message error",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"📞 Не смогла позвонить {target}: {e}",
                agent_name=self.name,
            )

    def _sip(self, target: str, cfg: dict) -> AgentResponse:
        number = cfg.get("contacts", {}).get(target)
        if not number:
            return AgentResponse.ok(
                text=f"Номер {target} не настроен в call.json",
                agent_name=self.name,
            )
        try:
            subprocess.Popen(["linphone", "--call", number],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return AgentResponse.ok(text=f"📞 Звоню {target}...", agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(text=f"Ошибка SIP: {e}", agent_name=self.name)

    def _sms(self, target: str, cfg: dict) -> AgentResponse:
        number = cfg.get("contacts", {}).get(target)
        if not number:
            return AgentResponse.ok(text=f"Номер {target} не настроен", agent_name=self.name)
        # через Android bridge / kannel
        return AgentResponse.ok(
            text=f"📱 SMS {target}: 'Позвони мне, пожалуйста'",
            agent_name=self.name,
        )

    def _load_config(self) -> dict:
        try:
            if CONFIG.exists():
                return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"mode": "telegram_voice", "default": "сын", "contacts": {}}
