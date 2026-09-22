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
    AgentAudioRouter,
    AgentBrain,
    AgentBrowserTabs,
    AgentContextMemory,
    AgentFocusSwitch,
    AgentFunctions,
    AgentInternet,
    AgentJournal,
    AgentMediaSearch,
    AgentPower,
    AgentRAGMemory,
    AgentRegistry,
    AgentScreenReader,
    AgentSecurity,
    AgentTime,
    AgentToolRouter,
    AgentUpdates,
    AgentVault,
    AgentVision,
    AgentVKMusic,
    AgentWindowControl,
)
from aura.core.orchestrator import Orchestrator


def build_orchestrator() -> Orchestrator:
    """
    Собрать Orchestrator со всеми агентами.

    Порядок регистрации (важен!):
    1. Простые и точные (time, power, audio_pult, vault)
    2. Дневник, память, реестр, функции, обновления, security
    3. Аудио-маршрутизация
    4. X11 специфичные (vision, focus_switch, context_memory)
    5. Специфичные "открой X" (vk_music, browser_tabs)
    6. Опасные, но широкие ключи (app_launcher, window_control, screen_reader)
    7. Медиа (media_search — перехватывает "включи")
    8. Internet — последним (общий "найди")

    Returns:
        Orchestrator с зарегистрированными агентами.
    """
    tool_router = AgentToolRouter()
    brain = AgentBrain()
    orch = Orchestrator(tool_router=tool_router, brain=brain)

    # --- Уровень 1: простые и точные ---
    orch.register(AgentTime())
    orch.register(AgentPower())
    orch.register(AgentAudioPult())
    orch.register(AgentVault())

    # --- Уровень 2: дневник, память, реестр, функции, обновления, security ---
    orch.register(AgentJournal())
    orch.register(AgentRAGMemory())
    orch.register(AgentRegistry())
    orch.register(AgentFunctions())
    orch.register(AgentUpdates())
    orch.register(AgentSecurity())

    # --- Уровень 3: аудио-маршрутизация ---
    orch.register(AgentAudioRouter())

    # --- Уровень 4: X11 специфичные ---
    orch.register(AgentVision())
    orch.register(AgentFocusSwitch())
    orch.register(AgentContextMemory())

    # --- Уровень 5: специфичные "открой X" — раньше AppLauncher ---
    orch.register(AgentVKMusic())
    orch.register(AgentBrowserTabs())

    # --- Уровень 6: опасные, но широкие ключи ---
    orch.register(AgentAppLauncher())
    orch.register(AgentWindowControl())
    orch.register(AgentScreenReader())

    # --- Уровень 7: медиа (перехватывает "включи") ---
    orch.register(AgentMediaSearch())

    # --- Уровень 8: Internet — последним (общий "найди") ---
    orch.register(AgentInternet())

    return orch


__all__ = ["build_orchestrator"]
