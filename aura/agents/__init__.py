"""
Реестр агентов Ауры.

Каждый агент — наследник BaseAgent, реализует can_handle/handle.
Добавляй новых агентов сюда по мере миграции.
"""

from aura.agents.app_launcher import AgentAppLauncher
from aura.agents.audio_pult import AgentAudioPult
from aura.agents.audio_router import AgentAudioRouter
from aura.agents.at_spi import AgentAtSpi
from aura.agents.brain import AgentBrain
from aura.agents.browser_tabs import AgentBrowserTabs
from aura.agents.checklist import AgentChecklist
from aura.agents.context_memory import AgentContextMemory
from aura.agents.focus_switch import AgentFocusSwitch
from aura.agents.functions import AgentFunctions
from aura.agents.internet import AgentInternet
from aura.agents.messenger import AgentMessenger
from aura.agents.journal import AgentJournal
from aura.agents.mcp import AgentMcp
from aura.agents.media_search import AgentMediaSearch
from aura.agents.music_ducker import AgentMusicDucker
from aura.agents.music_local import AgentMusicLocal
from aura.agents.media_pause import AgentMediaPause
from aura.agents.power import AgentPower
from aura.agents.rag_memory import AgentRAGMemory
from aura.agents.registry import AgentRegistry
from aura.agents.screen_reader import AgentScreenReader
from aura.agents.security import AgentSecurity
from aura.agents.telegram import AgentTelegram
from aura.agents.text_editor import AgentTextEditor
from aura.agents.time import AgentTime
from aura.agents.tool_router import AgentToolRouter
from aura.agents.updates import AgentUpdates
from aura.agents.vault import AgentVault
from aura.agents.vision import AgentVision
from aura.agents.vk_music import AgentVKMusic
from aura.agents.vk_web import AgentVKWeb
from aura.agents.window_control import AgentWindowControl
from aura.agents.window_manager import AgentWindowManager

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
    "AgentVault",
    "AgentSecurity",
    "AgentVision",
    "AgentFocusSwitch",
    "AgentContextMemory",
    "AgentTextEditor",
    "AgentMusicDucker",
    "AgentMusicLocal",
    "AgentMediaPause",
    "AgentWindowManager",
    "AgentAppLauncher",
    "AgentInternet",
    "AgentMessenger",
    "AgentWindowControl",
    "AgentScreenReader",
    "AgentBrowserTabs",
    "AgentMediaSearch",
    "AgentVKMusic",
    "AgentBrain",
    "AgentToolRouter",
    "AgentChecklist",
    "AgentAtSpi",
    "AgentMcp",
    "AgentTelegram",
    "AgentVKWeb",
]
