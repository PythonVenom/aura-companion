"""Тесты Tier 0 (ADR-152)."""
from __future__ import annotations
import time


def test_intents_count():
    from aura.core.intent_classifier import all_intents
    assert len(all_intents()) >= 20


def test_intent_music():
    from aura.core.intent_classifier import classify
    i, _ = classify("включи музыку")
    assert i == "music.play"


def test_intent_time():
    from aura.core.intent_classifier import classify
    i, _ = classify("который час")
    assert i == "time.now"


def test_intent_emergency():
    from aura.core.intent_classifier import classify
    i, _ = classify("мне плохо")
    assert i == "emergency"


def test_templates_count():
    from aura.core.templates import count
    assert count() >= 20


def test_templates_time():
    from aura.core.templates import render_now
    r = render_now("time.now")
    assert ":" in r


def test_tier0_music():
    from aura.core.tier0_orchestrator import get_tier0
    r = get_tier0().process("включи музыку")
    assert r.intent == "music.play"


def test_tier0_emergency():
    """Emergency intent — либо constitution (crisis), либо template (emergency)."""
    from aura.core.tier0_orchestrator import get_tier0
    r = get_tier0().process("мне плохо")
    # "мне плохо" → emergency intent → template "Вызываю помощь"
    # "не хочу жить" → constitution rule 5 → телефон доверия
    assert r.source in ("constitution", "template", "dispatcher")
    assert r.intent == "emergency" or r.source == "constitution"


def test_tier0_crisis_constitution():
    """Crisis keywords должны идти через constitution."""
    from aura.core.tier0_orchestrator import get_tier0
    r = get_tier0().process("не хочу жить")
    assert r.source == "constitution"


def test_tier0_fast():
    from aura.core.tier0_orchestrator import get_tier0
    t0 = get_tier0()
    start = time.time()
    for _ in range(10):
        t0.process("который час")
    elapsed = (time.time() - start) / 10 * 1000
    assert elapsed < 50, f"too slow: {elapsed:.1f}ms"
