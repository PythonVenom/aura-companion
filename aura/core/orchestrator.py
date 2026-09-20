"""
Оркестратор Ауры.

Заменяет AuraCore.process() из монолита.
По науке:
- Один роутер (реестр агентов)
- Никаких if/elif
- Async/await
- Легко тестируется

Оркестратор НЕ знает про:
- T-one (слух)
- Piper (голос)
- Ollama (LLM)
- Конкретных агентов

Он знает только про:
- AgentRegistry
- AgentRequest / AgentResponse
"""

from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, AgentStatus
from aura.core.registry import AgentRegistry


class Orchestrator:
    """
    Оркестратор: принимает текст, возвращает ответ.

    Использование:
        orch = Orchestrator()
        orch.register(AgentTime())
        orch.register(AgentPower())

        response = await orch.process("который час")
    """

    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self.fallback_text = "Не расслышала, Создатель, повторите"

    def register(self, agent) -> None:
        """Зарегистрировать агента."""
        self.registry.register(agent)

    async def process(self, text: str) -> str:
        """
        Обработать текст.

        1. Найти агента через реестр
        2. Если найден — выполнить handle()
        3. Если не найден — fallback
        """
        request = AgentRequest(text=text)

        agent = self.registry.find(request)
        if agent is None:
            return self.fallback_text

        try:
            response = await agent.handle(request)
        except Exception as e:
            return f"❌ Ошибка агента {agent.name}: {e}"

        if response.status == AgentStatus.OK:
            return response.text

        if response.status == AgentStatus.NOT_HANDLED:
            return self.fallback_text

        if response.status == AgentStatus.ERROR:
            return f"❌ {response.error or 'Ошибка'}"

        return self.fallback_text

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Обработать AgentRequest напрямую (для тестов)."""
        agent = self.registry.find(request)
        if agent is None:
            return AgentResponse.not_handled()
        return await agent.handle(request)

    def __len__(self) -> int:
        return len(self.registry)


__all__ = ["Orchestrator"]
