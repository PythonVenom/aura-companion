"""AgentOpenResolver — открой X через Cascade (ADR-098/099)."""
from __future__ import annotations
import subprocess
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent
from aura.core.cascade_factory import build_app_cascade

WEB_MAP = {
    "дипсик": "https://chat.deepseek.com",
    "deepseek": "https://chat.deepseek.com",
    "вк": "https://vk.com",
    "vk": "https://vk.com",
    "телеграм": "https://web.telegram.org",
    "telegram": "https://web.telegram.org",
}

class AgentOpenResolver(BaseAgent):
    name = "open_resolver"
    MODULE_ALWAYS = True
    KEYWORDS = ("открой ", "запусти ", "open ")

    def can_handle(self, request):
        text = request.text.lower().strip()
        return any(k in text for k in self.KEYWORDS)

    def _target(self, text):
        t = text.lower().strip()
        for k in self.KEYWORDS:
            if k in t:
                return t[t.index(k) + len(k):].strip(" .,!?:;")
        return ""

    def _spawn(self, cmd):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    async def handle(self, request):
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        target = self._target(request.text)
        if not target:
            return AgentResponse.not_handled(self.name)
        c = build_app_cascade()
        r = c.resolve(target)
        if r["level"] == "app":
            if self._spawn([r["value"]]):
                return AgentResponse.ok(f"Открываю {target}", self.name)
        if r["level"] == "window":
            return AgentResponse.ok(f"Окно {target} уже открыто", self.name)
        url = WEB_MAP.get(target)
        if url and self._spawn(["xdg-open", url]):
            return AgentResponse.ok(f"Открываю {target} в браузере", self.name)
        return AgentResponse.not_handled(self.name)

__all__ = ["AgentOpenResolver"]
