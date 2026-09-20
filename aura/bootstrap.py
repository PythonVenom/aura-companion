"""
Bootstrap Ауры.

Единственное место, где собирается Orchestrator со всеми агентами.
Точка входа для новой модульной архитектуры.

По науке:
- Явная регистрация агентов
- Никакой магии
- Порядок важен (первый подходящий выигрывает)
- Легко расширять: добавил агента — зарегистрировал здесь
"""

from __future__ import annotations

from aura.agents import (
    AgentAppLauncher,
    AgentAudioPult,
    AgentBrowserTabs,
    AgentInternet,
    AgentMediaSearch,
    AgentPower,
    AgentScreenReader,
    AgentTime,
    AgentVKMusic,
    AgentWindowControl,
)
from aura.core.orchestrator import Orchestrator


def build_orchestrator() -> Orchestrator:
    """
    Собрать Orchestrator со всеми агентами.

    Порядок регистрации (важен!):
    1. Простые и точные (time, power, audio)
    2. Опасные (app_launcher, window_control)
    3. Медиа (media_search — перехватывает "включи")
    4. VK Music (перехватывает "найди ... вк")
    5. Internet (общий "найди", "что такое") — последним

    Returns:
        Orchestrator с зарегистрированными агентами.
    """
    orch = Orchestrator()

    # --- Уровень 1: простые ---
    orch.register(AgentTime())
    orch.register(AgentPower())
    orch.register(AgentAudioPult())

    # --- Уровень 2: специфичные "открой X" — раньше AppLauncher ---
    orch.register(AgentVKMusic())
    orch.register(AgentBrowserTabs())

    # --- Уровень 3: опасные, но широкие ключи ---
    orch.register(AgentAppLauncher())
    orch.register(AgentWindowControl())
    orch.register(AgentScreenReader())

    # --- Уровень 4: медиа (перехватывает "включи") ---
    orch.register(AgentMediaSearch())

    # --- Уровень 5: Internet — последним (общий "найди") ---
    orch.register(AgentInternet())

    return orch


__all__ = ["build_orchestrator"]
