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
    AgentPower,
    AgentScreenReader,
    AgentTime,
    AgentWindowControl,
)
from aura.core.orchestrator import Orchestrator


def build_orchestrator() -> Orchestrator:
    """
    Собрать Orchestrator со всеми агентами.

    Порядок регистрации:
    1. Простые и точные (time, power, audio) — раньше
    2. Опасные (app_launcher, window_control) — после простых
    3. Интернет и медиа — в конце (могут перехватить лишнее)

    Returns:
        Orchestrator с зарегистрированными агентами.
    """
    orch = Orchestrator()

    # --- Уровень 1: простые, детерминированные ---
    orch.register(AgentTime())
    orch.register(AgentPower())
    orch.register(AgentAudioPult())

    # --- Уровень 2: опасные, но точные по ключевым словам ---
    orch.register(AgentAppLauncher())
    orch.register(AgentWindowControl())
    orch.register(AgentScreenReader())
    orch.register(AgentBrowserTabs())

    # --- Уровень 3: сеть (могут перехватить "найди", "что такое") ---
    orch.register(AgentInternet())

    return orch


__all__ = ["build_orchestrator"]
