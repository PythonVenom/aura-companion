"""#11 Curiosity Engine — тесты."""
from __future__ import annotations

import sqlite3
import time

import pytest

from aura.core import curiosity as C


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "DB", tmp_path / "curiosity.db")
    yield


@pytest.fixture
def engine():
    return C.CuriosityEngine()


# === register_gap ===

def test_register_new_gap(engine):
    g = engine.register_gap("тема 1", importance=0.7)
    assert g.topic == "тема 1"
    assert g.confidence == 0.0
    assert g.importance == 0.7


def test_register_normalizes_topic(engine):
    g = engine.register_gap("  ТЕМА  " , importance=0.5)
    assert g.topic == "тема"


def test_register_empty_topic_raises(engine):
    with pytest.raises(ValueError):
        engine.register_gap("")


def test_register_clamps_importance_high(engine):
    g = engine.register_gap("x", importance=5.0)
    assert g.importance == 1.0


def test_register_clamps_importance_low(engine):
    g = engine.register_gap("x", importance=-2.0)
    assert g.importance == 0.0


def test_register_existing_keeps_max_importance(engine):
    engine.register_gap("x", importance=0.9)
    g = engine.register_gap("x", importance=0.3)  # не понижаем
    assert g.importance == 0.9


def test_register_existing_bumps_importance(engine):
    engine.register_gap("x", importance=0.3)
    g = engine.register_gap("x", importance=0.9)
    assert g.importance == 0.9


# === pick_question ===

def test_pick_empty(engine):
    assert engine.pick_question() is None


def test_pick_returns_gap(engine):
    engine.register_gap("how to fly", importance=0.9)
    g = engine.pick_question()
    assert g is not None
    assert g.topic == "how to fly"


def test_pick_highest_priority(engine):
    engine.register_gap("low", importance=0.3)
    engine.register_gap("high", importance=0.9)
    g = engine.pick_question()
    assert g.topic == "high"


def test_pick_respects_cooldown(engine):
    """Свежезаданный вопрос не выбирается повторно."""
    engine.register_gap("x", importance=0.9)
    engine.record_answer("x")  # только что спросили
    g = engine.pick_question()
    assert g is None


def test_pick_respects_threshold(engine):
    """Слишком низкий приоритет не выбирается."""
    engine.register_gap("x", importance=0.1)
    # priority = 0.1 * 1.0 * min(1, 999/24) = 0.1 → < 0.2
    assert engine.pick_question() is None


# === record_answer ===

def test_record_answer_bumps_confidence(engine):
    engine.register_gap("x")
    assert engine.record_answer("x", confidence_delta=0.5) is True
    gaps = engine.list_gaps()
    assert gaps[0].confidence == 0.5


def test_record_answer_clamps_at_one(engine):
    engine.register_gap("x")
    engine.record_answer("x", confidence_delta=0.9)
    engine.record_answer("x", confidence_delta=0.9)
    assert engine.list_gaps()[0].confidence == 1.0


def test_record_answer_increments_count(engine):
    engine.register_gap("x")
    engine.record_answer("x")
    engine.record_answer("x")
    assert engine.list_gaps()[0].ask_count == 2


def test_record_answer_unknown_topic(engine):
    assert engine.record_answer("nonexistent") is False


# === list_gaps ===

def test_list_gaps_empty(engine):
    assert engine.list_gaps() == []


def test_list_gaps_returns_all(engine):
    engine.register_gap("a")
    engine.register_gap("b")
    engine.register_gap("c")
    assert len(engine.list_gaps()) == 3


# === stats ===

def test_stats_empty(engine):
    s = engine.stats()
    assert s["total"] == 0
    assert s["known"] == 0
    assert s["unknown"] == 0


def test_stats_classifies_known_unknown(engine):
    engine.register_gap("known")
    engine.register_gap("unknown")
    engine.record_answer("known", confidence_delta=0.9)  # → 0.9, known
    s = engine.stats()
    assert s["total"] == 2
    assert s["known"] == 1
    assert s["unknown"] == 1


def test_stats_avg_confidence(engine):
    engine.register_gap("a")
    engine.register_gap("b")
    engine.record_answer("a", confidence_delta=0.6)
    s = engine.stats()
    assert s["avg_confidence"] == 0.3  # (0.6 + 0.0) / 2


# === forget ===

def test_forget_existing(engine):
    engine.register_gap("x")
    assert engine.forget("x") is True
    assert engine.list_gaps() == []


def test_forget_unknown(engine):
    assert engine.forget("nope") is False


# === Gap.priority ===

def test_gap_priority_formula():
    g = C.Gap(topic="x", confidence=0.5, importance=1.0, last_asked=0.0)
    # age_hours огромный → recency=1.0, ignorance=0.5, priority=0.5
    p = g.priority()
    assert abs(p - 0.5) < 0.01


def test_gap_priority_zero_when_known():
    g = C.Gap(topic="x", confidence=1.0, importance=1.0, last_asked=0.0)
    assert g.priority() == 0.0


def test_gap_priority_grows_with_age():
    now = time.time()
    fresh = C.Gap(topic="x", confidence=0.5, importance=1.0, last_asked=now)
    old = C.Gap(topic="x", confidence=0.5, importance=1.0, last_asked=now - 48*3600)
    assert old.priority(now) > fresh.priority(now)
