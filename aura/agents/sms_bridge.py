"""T046 SMS bridge через KDE Connect D-Bus.

Наука:
- KDE Connect daemon: org.kde.kdeconnect
- Plugin "sms": интерфейс org.kde.kdeconnect.device.sms
- Fallback: ModemManager (org.freedesktop.ModemManager1) если 4G-модем
"""
from __future__ import annotations

import shutil
import subprocess

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


class AgentSMS(MicroAgent):
    name = "sms"

    TRIGGERS = ("смс", "sms", "отправь смс", "прочитай смс")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if not shutil.which("kdeconnect-cli"):
            return AgentResponse.ok(
                text="⚠️ Нет kdeconnect-cli. Поставь: sudo pacman -S kdeconnect",
                agent_name=self.name,
            )
        if "устройств" in t or "список" in t or "статус" in t:
            return self._devices()
        if "отправь" in t or "напиши" in t:
            return self._send(request.text)
        return AgentResponse.ok(
            text="SMS. Скажи: 'отправь смс <номер> <текст>' или 'устройства'.",
            agent_name=self.name,
        )

    def _devices(self) -> AgentResponse:
        try:
            r = subprocess.run(
                ["kdeconnect-cli", "-l"],
                capture_output=True, text=True, timeout=5,
            )
            out = (r.stdout or "").strip()
            if not out:
                return AgentResponse.ok(
                    text="📱 KDE Connect: нет сопряжённых устройств.",
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text=f"📱 KDE Connect:\n{out[:400]}",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(text=f"⚠️ SMS: {e}", agent_name=self.name)

    def _send(self, text: str) -> AgentResponse:
        t = text.lower()
        for kw in ("отправь смс ", "напиши смс "):
            if kw in t:
                rest = text[len(kw):].strip()
                parts = rest.split(" ", 1)
                if len(parts) < 2:
                    return AgentResponse.ok(
                        text="Формат: 'отправь смс <номер> <текст>'",
                        agent_name=self.name,
                    )
                number, msg = parts[0], parts[1]
                try:
                    # Найти первое сопряжённое устройство
                    r = subprocess.run(
                        ["kdeconnect-cli", "-l", "--id-only"],
                        capture_output=True, text=True, timeout=5,
                    )
                    ids = (r.stdout or "").strip().splitlines()
                    if not ids:
                        return AgentResponse.ok(
                            text="📱 Нет сопряжённых устройств. Запусти KDE Connect на телефоне.",
                            agent_name=self.name,
                        )
                    dev_id = ids[0].strip()
                    r2 = subprocess.run(
                        ["kdeconnect-cli", "--device", dev_id,
                         "--send-sms", msg, "--destination", number],
                        capture_output=True, text=True, timeout=10,
                    )
                    if r2.returncode == 0:
                        return AgentResponse.ok(
                            text=f"📱 SMS → {number}: «{msg[:40]}»",
                            agent_name=self.name,
                        )
                    return AgentResponse.ok(
                        text=f"⚠️ SMS send: {r2.stderr.strip()[:100]}",
                        agent_name=self.name,
                    )
                except Exception as e:
                    return AgentResponse.ok(
                        text=f"⚠️ SMS: {e}", agent_name=self.name,
                    )
        return AgentResponse.ok(
            text="Формат: 'отправь смс <номер> <текст>'",
            agent_name=self.name,
        )
