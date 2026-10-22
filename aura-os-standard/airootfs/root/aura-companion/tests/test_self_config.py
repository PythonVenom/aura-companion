"""Тесты self-configuration (ADR-153)."""
from __future__ import annotations


def test_profiler_record():
    from aura.core.profiler import Profiler
    p = Profiler()
    for _ in range(10):
        p.record("llm", 500)
    assert p.p50("llm") == 500


def test_profiler_slow():
    from aura.core.profiler import Profiler
    p = Profiler()
    for _ in range(10):
        p.record("llm", 5000)
    assert p.is_slow("llm")


def test_lru_cache():
    from aura.core.caches import LRUCache
    c = LRUCache(maxsize=3)
    c.put("a", 1); c.put("b", 2); c.put("c", 3); c.put("d", 4)
    assert c.get("a") is None and c.get("d") == 4


def test_caches_module():
    from aura.core.caches import emb_put, emb_get, stats
    emb_put("hello", [0.1])
    assert emb_get("hello") == [0.1]
    assert "embeddings" in stats()
