"""Тесты ReAct + Context + Streaming (ADR-123, 124, 127)."""
from __future__ import annotations


def test_should_use_react_multi_step():
    from aura.core.react_loop import should_use_react
    assert should_use_react("включи музыку и потом открой вк")
    assert should_use_react("сначала вк, а затем почта")
    assert should_use_react("если пойдёт дождь, закрой окно пожалуйста сейчас")  # длинное


def test_should_not_use_react_simple():
    from aura.core.react_loop import should_use_react
    assert not should_use_react("пауза")
    assert not should_use_react("который час")


def test_whitelist_no_power():
    from aura.core.react_loop import REACT_WHITELIST
    assert "power.lock" not in REACT_WHITELIST
    assert "control.pause" not in REACT_WHITELIST
    assert "music.play" in REACT_WHITELIST


def test_context_manager_build_messages():
    from aura.core.context_manager import ContextManager
    cm = ContextManager(window=5)
    cm.push("user", "привет")
    cm.push("aura", "привет")
    msgs = cm.build_messages("как дела")
    assert msgs[-1] == {"role": "user", "content": "как дела"}
    assert msgs[0]["role"] == "system"


def test_context_manager_priority_recall():
    from aura.core.context_manager import ContextManager
    from aura.core.memory.recall import MemoryHit
    cm = ContextManager(window=5)
    hits = [MemoryHit("semantic", 0.9,
                      {"subject": "батя", "predicate": "PREFERS", "object": "Чайковский"})]
    msgs = cm.build_messages("что любит батя", recall_hits=hits)
    sys_msgs = [m for m in msgs if m["role"] == "system"]
    assert any("Чайковский" in m["content"] for m in sys_msgs)


def test_streaming_imports():
    from aura.core.inference import stream_chat, generate
    assert callable(stream_chat)
    assert callable(generate)


def test_react_loop_smoke():
    """ReAct не падает без LLM — graceful."""
    from aura.core.react_loop import react_loop
    r = react_loop("который час", max_iterations=1)
    assert "answer" in r
    assert "steps" in r
    assert "iterations" in r
