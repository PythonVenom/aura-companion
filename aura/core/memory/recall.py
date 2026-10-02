"""Recall — единая точка запроса памяти (ADR-122).

Опрашивает слои → объединяет → ранжирует.

Наука:
- Ebbinghaus, H. (1885). Über das Gedächtnis. (recency decay)
- McGaugh, J. L. (2004). The amygdala modulates the consolidation of memories.
  Annual Review of Neuroscience, 27, 1-28. (emotional weight)
- Liu, N. F. et al. (2023). Lost in the Middle: How Language Models Use Long Contexts.
  TACL. (порядок имеет значение)

Возвращает ранжированный список (score, source, payload).
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass


@dataclass
class MemoryHit:
    source: str          # "working"|"semantic"|"social"
    score: float
    payload: dict


def _recency_score(ts: float, halflife_days: float = 30.0) -> float:
    """Ebbinghaus-style exponential decay."""
    if ts <= 0:
        return 1.0
    age_days = (time.time() - ts) / 86400.0
    return math.exp(-age_days * math.log(2) / halflife_days)


def recall(query: str, n: int = 8) -> list[MemoryHit]:
    """Опросить слои и вернуть top-n ранжированных."""
    hits: list[MemoryHit] = []

    # Working (всегда самое свежее)
    try:
        from aura.core.memory.working import get_working
        w = get_working()
        for i, turn in enumerate(w.last(10)):
            hits.append(MemoryHit(
                source="working", score=1.0 - i * 0.02,
                payload={"role": turn.role, "text": turn.text},
            ))
    except Exception:
        pass

    # Semantic (факты, embedding + recency)
    try:
        from aura.core.memory.semantic import get_semantic
        s = get_semantic()
        for f in s.search(query, n=n):
            rel = f.confidence
            rec = _recency_score(f.ts)
            hits.append(MemoryHit(
                source="semantic", score=0.6 * rel + 0.4 * rec,
                payload={"subject": f.subject, "predicate": f.predicate,
                         "object": f.object, "confidence": f.confidence},
            ))
    except Exception:
        pass

    # Social (граф — только если запрос упоминает известное имя)
    try:
        from aura.core.memory.social import get_social
        s = get_social()
        names = [e.name.lower() for e in s.entities()]
        ql = query.lower()
        for name in names:
            if name and name in ql:
                for r in s.relations_of(name.capitalize() if name.islower() else name):
                    hits.append(MemoryHit(
                        source="social", score=0.8 + 0.2 * r.weight,
                        payload={"src": r.src, "kind": r.kind, "dst": r.dst,
                                 "evidence": r.evidence},
                    ))
                for ev in s.events_of(name.capitalize() if name.islower() else name):
                    hits.append(MemoryHit(
                        source="social", score=0.7,
                        payload={"event": ev["kind"], "date": ev["date"], "of": name},
                    ))
    except Exception:
        pass

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:n]


def recall_all() -> dict:
    """Сводка состояния всех слоёв (для doctor/smoke)."""
    out: dict = {}
    try:
        from aura.core.memory.working import get_working
        out["working"] = {"len": len(get_working())}
    except Exception as e:
        out["working"] = {"error": str(e)}
    try:
        from aura.core.memory.semantic import get_semantic
        out["semantic"] = get_semantic().stats()
    except Exception as e:
        out["semantic"] = {"error": str(e)}
    try:
        from aura.core.memory.social import get_social
        out["social"] = get_social().stats()
    except Exception as e:
        out["social"] = {"error": str(e)}
    return out
