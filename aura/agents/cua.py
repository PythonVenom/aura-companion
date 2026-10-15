"""AgentCUA — Computer-Use Agent (OpenClaw-style).

Наука: OpenClaw CUA (2025), WebArena (Zhou 2023).
Управляет браузером/системой через высокоуровневые команды.
"""
from __future__ import annotations

import shutil
import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentCUA(BaseAgent):
    name = "cua"
    MODULE_ALWAYS = True

    TRIGGERS = (
        "открой сайт", "зайди на", "перейди на",
        "открой браузер", "запусти firefox",
        "сделай скриншот", "кликни в браузере",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        t = request.text.lower()

        # Открыть URL
        if "открой сайт" in t or "зайди на" in t or "перейди на" in t:
            import re
            m = re.search(r"(https?://\S+|(?:[a-z0-9-]+\.)+[a-z]{2,})", t)
            if m:
                url = m.group(1)
                if not url.startswith("http"):
                    url = "https://" + url
                ok = self._open_url(url)
                return AgentResponse.ok(
                    text=f"🌐 {'Открываю' if ok else 'Не смог открыть'}: {url}",
                    agent_name=self.name,
                )

        if "открой браузер" in t or "запусти firefox" in t:
            ok = self._open_browser()
            return AgentResponse.ok(
                text=f"🌐 Firefox {'запущен' if ok else 'не найден'}",
                agent_name=self.name,
            )

        return AgentResponse.not_handled(self.name)

    @staticmethod
    def _open_url(url: str) -> bool:
        try:
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", url],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _open_browser() -> bool:
        for cmd in ("firefox", "google-chrome", "chromium"):
            if shutil.which(cmd):
                try:
                    subprocess.Popen([cmd],
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                    return True
                except Exception:
                    continue
        return False


__all__ = ["AgentCUA"]
