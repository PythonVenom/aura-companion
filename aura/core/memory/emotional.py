"""Emotional Memory — обёртка над journal_mood (ADR-122, слой 7).

Наука: McGaugh, J. L. (2004). The amygdala modulates the consolidation of memories.
       Annual Review of Neuroscience, 27, 1-28.

Aura: эмоциональная валентность диалога, настроение пользователя за период.
"""
from __future__ import annotations
from typing import Optional


class EmotionalMemory:
    def __init__(self) -> None:
        self._agent = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        try:
            from aura.agents.journal_mood import VoiceJournal
            self._agent = VoiceJournal()
            self._ready = True
        except Exception as e:
            print(f"⚠️ Emotional init: {e}")

    def check_ready(self) -> bool:
        return self._ready

    def add(self, text: str, mood: Optional[float] = None) -> bool:
        if not self._ready:
            return False
        try:
            self._agent.add(text, mood)
            return True
        except Exception:
            return False

    def stats(self, days: int = 7) -> dict:
        if not self._ready:
            return {"ready": False}
        try:
            s = self._agent.stats_last_days(days)
            return {"ready": True, **s}
        except Exception as e:
            return {"ready": True, "error": str(e)}


_SINGLETON: Optional[EmotionalMemory] = None


def get_emotional() -> EmotionalMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = EmotionalMemory()
    return _SINGLETON
