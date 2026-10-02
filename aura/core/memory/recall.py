"""Recall — единая точка запроса памяти (ADR-122).

Опрашивает слои → объединяет → ранжирует.

Наука:
- Ebbinghaus, H. (1885). Über das Gedächtnis. (recency decay)
- McGaugh, J. L. (2004). The amygdala modulates memory consolidation.
- Liu, N. F. et al. (2023). Lost in the Middle. TACL.

Слои:
1. Working      — свежее
2. Episodic     — диалоги (AgentRAGMemory)
3. Semantic     — факты SPO
4. Prospective  — задачи/напоминания (care)
5. Emotional    — настроение (journal)
6. Spatial      — окна/apps (X11)
7. Social       — граф семьи (ADR-125)
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass


@dataclass
class MemoryHit:
    source: str
    score: float
    payload: dict


def _recency_score(ts: float, halflife_days: float = 30.0) -> float:
    if ts <= 0:
        return 1.0
    age_days = (time.time() - ts) / 86400.0
    return math.exp(-age_days * math.log(2) / halflife_days)


def recall(query: str, n: int = 8) -> list[MemoryHit]:
    hits: list[MemoryHit] = []

    # 1. Working
    try:
        from aura.core.memory.working import get_working
        for i, turn in enumerate(get_working().last(10)):
            hits.append(MemoryHit("working", 1.0 - i * 0.02,
                                  {"role": turn.role, "text": turn.text}))
    except Exception:
        pass

    # 3. Semantic
    try:
        from aura.core.memory.semantic import get_semantic
        s = get_semantic()
        if s.check_ready():
            for f in s.search(query, n=n):
                hits.append(MemoryHit("semantic",
                    0.6 * f.confidence + 0.4 * _recency_score(f.ts),
                    {"subject": f.subject, "predicate": f.predicate,
                     "object": f.object, "confidence": f.confidence}))
    except Exception:
        pass

    # 7. Social (только если упоминается известное имя)
    try:
        from aura.core.memory.social import get_social
        s = get_social()
        if s.check_ready():
            ql = query.lower()
            for ent in s.entities():
                name_l = ent.name.lower()
                if name_l and name_l in ql:
                    for r in s.relations_of(ent.name):
                        hits.append(MemoryHit("social", 0.8 + 0.2 * r.weight,
                            {"src": r.src, "kind": r.kind, "dst": r.dst,
                             "evidence": r.evidence}))
                    for ev in s.events_of(ent.name):
                        hits.append(MemoryHit("social", 0.7,
                            {"event": ev["kind"], "date": ev["date"],
                             "of": ent.name}))
    except Exception:
        pass

    # 6. Emotional (последние N дней)
    try:
        from aura.core.memory.emotional import get_emotional
        e = get_emotional()
        if e.check_ready():
            st = e.stats(days=7)
            if st.get("count", 0) > 0:
                hits.append(MemoryHit("emotional", 0.5,
                                      {"mood_avg": st.get("avg"), "count": st["count"]}))
    except Exception:
        pass

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:n]


def recall_all() -> dict:
    """Сводка состояния всех слоёв (для doctor/smoke)."""
    out: dict = {}
    for name, getter in [
        ("working", "from aura.core.memory.working import get_working; w=get_working(); r={'len':len(w)}"),
        ("semantic", "from aura.core.memory.semantic import get_semantic; r=get_semantic().stats()"),
        ("social", "from aura.core.memory.social import get_social; r=get_social().stats()"),
        ("episodic", "from aura.core.memory.episodic import get_episodic; r=get_episodic().stats()"),
        ("prospective", "from aura.core.memory.prospective import get_prospective; r=get_prospective().stats()"),
        ("emotional", "from aura.core.memory.emotional import get_emotional; r=get_emotional().stats()"),
        ("spatial", "from aura.core.memory.spatial import get_spatial; r=get_spatial().stats()"),
    ]:
        try:
            ns: dict = {}
            exec(getter, ns)
            out[name] = ns["r"]
        except Exception as e:
            out[name] = {"error": str(e)}
    return out
