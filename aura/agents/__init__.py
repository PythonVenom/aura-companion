"""
Реестр агентов Ауры.

Каждый агент — наследник BaseAgent, реализует can_handle/handle.
Добавляй новых агентов сюда по мере миграции.
"""

from aura.agents.app_launcher import AgentAppLauncher
from aura.agents.audio_pult import AgentAudioPult
from aura.agents.audio_router import AgentAudioRouter
from aura.agents.browser_tabs import AgentBrowserTabs
from aura.agents.functions import AgentFunctions
from aura.agents.internet import AgentInternet
from aura.agents.journal import AgentJournal
from aura.agents.media_search import AgentMediaSearch
from aura.agents.power import AgentPower
from aura.agents.rag_memory import AgentRAGMemory
from aura.agents.registry import AgentRegistry
from aura.agents.screen_reader import AgentScreenReader
from aura.agents.time import AgentTime
from aura.agents.updates import AgentUpdates
from aura.agents.vk_music import AgentVKMusic
from aura.agents.window_control import AgentWindowControl
from aura.agents.brain import AgentBrain
from aura.agents.tool_router import AgentToolRouter

__all__ = [
    "AgentTime",
    "AgentPower",
    "AgentAudioPult",
    "AgentAudioRouter",
    "AgentJournal",
    "AgentRAGMemory",
    "AgentFunctions",
    "AgentUpdates",
    "AgentRegistry",
    "AgentAppLauncher",
    "AgentInternet",
    "AgentWindowControl",
    "AgentScreenReader",
    "AgentBrowserTabs",
    "AgentMediaSearch",
    "AgentVKMusic",
    "AgentBrain",
    "AgentToolRouter",
]
