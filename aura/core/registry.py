"""
Реестр агентов.

Регистрирует агентов и находит подходящего для запроса.
Не знает про ToolRouter, AuraCore, Ollama.

По науке:
- Простая коллекция
- Без магии
- Легко тестируется
"""

from __future__ import annotations

from aura.core.protocol import AgentProtocol, AgentRequest


class AgentRegistry:
    """
    Реестр агентов.

    Использование:
        registry = AgentRegistry()
        registry.register(AgentTime())
        registry.register(AgentPower())

        agent = registry.find(AgentRequest(text="который час"))
        if agent:
            response = await agent.handle(request)
    """

    def __init__(self) -> None:
        self._agents: list[AgentProtocol] = []

    def register(self, agent: AgentProtocol) -> None:
        """Зарегистрировать агента."""
        self._agents.append(agent)

    def unregister(self, name: str) -> None:
        """Удалить агента по имени."""
        self._agents = [a for a in self._agents if a.name != name]

    def find(self, request: AgentRequest) -> AgentProtocol | None:
        """
        Найти первого агента, который может обработать запрос.

        Порядок регистрации важен: первый подходящий выигрывает.
        """
        for agent in self._agents:
            if agent.can_handle(request):
                return agent
        return None

    def list_names(self) -> list[str]:
        """Список имён агентов (для отладки)."""
        return [a.name for a in self._agents]

    def __len__(self) -> int:
        return len(self._agents)

    def __iter__(self):
        return iter(self._agents)


__all__ = ["AgentRegistry"]
