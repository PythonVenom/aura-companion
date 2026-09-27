"""Telegram Web адаптер — голосовое управление Telegram.

Философия: web > native (см. JOURNAL).
SiteAdapter pattern (ADR-018).
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse
from aura.core.bridge import send_command


def _err(result) -> str:
    if result is None:
        return "🌐 Telegram: bridge недоступен"
    return f"🌐 Ошибка: {result.get('error', 'unknown')}"


class AgentTelegram(MicroAgent):
    """Telegram Web K — чаты, отправка, навигация."""

    KEYWORDS = (
        "телеграм", "телега", "тг ", "открой телеграм",
        "напиши в телеграм", "телеграм чаты", "телеграм сообщения",
    )

    def __init__(self):
        super().__init__("telegram", "Telegram Web адаптер")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        padded = f" {text} "
        if " тг " in padded or "телеграм" in text or "телега" in text:
            return True
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        # 1. Список чатов
        if "чаты" in text or "сообщения" in text or "переписки" in text:
            result = send_command({"action": "tg_list_chats"})
            if result is None or "error" in result:
                return AgentResponse.ok(_err(result), self.name)
            chats = result.get("data", [])
            if not chats:
                return AgentResponse.ok("🌐 Telegram: нет чатов", self.name)
            lines = ["🌐 Telegram:"]
            for i, c in enumerate(chats[:10], 1):
                lines.append(f"{i}. {c.get('name', '?')[:40]}")
            return AgentResponse.ok("\n".join(lines), self.name)

        # 2. Найти чат
        if "найди" in text or "открой чат" in text:
            query = ""
            for kw in ("найди чат ", "открой чат ", "найди "):
                if kw in text:
                    query = text.split(kw, 1)[1].strip()
                    break
            if query:
                result = send_command({"action": "tg_find_chat", "query": query})
                if result is None or "error" in result:
                    return AgentResponse.ok(_err(result), self.name)
                data = result.get("data", {})
                if data.get("found"):
                    return AgentResponse.ok(f"🌐 Telegram: {data.get('name')}", self.name)
                return AgentResponse.ok(f"❌ Telegram: не найден", self.name)

        # 3. Открыть Telegram
        if "открой телеграм" in text or "открой телегу" in text:
            return AgentResponse.ok("🌐 Telegram: открыт", self.name)

        return AgentResponse.ok("Telegram: команда не распознана", self.name)


__all__ = ["AgentTelegram"]
