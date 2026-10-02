"""Spatial Memory — обёртка над context_memory (ADR-122, слой 8).

Наука: Burgess, N., Maguire, E. A. & O'Keefe, J. (2002). The Human Hippocampus
       and Spatial and Episodic Memory. Neuron, 35(4), 625-641.

Aura: где сейчас пользователь — окна, приложения, медиа-источники (X11).
"""
from __future__ import annotations
from typing import Optional


class SpatialMemory:
    def __init__(self) -> None:
        self._agent = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        try:
            from aura.agents.context_memory import AgentContextMemory
            self._agent = AgentContextMemory()
            self._ready = True
        except Exception as e:
            print(f"⚠️ Spatial init: {e}")

    def check_ready(self) -> bool:
        return self._ready

    def scan(self) -> bool:
        if not self._ready:
            return False
        try:
            return self._agent.scan_windows()
        except Exception:
            return False

    def last_media(self) -> Optional[dict]:
        if not self._ready:
            return None
        try:
            return self._agent.get_last_media_source()
        except Exception:
            return None

    def stats(self) -> dict:
        if not self._ready:
            return {"ready": False}
        return {"ready": True}


_SINGLETON: Optional[SpatialMemory] = None


def get_spatial() -> SpatialMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SpatialMemory()
    return _SINGLETON
