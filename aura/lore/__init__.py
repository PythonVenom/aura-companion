"""Лор Ауры: терминология, персона, бортовой журнал."""
from aura.lore.persona import LINES, PHRASES, speak_line
from aura.lore.story import StoryLog, get_briefing
from aura.lore.terminology import TERMS, translate

__all__ = [
    "LINES",
    "PHRASES",
    "TERMS",
    "StoryLog",
    "get_briefing",
    "speak_line",
    "translate",
]
