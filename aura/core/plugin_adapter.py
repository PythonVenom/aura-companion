"""Adapter: плагин-агент → BaseAgent для orchestrator (ADR-090).

Плагины — простые классы с can_handle/handle.
Orchestrator ждёт BaseAgent с can_handle + async handle().
Этот adapter склеивает.
"""
from __future__ import annotations
from typing import Any


class PluginAgentWrapper:
    """Обёртка плагин-агента под BaseAgent-интерфейс."""

    def __init__(self, plugin_agent: Any, plugin_id: str):
        self._agent = plugin_agent
        self.name = f"plugin_{plugin_id}"
        self.description = f"Plugin: {plugin_id}"
        self.active = True

    def can_handle(self, request) -> bool:
        text = getattr(request, "text", "")
        try:
            return bool(self._agent.can_handle(text))
        except Exception:
            return False

    async def handle(self, request):
        """Async-обёртка вокруг sync plugin.handle()."""
        from aura.core.protocol import AgentResponse
        text = getattr(request, "text", "")
        try:
            import asyncio
            result = await asyncio.to_thread(self._agent.handle, text)
            return AgentResponse.ok(str(result), self.name)
        except Exception as e:
            return AgentResponse.ok(f"❌ plugin error: {e}", self.name)


def register_plugin_agent(orch, agent_cls, plugin_id: str) -> None:
    """Создать instance + зарегистрировать в orch.registry."""
    try:
        instance = agent_cls()
    except Exception as e:
        print(f"⚠️ plugin {plugin_id} init: {e}")
        return
    wrapper = PluginAgentWrapper(instance, plugin_id)
    try:
        reg = orch.registry
        name = wrapper.name
        # Основной путь: register(agent)
        if hasattr(reg, "register"):
            try:
                reg.register(wrapper)
                return
            except Exception:
                pass
        # Fallback: _agents dict
        if hasattr(reg, "_agents") and isinstance(getattr(reg, "_agents"), dict):
            reg._agents[name] = wrapper
            return
        # Fallback: _agents list — append
        if hasattr(reg, "_agents") and isinstance(getattr(reg, "_agents"), list):
            reg._agents.append(wrapper)
            return
    except Exception as e:
        print(f"⚠️ register {plugin_id}: {e}")


__all__ = ["PluginAgentWrapper", "register_plugin_agent"]
