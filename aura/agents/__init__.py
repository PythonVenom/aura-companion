"""
Реестр агентов Ауры.

Каждый агент — наследник BaseAgent, реализует can_handle/handle.
Добавляй новых агентов сюда по мере миграции.
"""

from aura.agents.audio_pult import AgentAudioPult
from aura.agents.power import AgentPower
from aura.agents.time import AgentTime

__all__ = [
    "AgentTime",
    "AgentPower",
    "AgentAudioPult",
]
