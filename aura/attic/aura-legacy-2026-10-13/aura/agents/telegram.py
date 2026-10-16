"""Telegram Web адаптер — голосовое управление Telegram.

Философия: web > native (см. JOURNAL).
SiteAdapter pattern (ADR-018).
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.bridge import send_command
from aura.core.protocol import AgentRequest, AgentResponse


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

    # Bug 49: app-команды без telegram-контекста → app_launcher
    APP_KEYWORDS = ("открой", "открыть", "закрой", "закрыть",
                    "запусти", "запустить", "сверни", "разверни")
    # Bug 49: если есть эти слова — telegram-интент (не app-открытие)
    TELEGRAM_CONTEXT = ("канал", "чат", "сообщени", "переписк",
                        "прочитай", "найди", "список", "отправь")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        padded = f" {text} "
        # 1. Telegram-слова есть?
        has_tg = (" тг " in padded or "телеграм" in text or "телега" in text
                  or "telegram" in text or " tg " in padded
                  or any(kw in text for kw in self.KEYWORDS))
        if not has_tg:
            return False
        # 2. App-команда БЕЗ telegram-контекста → app_launcher
        if any(kw in text for kw in self.APP_KEYWORDS):
            if not any(kw in text for kw in self.TELEGRAM_CONTEXT):
                return False
        return True

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
                return AgentResponse.ok("❌ Telegram: не найден", self.name)

        # 3. Прочитать последнее
        if "прочитай" in text or "что пишут" in text or "последнее" in text:
            result = send_command({"action": "tg_read_last"})
            if result is None or "error" in result:
                return AgentResponse.ok(_err(result), self.name)
            data = result.get("data", {})
            msg = data.get("text", "")
            if msg:
                return AgentResponse.ok(f"📱 Telegram: {msg[:200]}", self.name)
            return AgentResponse.ok("📱 Telegram: пусто", self.name)

        # 4. Папки
        if "папки" in text or "категории" in text:
            result = send_command({"action": "tg_list_folders"})
            if result is None or "error" in result:
                return AgentResponse.ok(_err(result), self.name)
            data = result.get("data", [])
            if not data:
                return AgentResponse.ok("📱 Telegram: папок нет", self.name)
            names = [f.get("name", "?") for f in data[:5]]
            return AgentResponse.ok(f"📱 Telegram папки: {', '.join(names)}", self.name)

        # 5. Открыть канал
        if "канал" in text or "открой канал" in text:
            query = ""
            for kw in ("канал ", "открой канал "):
                if kw in text:
                    query = text.split(kw, 1)[1].strip()
                    break
            if query:
                result = send_command({"action": "tg_open_channel", "query": query})
                if result is None or "error" in result:
                    return AgentResponse.ok(_err(result), self.name)
                data = result.get("data", {})
                if data.get("ok"):
                    return AgentResponse.ok(f"📱 Telegram: {data.get('name')}", self.name)
                return AgentResponse.ok("📱 Telegram: не найден", self.name)

        # 6. Открыть Telegram
        if "открой телеграм" in text or "открой телегу" in text:
            return AgentResponse.ok("🌐 Telegram: открыт", self.name)

        return AgentResponse.ok("Telegram: команда не распознана", self.name)


__all__ = ["AgentTelegram"]
