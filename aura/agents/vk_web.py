"""VK Web адаптер — голосовое управление vk.com через Firefox bridge.

По образцу messenger.py. Один content script на сайт.
Философия: web > приложение (см. JOURNAL).
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse
from aura.core.bridge import send_command


def error_text(result) -> str:
    if result is None:
        return "🌐 VK: bridge недоступен"
    return f"🌐 Ошибка: {result.get('error', 'unknown')}"


class AgentVKWeb(MicroAgent):
    """VK Web через Firefox content script."""

    KEYWORDS = (
        "вк", "вконтакте",
        "открой вк", "вк музыка", "вк друзья", "вк группы",
        "вк новости", "вк сообщения", "вк лента", "вк стена",
        "плейлист вк", "трек вк",
    )

    def __init__(self):
        super().__init__("vk_web", "VK Web адаптер")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        # Защита: «вк» внутри других слов (вкладки, вкладыш)
        if "вкладк" in text or "вкладок" in text:
            return False
        padded = f" {text} "
        return " вк " in padded or "вконтакте" in text or any(kw in text for kw in self.KEYWORDS[2:])

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        text = request.text.lower()
        # Заглушки — реализация по мере готовности content_vk.js
        return AgentResponse.ok("VK: заготовка (TDD)", self.name)


__all__ = ["AgentVKWeb"]
