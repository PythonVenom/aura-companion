"""Тесты для aura/core/chat_watcher.py — thread читает inbox → queue."""
from __future__ import annotations

import json
import queue
import time

import pytest

from aura.core.chat_bridge import ChatBridge
from aura.core.chat_watcher import ChatWatcher


@pytest.fixture
def bridge(tmp_path):
    return ChatBridge(
        inbox_path=tmp_path / "i.jsonl",
        history_path=tmp_path / "h.jsonl",
    )


def test_watcher_starts_and_stops(bridge):
    q = queue.Queue()
    w = ChatWatcher(bridge, q, interval=0.05)
    w.start()
    assert w.is_alive()
    w.stop()
    time.sleep(0.1)
    assert not w.is_alive()


def test_watcher_reads_new_message(bridge, tmp_path):
    q = queue.Queue()
    w = ChatWatcher(bridge, q, interval=0.05)
    w.start()
    (tmp_path / "i.jsonl").write_text(
        '{"user":"hi","ts":1}\n', encoding="utf-8"
    )
    time.sleep(0.2)
    w.stop()
    assert not q.empty()
    msg = q.get_nowait()
    assert msg["user"] == "hi"


def test_watcher_reads_multiple(bridge, tmp_path):
    q = queue.Queue()
    w = ChatWatcher(bridge, q, interval=0.05)
    w.start()
    (tmp_path / "i.jsonl").write_text(
        '{"user":"a","ts":1}\n{"user":"b","ts":2}\n', encoding="utf-8"
    )
    time.sleep(0.25)
    w.stop()
    count = 0
    while not q.empty():
        q.get_nowait()
        count += 1
    assert count == 2


def test_watcher_does_not_duplicate(bridge, tmp_path):
    q = queue.Queue()
    w = ChatWatcher(bridge, q, interval=0.05)
    w.start()
    (tmp_path / "i.jsonl").write_text(
        '{"user":"x","ts":1}\n', encoding="utf-8"
    )
    time.sleep(0.25)
    w.stop()
    count = 0
    while not q.empty():
        q.get_nowait()
        count += 1
    assert count == 1


def test_watcher_survives_bridge_error(bridge, tmp_path, monkeypatch):
    q = queue.Queue()
    w = ChatWatcher(bridge, q, interval=0.05)
    call_count = {"n": 0}
    real_read = bridge.read_new
    def flaky():
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("boom")
        return real_read()
    monkeypatch.setattr(bridge, "read_new", flaky)
    w.start()
    time.sleep(0.2)
    assert w.is_alive()  # не умерла от ошибки
    w.stop()
