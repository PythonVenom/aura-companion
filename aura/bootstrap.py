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

import tomllib
from pathlib import Path

from aura.agents.time_agent import AgentTimeAgent
from aura.agents.health import AgentHealth

from aura.agents.massage import AgentMassage
from aura.agents.dictation import AgentDictation
from aura.agents.construction import AgentConstruction
from aura.agents.bpm import AgentBPM

from aura.agents import (
    AgentAppLauncher,
    AgentAudioPult,
    AgentAudioRouter,
    AgentBrain,
    AgentAtSpi,
    AgentMcp,
    AgentTelegram,
    AgentVKWeb,
    AgentBrowserTabs,
    AgentChecklist,
    AgentContextMemory,
    AgentFocusSwitch,
    AgentFunctions,
    AgentInternet,
    AgentMessenger,
    AgentJournal,
    AgentMediaSearch,
    AgentMusicDucker,
    AgentMediaPause,
    AgentMusicLocal,
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


MODULES_CONFIG_PATH = Path.home() / ".config" / "aura" / "modules.toml"


def load_modules_config() -> dict:
    """Прочитать ~/.config/aura/modules.toml. Пусто если нет."""
    if not MODULES_CONFIG_PATH.exists():
        return {}
    try:
        with open(MODULES_CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        return data.get("modules", {})
    except Exception:
        return {}


def is_module_enabled(agent_class, config: dict) -> bool:
    """Включён ли модуль (ADR-011)."""
    if getattr(agent_class, "MODULE_ALWAYS", False):
        return True
    if not MODULES_CONFIG_PATH.exists():
        return True
    module_name = getattr(agent_class, "MODULE_NAME", agent_class.__name__.lower())
    # Default — включён. Пользователь явно выключает (ADR-011).
    return bool(config.get(module_name, True))


def _try_register(orch, agent_class, config: dict) -> bool:
    """Зарегистрировать агента, если его модуль включён (ADR-011)."""
    if not is_module_enabled(agent_class, config):
        return False
    try:
        orch.register(agent_class())
        return True
    except Exception as e:
        print(f"⚠️ Не зарегистрирован {agent_class.__name__}: {e}")
        return False


def _load_plugins(orch) -> int:
    """Загрузить плагины из ~/.local/share/aura/plugins/ (ADR-090)."""
    try:
        from aura.core.plugin_manager import PluginManager
        pm = PluginManager()
        plugins = pm.list_plugins()
        loaded = 0
        for p in plugins:
            plugin_dir = pm.root / p.id
            py = plugin_dir / "plugin.py"
            if not py.exists():
                continue
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"aura_plugin_{p.id}", py)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                loaded += 1
            except Exception as e:
                print(f"⚠️ plugin {p.id}: {e}")
        if loaded:
            print(f"🔌 Плагинов загружено: {loaded}")
        return loaded
    except Exception:
        return 0


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
    # Bug 47: AURA_BRAIN=0 в env → brain отключён (fast path для видео)
    import os as _os
    if _os.environ.get("AURA_BRAIN", "1") == "0":
        brain = None
        print("⚡ Brain ОТКЛЮЧЁН (AURA_BRAIN=0) — только агенты")
    else:
        brain = AgentBrain()
    orch = Orchestrator(tool_router=tool_router, brain=brain)
    _load_plugins(orch)
    modules_config = load_modules_config()

    # --- Уровень 1: простые и точные ---
    _try_register(orch, AgentTime, modules_config)
    _try_register(orch, AgentPower, modules_config)
    _try_register(orch, AgentTimeAgent, modules_config)
    _try_register(orch, AgentMassage, modules_config)
    _try_register(orch, AgentDictation, modules_config)
    _try_register(orch, AgentConstruction, modules_config)
    _try_register(orch, AgentBPM, modules_config)
    _try_register(orch, AgentHealth, modules_config)
    _try_register(orch, AgentVault, modules_config)

    # --- Уровень 2: узкий ducking — ДО audio_pult ---
    _try_register(orch, AgentMusicDucker, modules_config)
    _try_register(orch, AgentMusicLocal, modules_config)
    _try_register(orch, AgentMediaPause, modules_config)

    # --- Уровень 3: audio_pult — широкие ключи ---
    _try_register(orch, AgentAudioPult, modules_config)

    # --- Уровень 4: дневник, память, реестр, функции, обновления, security ---
    _try_register(orch, AgentJournal, modules_config)
    _try_register(orch, AgentRAGMemory, modules_config)
    _try_register(orch, AgentRegistry, modules_config)
    _try_register(orch, AgentFunctions, modules_config)
    _try_register(orch, AgentUpdates, modules_config)
    _try_register(orch, AgentSecurity, modules_config)

    # --- Уровень 5: аудио-маршрутизация ---
    _try_register(orch, AgentAudioRouter, modules_config)

    # --- Уровень 6: X11 специфичные ---
    _try_register(orch, AgentVision, modules_config)
    _try_register(orch, AgentFocusSwitch, modules_config)
    _try_register(orch, AgentWindowManager, modules_config)
    _try_register(orch, AgentContextMemory, modules_config)
    _try_register(orch, AgentTextEditor, modules_config)
    _try_register(orch, AgentChecklist, modules_config)
    _try_register(orch, AgentAtSpi, modules_config)
    _try_register(orch, AgentMcp, modules_config)
    _try_register(orch, AgentTelegram, modules_config)
    _try_register(orch, AgentVKWeb, modules_config)

    # --- Уровень 7: специфичные "открой X" — раньше AppLauncher ---
    # Порядок важен: browser_tabs специфичнее — «найди вкладку X»
    # должно уходить сюда, а не в vk_music (у которого SEARCH_KEYWORDS = «найди»).
    _try_register(orch, AgentBrowserTabs, modules_config)
    _try_register(orch, AgentMessenger, modules_config)
    _try_register(orch, AgentVKMusic, modules_config)

    # --- Уровень 8: опасные, но широкие ключи ---
    _try_register(orch, AgentAppLauncher, modules_config)
    _try_register(orch, AgentWindowControl, modules_config)
    _try_register(orch, AgentScreenReader, modules_config)

    # --- Уровень 9: медиа (перехватывает "включи") ---
    _try_register(orch, AgentMediaSearch, modules_config)

    # --- Уровень 10: Internet — последним (общий "найди") ---
    _try_register(orch, AgentInternet, modules_config)
    return orch


__all__ = ["build_orchestrator"]
