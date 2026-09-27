"""VK Web адаптер — полное голосовое управление vk.com.

Философия: web > native app (см. JOURNAL).
SiteAdapter pattern (ADR-018).
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse
from aura.core.bridge import send_command


def _err(result) -> str:
    if result is None:
        return "🌐 VK: bridge недоступен"
    return f"🌐 Ошибка: {result.get('error', 'unknown')}"


class AgentVKWeb(MicroAgent):
    """VK Web — навигация, музыка, сообщения, друзья, группы."""

    SECTIONS = {
        "лента": "feed", "новости": "feed", "feed": "feed",
        "сообщения": "im", "переписки": "im", "im": "im",
        "друзья": "friends", "друзья онлайн": "friends",
        "группы": "groups", "паблики": "groups",
        "музыка": "audio", "аудио": "audio",
        "видео": "videos",
        "моя страница": "me", "профиль": "me",
    }

    KEYWORDS = (
        "вк ", "вконтакте",
        "вк музыка", "вк друзья", "вк группы", "вк новости",
        "вк лента", "вк сообщения", "вк видео", "вк стена",
        "открой вк", "перейди в вк",
    )

    def __init__(self):
        super().__init__("vk_web", "VK Web адаптер")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        if "вкладк" in text or "вкладок" in text:
            return False
        padded = f" {text} "
        if " вк " in padded or "вконтакте" in text:
            return True
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        # 1. Навигация по разделам
        for ru_name, en_name in self.SECTIONS.items():
            if ru_name in text:
                result = send_command({"action": "vk_navigate", "section": en_name})
                if result is None or "error" in result:
                    return AgentResponse.ok(_err(result), self.name)
                data = result.get("data", {})
                if data.get("ok"):
                    return AgentResponse.ok(f"🌐 VK: {ru_name}", self.name)
                return AgentResponse.ok(f"❌ VK: раздел не найден", self.name)

        # 2. Список разделов
        if "что можно" in text or "разделы" in text or "куда" in text:
            return AgentResponse.ok(
                "🌐 VK разделы: лента, сообщения, друзья, группы, музыка, видео",
                self.name,
            )

        # 3. Список сообщений
        if "сообщения" in text or "переписки" in text or "чаты" in text:
            result = send_command({"action": "vk_list_chats"})
            if result is None or "error" in result:
                return AgentResponse.ok(_err(result), self.name)
            data = result.get("data", {})
            chats = data.get("chats", [])
            if not chats:
                return AgentResponse.ok("🌐 VK: нет чатов", self.name)
            lines = ["🌐 VK чаты:"]
            for i, c in enumerate(chats[:10], 1):
                name = c.get("name", "?")[:40]
                preview = c.get("preview", "")[:40]
                lines.append(f"{i}. {name} — {preview}")
            return AgentResponse.ok("\n".join(lines), self.name)

        # 4. Ответить в VK
        if "ответь" in text or "напиши" in text:
            # «ответь: привет» или «напиши Васе: привет»
            reply = ""
            for kw in ("ответь:", "ответь ", "напиши:", "напиши "):
                if kw in text:
                    reply = text.split(kw, 1)[1].strip(" .,!?:;")
                    break
            if reply:
                result = send_command({"action": "vk_send_message", "text": reply})
                if result is None or "error" in result:
                    return AgentResponse.ok(_err(result), self.name)
                return AgentResponse.ok(f"🌐 VK: написала «{reply[:50]}»", self.name)

        # 5. Просто «открой вк» — фокус на вкладку
        if "открой вк" in text or "открой вконтакте" in text:
            result = send_command({"action": "vk_current"})
            if result and "data" in result:
                section = result["data"].get("section", "unknown")
                return AgentResponse.ok(f"🌐 VK открыт: {section}", self.name)
            return AgentResponse.ok("🌐 VK: открываю", self.name)

        return AgentResponse.ok("VK: команда не распознана", self.name)


__all__ = ["AgentVKWeb"]
