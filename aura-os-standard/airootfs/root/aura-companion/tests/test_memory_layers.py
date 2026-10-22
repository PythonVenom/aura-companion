"""Тесты 10-слойной памяти (ADR-122)."""
from __future__ import annotations
import tempfile
from pathlib import Path


def test_working_push_and_last():
    from aura.core.memory.working import WorkingMemory
    w = WorkingMemory(capacity=5)
    for i in range(7):
        w.push("user", f"msg{i}")
    assert len(w) == 5
    assert w.last(1)[0].text == "msg6"


def test_working_as_messages():
    from aura.core.memory.working import WorkingMemory
    w = WorkingMemory()
    w.push("user", "привет")
    w.push("aura", "привет")
    msgs = w.as_messages(2)
    assert msgs == [
        {"role": "user", "content": "привет"},
        {"role": "assistant", "content": "привет"},
    ]


def test_semantic_fact_dataclass():
    from aura.core.memory.semantic import Fact
    f = Fact(subject="батя", predicate="PREFERS", object="Чайковский")
    assert f.to_text() == "батя PREFERS Чайковский"
    assert f.confidence == 1.0


def test_social_sqlite(tmp_path):
    from aura.core.memory.social import SocialMemory
    db = tmp_path / "social_test.db"
    s = SocialMemory(db_path=db)
    assert s.check_ready()
    s.add_relation("батя", "PREFERS", "Чайковский", weight=0.9)
    rels = s.relations_of("батя", kind="PREFERS")
    assert len(rels) == 1
    assert rels[0].dst == "Чайковский"
    s.add_event("мама", "birthday", "2026-05-15")
    evs = s.events_of("мама")
    assert len(evs) == 1 and evs[0]["kind"] == "birthday"


def test_social_entity_dedup(tmp_path):
    from aura.core.memory.social import SocialMemory
    s = SocialMemory(db_path=tmp_path / "s.db")
    id1 = s.upsert_entity("батя")
    id2 = s.upsert_entity("батя")
    assert id1 == id2


def test_recall_all_smoke():
    from aura.core.memory.recall import recall_all
    r = recall_all()
    assert "working" in r
    assert "semantic" in r
    assert "social" in r


def test_recall_returns_hits():
    from aura.core.memory.recall import recall
    from aura.core.memory.working import get_working
    get_working().push("user", "поговорим про Чайковского")
    hits = recall("Чайковский", n=5)
    assert isinstance(hits, list)
    assert all(hasattr(h, "source") for h in hits)
