"""Episodic Memory — обёртка над AgentRAGMemory (ADR-122, слой 3).

Наука: Tulving, E. (1972). Episodic and Semantic Memory.
       Maharana, A. et al. (2024). LoCoMo — evaluating long-term memory.

Не дублируем ChromaDB — используем существующую коллекцию диалогов.
"""
from __future__ import annotations
from typing import Optional


class EpisodicMemory:
    def __init__(self) -> None:
        self._agent = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        try:
            from aura.agents.rag_memory import AgentRAGMemory
            self._agent = AgentRAGMemory()
            self._ready = bool(self._agent.check_ready())
        except Exception as e:
            print(f"⚠️ Episodic init: {e}")

    def check_ready(self) -> bool:
        return self._ready

    def remember(self, user_text: str, aura_response: str) -> str:
        if not self._ready:
            return ""
        try:
            return self._agent.remember(user_text, aura_response) or ""
        except Exception:
            return ""

    def search(self, query: str, n: int = 3) -> str:
        if not self._ready:
            return ""
        try:
            return self._agent.search(query, n_results=n) or ""
        except Exception:
            return ""

    def stats(self) -> dict:
        if not self._ready:
            return {"ready": False}
        try:
            return {"ready": True, "raw": self._agent.get_stats()}
        except Exception as e:
            return {"ready": True, "error": str(e)}


_SINGLETON: Optional[EpisodicMemory] = None


def get_episodic() -> EpisodicMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = EpisodicMemory()
    return _SINGLETON
