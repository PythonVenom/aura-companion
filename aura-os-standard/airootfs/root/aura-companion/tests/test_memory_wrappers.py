"""Тесты wrappers + extractor (ADR-122)."""
from __future__ import annotations


def test_working_ok():
    from aura.core.memory import get_working
    w = get_working()
    assert w.capacity == 20


def test_recall_all_has_7_sources():
    from aura.core.memory import recall_all
    r = recall_all()
    for key in ("working", "semantic", "social", "episodic",
                "prospective", "emotional", "spatial"):
        assert key in r


def test_episodic_ready_flag():
    from aura.core.memory.episodic import get_episodic
    e = get_episodic()
    assert isinstance(e.check_ready(), bool)


def test_prospective_tasks_list():
    from aura.core.memory.prospective import get_prospective
    p = get_prospective()
    assert isinstance(p.tasks(), list)


def test_emotional_stats_shape():
    from aura.core.memory.emotional import get_emotional
    st = get_emotional().stats(days=7)
    assert "ready" in st


def test_spatial_ready_flag():
    from aura.core.memory.spatial import get_spatial
    s = get_spatial()
    assert isinstance(s.check_ready(), bool)


def test_extractor_returns_lists_on_failure():
    """LLM может быть недоступен — extractor не должен падать."""
    from aura.core.memory.extractor import extract_semantic, extract_social
    assert isinstance(extract_semantic("тест"), list)
    r = extract_social("тест")
    assert set(r.keys()) == {"entities", "relations", "events"}


def test_recall_returns_working_first():
    from aura.core.memory import recall
    from aura.core.memory.working import get_working
    get_working().clear()
    get_working().push("user", "hello")
    hits = recall("hello", n=3)
    assert hits
    assert hits[0].source == "working"
