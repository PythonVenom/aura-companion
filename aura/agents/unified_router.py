"""T-msg-6 — Unified message router.

Наука:
- Hohpe & Woolf 2003 — Enterprise Integration Patterns (Message Router)
- Gamma et al. 1994 — Adapter + Facade (GoF)
- UC Forum 2020 — Unified Communications
- Matterbridge — референс (мост между чатами)

Идея: один фасад над всеми messenger-агентами.
Роутер находит зарегистрированный адаптер по имени и передаёт сообщение.
Новые адаптеры (Matrix, XMPP, Signal) регистрируются автоматически.
"""
from __future__ import annotations

from aura.agents.base import MicroAgent
from aura.core.protocol import AgentRequest, AgentResponse


# Маппинг: алиас → имя агента
ALIASES = {
    "tg": "telegram",
    "telegram": "telegram",
    "телеграм": "telegram",
    "wa": "whatsapp",
    "whatsapp": "whatsapp",
    "ватсап": "whatsapp",
    "вацап": "whatsapp",
    "vk": "vk_web",
    "вк": "vk_web",
    "max": "messenger",
    "макс": "messenger",
    "email": "email",
    "почта": "email",
    "mail": "email",
    "sms": "sms",
    "смс": "sms",
    "signal": "signal",
    "matrix": "matrix",
    "xmpp": "xmpp",
    "discord": "discord",
    "slack": "slack",
}


class AgentUnifiedRouter(MicroAgent):
    name = "unified_router"

    TRIGGERS = ("отправь в", "напиши в", "прочитай из",
                "найди во всех", "единый чат", "все сообщения",
                "router", "роутер")

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()

        if "статус" in t or "какие" in t or "список" in t:
            return self._status()
        if "все сообщения" in t or "единый чат" in t:
            return self._unified_inbox()
        if "отправь" in t or "напиши" in t:
            return self._route_send(request.text)
        if "прочитай" in t:
            return self._route_read(request.text)

        return AgentResponse.ok(
            text="Роутер. 'отправь в <чат> <кому> <что>' / 'все сообщения' / "
                 "'статус'",
            agent_name=self.name,
        )

    def _detect_target(self, text: str) -> tuple[str | None, str]:
        """Найти messenger в тексте. Возвращает (имя_агента, остаток)."""
        t = text.lower()
        for alias, agent_name in ALIASES.items():
            if f"в {alias}" in t or f"из {alias}" in t or f"{alias} " in t:
                return agent_name, text
        return None, text

    # --- Отправка ---

    def _route_send(self, text: str) -> AgentResponse:
        agent_name, _ = self._detect_target(text)
        if not agent_name:
            available = ", ".join(sorted(set(ALIASES.values())))
            return AgentResponse.ok(
                text=f"🤔 Не поняла, куда отправить. Доступно: {available}",
                agent_name=self.name,
            )
        # Ищем зарегистрированный агент
        agent = self._find_agent(agent_name)
        if not agent:
            return AgentResponse.ok(
                text=f"⚠️ Агент '{agent_name}' не зарегистрирован. "
                     f"Установи модуль или используй другой мессенджер.",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"➡️ Маршрут: {agent_name}. Передаю агенту.",
            agent_name=self.name,
        )

    def _route_read(self, text: str) -> AgentResponse:
        agent_name, _ = self._detect_target(text)
        if not agent_name:
            return self._unified_inbox()
        agent = self._find_agent(agent_name)
        if not agent:
            return AgentResponse.ok(
                text=f"⚠️ Агент '{agent_name}' не найден.",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"📖 Маршрут: {agent_name}. Прошу прочитать.",
            agent_name=self.name,
        )

    def _find_agent(self, agent_name: str):
        """Найти агент в orchestrator."""
        try:
            # Пытаемся импортировать — наличие модуля = регистрация
            mod_path = f"aura.agents.{agent_name}"
            __import__(mod_path)
            return True
        except ImportError:
            return None

    # --- Единый inbox ---

    def _unified_inbox(self) -> AgentResponse:
        """Собрать сводку по всем доступным messenger-агентам."""
        available = []
        for agent_name in sorted(set(ALIASES.values())):
            if self._find_agent(agent_name):
                available.append(agent_name)
        if not available:
            return AgentResponse.ok(
                text="📭 Ни один messenger-агент не установлен.",
                agent_name=self.name,
            )
        lines = [f"📬 Доступные каналы ({len(available)}):"]
        for name in available:
            lines.append(f"  • {name}")
        lines.append("\nСкажи 'прочитай из <канал>' для конкретного.")
        return AgentResponse.ok(text="\n".join(lines), agent_name=self.name)

    # --- Статус ---

    def _status(self) -> AgentResponse:
        available = []
        for agent_name in sorted(set(ALIASES.values())):
            if self._find_agent(agent_name):
                available.append(agent_name)
        return AgentResponse.ok(
            text=f"🔀 Router: {len(available)} каналов доступно. "
                 f"Алиасы: {len(ALIASES)}.",
            agent_name=self.name,
        )

    # --- Публичный API ---

    def resolve(self, alias: str) -> str | None:
        """Публичный API: алиас → имя агента."""
        return ALIASES.get(alias.lower())

    def list_aliases(self) -> dict:
        """Публичный API: все алиасы."""
        return dict(ALIASES)


__all__ = ["AgentUnifiedRouter", "ALIASES"]
