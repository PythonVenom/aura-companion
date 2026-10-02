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

import asyncio


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

    def __init__(self, tool_router=None, brain=None, dispatcher=None) -> None:
        self.registry = AgentRegistry()
        self.tool_router = tool_router
        self.brain = brain
        self.dispatcher = dispatcher
        self.route_tree = None
        if dispatcher is not None:
            try:
                from aura.core.route_tree import build_route_tree
                self.route_tree = build_route_tree()
            except Exception as e:
                print(f"⚠️ RouteTree init: {e}")
        self.fallback_text = "Не расслышала, Создатель, повторите"
        self._last_response: AgentResponse | None = None

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

        # observability (ADR-112)
        try:
            from aura.observability import new_trace, log
            new_trace("process")
            log("input", text=text[:120])
        except Exception:
            pass

        agent = self.registry.find(request)
        if agent is None:
            # 2. RouteTree → dispatcher (быстрый regex-роутинг)
            if self.route_tree is not None and self.dispatcher is not None:
                try:
                    routed = self.route_tree.handle(text, {})
                    if routed and isinstance(routed, dict):
                        route = routed.get("route", "")
                        action = routed.get("action", "")
                        args = routed.get("args", {}) or {}
                        if route and route != "ask" and action:
                            cap = f"{route}.{action}"
                            ok, result = self.dispatcher.dispatch(cap, args)
                            if ok:
                                return result
                except Exception as e:
                    print(f"⚠️ RouteTree: {e}")
            # 3. ToolRouter
            if self.tool_router is not None:
                try:
                    result = await asyncio.to_thread(self.tool_router.route, text)
                    if result:
                        t = result.get("type")
                        rtext = result.get("response", "")
                        if t in ("tool", "text") and rtext and len(rtext) > 2:
                            return rtext
                except Exception as e:
                    print(f"⚠️ ToolRouter: {e}")
            # 3. Brain
            if self.brain is not None:
                try:
                    result = await asyncio.to_thread(self.brain.ask, text)
                    if result and not result.startswith("❌"):
                        return result
                except Exception as e:
                    print(f"⚠️ Brain: {e}")
            return self.fallback_text

        try:
            response = await agent.handle(request)
        except Exception as e:
            return f"❌ Ошибка агента {agent.name}: {e}"

        if response.status == AgentStatus.OK:
            self._last_response = response
            return response.text

        if response.status == AgentStatus.NOT_HANDLED:
            return self.fallback_text

        if response.status == AgentStatus.ERROR:
            return f"❌ {response.error or 'Ошибка'}"

        return self.fallback_text

    def last_silent(self) -> bool:
        """True = последний ответ был silent (ADR-048)."""
        return bool(self._last_response and self._last_response.silent)

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Обработать AgentRequest напрямую (для тестов)."""
        agent = self.registry.find(request)
        if agent is None:
            return AgentResponse.not_handled()
        return await agent.handle(request)

    def __len__(self) -> int:
        return len(self.registry)


__all__ = ["Orchestrator"]
