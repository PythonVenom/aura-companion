"""DeepSeek Web — Аура говорит с Дядей Р2 через браузер.

Паттерн: vk_web.py (SiteAdapter).
Транспорт: bridge.py → native host → extension → chat.deepseek.com.

Наука: Licklider 1960 (симбиоз), Brooks 1975 (база > фичи).
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.bridge import error_text, send_command
from aura.core.protocol import AgentRequest, AgentResponse


class AgentDeepSeekWeb(MicroAgent):
    """Аура шлёт пакет контекста Дяде Р2, получает ответ."""

    KEYWORDS = (
        "дядя р2", "дядя p2", "спроси deepseek", "спроси дипсик",
        "спроси у deepseek", "deepseek", "дипсик",
    )

    def __init__(self):
        super().__init__("deepseek_web", "DeepSeek Web адаптер")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text
        question = text
        for kw in self.KEYWORDS:
            if kw in text.lower():
                idx = text.lower().find(kw)
                question = text[idx + len(kw):].strip(" :,.-")
                break
        if not question:
            return AgentResponse.ok(
                "🌐 Что спросить? Напиши: 'дядя р2: <вопрос>'",
                self.name,
            )

        try:
            from aura.cockpit.handoff import build_handoff
            context = build_handoff()
        except Exception as e:
            context = f"(контекст недоступен: {e})"

        result = send_command(
            {
                "action": "deepseek_ask",
                "text": question,
                "context": context,
            },
            timeout=200.0,
        )

        if result is None or "error" in result:
            return AgentResponse.ok(error_text(result), self.name)

        reply = result.get("text", "").strip()
        if not reply:
            return AgentResponse.ok("🌐 DeepSeek: пустой ответ", self.name)

        preview = reply[:500]
        return AgentResponse.ok(f"🤖 Дядя Р2:\n{preview}", self.name)


__all__ = ["AgentDeepSeekWeb"]
