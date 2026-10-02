"""Memory layers (ADR-122, 10 слоёв).

Реализовано в v4.0-alpha:
- Working  (кольцевой буфер, Baddeley & Hitch 1974)
- Semantic (SPO facts + confidence, Tulving 1972 + MIRIX 2025)
- Social   (family graph, SocialMemBench 2026)

Обёртки над существующим (v4.0-beta):
- Episodic  → AgentRAGMemory
- Prospective → care.py
- Emotional → journal_mood.py
- Spatial   → context_memory.py

v5.0:
- Meta (confidence calibration, MetaMem 2026)
- Consolidator (Ebbinghaus decay, ZenBrain 2025)
"""
from __future__ import annotations

from aura.core.memory.working import WorkingMemory, get_working
from aura.core.memory.semantic import SemanticMemory, get_semantic
from aura.core.memory.social import SocialMemory, get_social
from aura.core.memory.recall import recall, recall_all

__all__ = [
    "WorkingMemory", "get_working",
    "SemanticMemory", "get_semantic",
    "SocialMemory", "get_social",
    "recall", "recall_all",
]
