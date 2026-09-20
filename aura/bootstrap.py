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
    AgentBrowserTabs,
    AgentFunctions,
    AgentInternet,
    AgentJournal,
    AgentMediaSearch,
    AgentPower,
    AgentRAGMemory,
    AgentRegistry,
    AgentScreenReader,
    AgentTime,
    AgentUpdates,
    AgentVKMusic,
    AgentWindowControl,
)
from aura.core.orchestrator import Orchestrator


def build_orchestrator() -> Orchestrator:
    """
    Собрать Orchestrator со всеми агентами.

    Порядок регистрации (важен!):
    1. Простые и точные (time, power, audio_pult) — самые узкие ключи
    2. Дневник, память, реестр, функции, обновления — специфичные команды
    3. Аудио-маршрутизация — "проверь аудио", "какая гарнитура"
    4. Специфичные "открой X" (vk_music, browser_tabs)
    5. Опасные, но широкие ключи (app_launcher, window_control, screen_reader)
    6. Медиа (media_search — перехватывает "включи")
    7. Internet — последним (общий "найди")

    Returns:
        Orchestrator с зарегистрированными агентами.
    """
    orch = Orchestrator()

    # --- Уровень 1: простые и точные ---
    orch.register(AgentTime())
    orch.register(AgentPower())
    orch.register(AgentAudioPult())

    # --- Уровень 2: дневник, память, реестр, функции, обновления ---
    orch.register(AgentJournal())
    orch.register(AgentRAGMemory())
    orch.register(AgentRegistry())
    orch.register(AgentFunctions())
    orch.register(AgentUpdates())

    # --- Уровень 3: аудио-маршрутизация ---
    orch.register(AgentAudioRouter())

    # --- Уровень 4: специфичные "открой X" — раньше AppLauncher ---
    orch.register(AgentVKMusic())
    orch.register(AgentBrowserTabs())

    # --- Уровень 5: опасные, но широкие ключи ---
    orch.register(AgentAppLauncher())
    orch.register(AgentWindowControl())
    orch.register(AgentScreenReader())

    # --- Уровень 6: медиа (перехватывает "включи") ---
    orch.register(AgentMediaSearch())

    # --- Уровень 7: Internet — последним (общий "найди") ---
    orch.register(AgentInternet())

    return orch


__all__ = ["build_orchestrator"]
