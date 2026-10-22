"""MemoryHub — централизованный доступ к 7 слоям памяти AURA.

Наука: Complementary Learning Systems (McClelland 1995),
       Atkinson-Shiffrin (1968) — сенсорная, краткосрочная, долгосрочная.

Слои:
1. WorkingMemory   — текущий диалог (последние N ходов)
2. EpisodicMemory  — события с временными метками
3. SemanticMemory  — факты (subject-predicate-object)
4. EmotionalMemory — эмоциональная окраска
5. ProspectiveMemory — намерения («позвонить бате в 20:00»)
6. SocialMemory    — люди и отношения
7. SpatialMemory   — локации (комнаты, устройства)
"""
from __future__ import annotations

from typing import Any


class MemoryHub:
    """Единая точка доступа ко всем слоям памяти."""

    def __init__(self) -> None:
        self._working = None
        self._episodic = None
        self._semantic = None
        self._emotional = None
        self._prospective = None
        self._social = None
        self._spatial = None
        self._init_layers()

    def _init_layers(self) -> None:
        try:
            from aura.core.memory.working import WorkingMemory
            self._working = WorkingMemory()
        except Exception:
            pass
        try:
            from aura.core.memory.episodic import EpisodicMemory
            self._episodic = EpisodicMemory()
        except Exception:
            pass
        try:
            from aura.core.memory.semantic import get_semantic
            self._semantic = get_semantic()
        except Exception:
            pass
        try:
            from aura.core.memory.emotional import EmotionalMemory
            self._emotional = EmotionalMemory()
        except Exception:
            pass
        try:
            from aura.core.memory.prospective import ProspectiveMemory
            self._prospective = ProspectiveMemory()
        except Exception:
            pass
        try:
            from aura.core.memory.social import SocialMemory
            self._social = SocialMemory()
        except Exception:
            pass
        try:
            from aura.core.memory.spatial import SpatialMemory
            self._spatial = SpatialMemory()
        except Exception:
            pass

    @property
    def working(self) -> Any:
        return self._working

    @property
    def episodic(self) -> Any:
        return self._episodic

    @property
    def semantic(self) -> Any:
        return self._semantic

    @property
    def emotional(self) -> Any:
        return self._emotional

    @property
    def prospective(self) -> Any:
        return self._prospective

    @property
    def social(self) -> Any:
        return self._social

    @property
    def spatial(self) -> Any:
        return self._spatial

    def stats(self) -> dict[str, bool]:
        """Какие слои загружены."""
        return {
            "working": self._working is not None,
            "episodic": self._episodic is not None,
            "semantic": self._semantic is not None,
            "emotional": self._emotional is not None,
            "prospective": self._prospective is not None,
            "social": self._social is not None,
            "spatial": self._spatial is not None,
        }


_HUB: MemoryHub | None = None


def get_hub() -> MemoryHub:
    """Singleton MemoryHub."""
    global _HUB
    if _HUB is None:
        _HUB = MemoryHub()
    return _HUB


__all__ = ["MemoryHub", "get_hub"]
