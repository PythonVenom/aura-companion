"""Тесты для aura/core/logbook.py — бортовой журнал (ADR-084)."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
import pytest
from aura.core.logbook import Logbook, LogEntry


@pytest.fixture
def lb(tmp_path):
    return Logbook(root=tmp_path)


def test_log_event(lb, tmp_path):
    lb.event("commit", "feat: test", {"files": ["a.py"]})
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1


def test_log_decision(lb, tmp_path):
    lb.decision("use_http", "HTTP API для всех клиентов", adr="ADR-079")
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1


def test_log_unresolved(lb, tmp_path):
    lb.unresolved("Bug 67 в мониторинге", "24ч мониторинг")
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1


def test_read_today(lb):
    lb.event("a", "event1")
    lb.event("b", "event2")
    lb.decision("c", "dec1")
    today = lb.read_today()
    assert len(today) >= 3


def test_markdown_today(lb):
    lb.event("commit", "feat: x")
    lb.decision("use_x", "почему x")
    md = lb.markdown_today()
    assert "commit" in md.lower()
    assert "use_x" in md or "decisions" in md.lower()


def test_rotate_no_growth(lb, tmp_path):
    for i in range(100):
        lb.event("tick", f"event {i}")
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 1  # один файл на день


def test_search_by_tag(lb):
    lb.event("commit", "feat: a", {"tag": "widget"})
    lb.event("commit", "fix: b", {"tag": "api"})
    results = lb.search(tag="widget")
    assert len(results) >= 1
