"""#146 AgentPlugins — управление реестром плагинов."""
from __future__ import annotations

from aura.core.plugin_registry import (
    format_registry,
    search,
)
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentPlugins(BaseAgent):
    name = "plugins"

    TRIGGERS = (
        "реестр плагинов", "каталог плагинов", "магазин плагинов",
        "найди плагин", "поиск плагина",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(kw in t for kw in self.TRIGGERS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if "найди" in t or "поиск" in t:
            query = t.replace("найди", "").replace("плагин", "").replace("поиск", "").strip()
            if query:
                results = search(query)
                if not results:
                    return AgentResponse.ok(f"❌ Не найдено: {query}", self.name)
                lines = [f"🔍 Найдено {len(results)}:"]
                for p in results[:10]:
                    lines.append(f"  • {p.name} v{p.version}")
                return AgentResponse.ok("\n".join(lines), self.name)
        return AgentResponse.ok(format_registry(), self.name)


__all__ = ["AgentPlugins"]
