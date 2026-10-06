"""CEC TV adapter. T031 — управление ТВ через HDMI-CEC.

Наука: CEC (Consumer Electronics Control) — протокол HDMI.
Работает на большинстве современных ТВ через libcec.
Утилита: cec-client (пакет cec-utils).
"""
from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


CEC_BIN = "cec-client"


class AgentCEC(BaseAgent):
    name = "cec"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "включи телевизор", "выключи телевизор", "включи тв", "выключи тв",
        "громче тв", "тише тв", "переключи канал", "телевизор",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        if not any(kw in t for kw in self.TRIGGERS):
            return False
        # Проверка наличия cec-client
        import shutil
        return shutil.which(CEC_BIN) is not None

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "включи" in t:
            return self._run("on 0", "Включаю ТВ")
        if "выключи" in t:
            return self._run("standby 0", "Выключаю ТВ")
        if "громче" in t:
            return self._run("volup", "Громче")
        if "тише" in t:
            return self._run("voldown", "Тише")
        if "канал" in t:
            return self._run("channelup", "Следующий канал")

        return AgentResponse.ok(
            text="CEC готов. Скажи: 'включи/выключи ТВ', 'громче/тише'.",
            agent_name=self.name,
        )

    def _run(self, cmd: str, reply: str) -> AgentResponse:
        try:
            subprocess.run(
                ["bash", "-c", f"echo '{cmd}' | {CEC_BIN} -s -d 1"],
                timeout=3, capture_output=True,
            )
            return AgentResponse.ok(text=f"📺 {reply}", agent_name=self.name)
        except Exception as e:
            return AgentResponse.ok(
                text=f"⚠️ CEC ошибка: {e}",
                agent_name=self.name,
            )
