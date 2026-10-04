"""Тесты для aura/core/chat_bridge.py — file-based IPC для чата."""
from __future__ import annotations

import json

import pytest

from aura.core.chat_bridge import ChatBridge


@pytest.fixture
def bridge(tmp_path):
    return ChatBridge(
        inbox_path=tmp_path / "chat_inbox.jsonl",
        history_path=tmp_path / "chat_history.jsonl",
    )


def test_read_new_empty(bridge):
    assert bridge.read_new() == []


def test_read_new_one_line(bridge, tmp_path):
    (tmp_path / "chat_inbox.jsonl").write_text(
        '{"user":"hi","ts":1}\n', encoding="utf-8"
    )
    msgs = bridge.read_new()
    assert len(msgs) == 1
    assert msgs[0]["user"] == "hi"


def test_read_new_tracks_offset(bridge, tmp_path):
    (tmp_path / "chat_inbox.jsonl").write_text(
        '{"user":"a","ts":1}\n', encoding="utf-8"
    )
    bridge.read_new()
    assert bridge.read_new() == []


def test_read_new_incremental(bridge, tmp_path):
    inbox = tmp_path / "chat_inbox.jsonl"
    inbox.write_text('{"user":"a","ts":1}\n', encoding="utf-8")
    bridge.read_new()
    with open(inbox, "a", encoding="utf-8") as f:
        f.write('{"user":"b","ts":2}\n')
    msgs = bridge.read_new()
    assert len(msgs) == 1
    assert msgs[0]["user"] == "b"


def test_read_new_skips_malformed(bridge, tmp_path):
    (tmp_path / "chat_inbox.jsonl").write_text(
        'garbage\n{"user":"ok","ts":1}\n', encoding="utf-8"
    )
    msgs = bridge.read_new()
    assert len(msgs) == 1
    assert msgs[0]["user"] == "ok"


def test_append_history(bridge, tmp_path):
    bridge.append_history("hello", "world")
    lines = (tmp_path / "chat_history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    d = json.loads(lines[0])
    assert d["user"] == "hello"
    assert d["aura"] == "world"
    assert "ts" in d


def test_append_history_multiple(bridge, tmp_path):
    bridge.append_history("a", "1")
    bridge.append_history("b", "2")
    lines = (tmp_path / "chat_history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_append_history_creates_parent(bridge, tmp_path):
    bridge.append_history("x", "y")
    assert (tmp_path / "chat_history.jsonl").exists()
