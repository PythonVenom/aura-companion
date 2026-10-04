"""Тесты ContextMemory."""
from __future__ import annotations
from aura.core.context import ContextMemory


def test_empty():
    c = ContextMemory()
    assert c.recent() == []


def test_add_and_recent():
    c = ContextMemory()
    c.add("cmd", "test")
    assert len(c.recent()) == 1


def test_summary_empty():
    c = ContextMemory()
    s = c.summary()
    assert "ничего" in s


def test_summary_with_events():
    c = ContextMemory()
    c.add("cmd", "открыл VSCode")
    c.add("action", "запустил тесты")
    s = c.summary()
    assert "VSCode" in s
    assert "тесты" in s


def test_maxlen():
    c = ContextMemory(maxlen=3)
    for i in range(5):
        c.add("t", str(i))
    assert len(c.events) == 3
