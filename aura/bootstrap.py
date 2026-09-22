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
    AgentMusicDucker,
    AgentPower,
    AgentRAGMemory,
    AgentRegistry,
    AgentScreenReader,
    AgentSecurity,
    AgentTextEditor,
    AgentTime,
    AgentToolRouter,
    AgentUpdates,
    AgentVault,
    AgentVision,
    AgentVKMusic,
    AgentWindowControl,
    AgentWindowManager,
)
from aura.core.orchestrator import Orchestrator


def build_orchestrator() -> Orchestrator:
    """
    Собрать Orchestrator со всеми агентами.

    Порядок регистрации (важен!):
    1. Простые и точные (time, power, vault)
    2. Узкий ducking (music_ducker — до audio_pult, чтобы не перехватить «громче»)
    3. audio_pult — широкие «громче/тише»
    4. Дневник, память, реестр, функции, обновления, security
    5. Аудио-маршрутизация
    6. X11 (vision, focus_switch, window_manager, context_memory, text_editor)
    7. Специфичные «открой X» (vk_music, browser_tabs)
    8. Опасные, но широкие ключи (app_launcher, window_control, screen_reader)
    9. Медиа (media_search — перехватывает «включи»)
    10. Internet — последним (общий «найди»)

    Returns:
        Orchestrator с зарегистрированными агентами.
    """
    tool_router = AgentToolRouter()
    brain = AgentBrain()
    orch = Orchestrator(tool_router=tool_router, brain=brain)

    # --- Уровень 1: простые и точные ---
    orch.register(AgentTime())
    orch.register(AgentPower())
    orch.register(AgentVault())

    # --- Уровень 2: узкий ducking — ДО audio_pult ---
    orch.register(AgentMusicDucker())

    # --- Уровень 3: audio_pult — широкие ключи ---
    orch.register(AgentAudioPult())

    # --- Уровень 4: дневник, память, реестр, функции, обновления, security ---
    orch.register(AgentJournal())
    orch.register(AgentRAGMemory())
    orch.register(AgentRegistry())
    orch.register(AgentFunctions())
    orch.register(AgentUpdates())
    orch.register(AgentSecurity())

    # --- Уровень 5: аудио-маршрутизация ---
    orch.register(AgentAudioRouter())

    # --- Уровень 6: X11 специфичные ---
    orch.register(AgentVision())
    orch.register(AgentFocusSwitch())
    orch.register(AgentWindowManager())
    orch.register(AgentContextMemory())
    orch.register(AgentTextEditor())

    # --- Уровень 7: специфичные "открой X" — раньше AppLauncher ---
    orch.register(AgentVKMusic())
    orch.register(AgentBrowserTabs())

    # --- Уровень 8: опасные, но широкие ключи ---
    orch.register(AgentAppLauncher())
    orch.register(AgentWindowControl())
    orch.register(AgentScreenReader())

    # --- Уровень 9: медиа (перехватывает "включи") ---
    orch.register(AgentMediaSearch())

    # --- Уровень 10: Internet — последним (общий "найди") ---
    orch.register(AgentInternet())

    return orch


__all__ = ["build_orchestrator"]
