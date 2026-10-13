"""T016 — тесты для aura.core.notifications."""
from __future__ import annotations

import sqlite3
from unittest.mock import patch

import pytest

from aura.core import notifications as n


def test_levels_order():
    """P0 < P1 < P2 < P3 по важности."""
    assert n.NotifLevel.P0 < n.NotifLevel.P1 < n.NotifLevel.P2 < n.NotifLevel.P3


def test_levels_values():
    assert int(n.NotifLevel.P0) == 0
    assert int(n.NotifLevel.P1) == 1
    assert int(n.NotifLevel.P2) == 2
    assert int(n.NotifLevel.P3) == 3


@pytest.mark.parametrize("priority,expected", [
    (100, n.NotifLevel.P0),
    (95, n.NotifLevel.P0),
    (90, n.NotifLevel.P0),
    (89, n.NotifLevel.P1),
    (70, n.NotifLevel.P1),
    (69, n.NotifLevel.P2),
    (40, n.NotifLevel.P2),
    (39, n.NotifLevel.P3),
    (0, n.NotifLevel.P3),
])
def test_from_priority(priority, expected):
    assert n.from_priority(priority) == expected


def test_urgency_mapping():
    """P0 → critical, P1/P2 → normal, P3 → low."""
    assert n._URGENCY[n.NotifLevel.P0] == "critical"
    assert n._URGENCY[n.NotifLevel.P1] == "normal"
    assert n._URGENCY[n.NotifLevel.P2] == "normal"
    assert n._URGENCY[n.NotifLevel.P3] == "low"


def test_notify_calls_notify_send(tmp_path, monkeypatch):
    """Проверяем, что notify-send вызывается с правильными аргументами."""
    monkeypatch.setattr(n, "DB", tmp_path / "notif.db")
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return None

    with patch("aura.core.notifications.shutil.which", return_value="/usr/bin/notify-send"):
        with patch("aura.core.notifications.subprocess.run", side_effect=fake_run):
            result = n.notify(n.NotifLevel.P0, "SOS", "Падение!", agent="fall")

    assert result is True
    assert len(calls) == 1
    args = calls[0]
    assert args[0] == "notify-send"
    assert "-a" in args and "Aura" in args
    assert "-u" in args and "critical" in args
    assert "SOS" in args
    assert "Падение!" in args


def test_notify_no_notify_send(tmp_path, monkeypatch):
    """Если notify-send нет — вернуть False, не падать."""
    monkeypatch.setattr(n, "DB", tmp_path / "notif.db")
    with patch("aura.core.notifications.shutil.which", return_value=None):
        result = n.notify(n.NotifLevel.P1, "test", "body")
    assert result is False


def test_notify_logs_to_db(tmp_path, monkeypatch):
    """Каждое уведомление пишется в историю."""
    db = tmp_path / "notif.db"
    monkeypatch.setattr(n, "DB", db)

    with patch("aura.core.notifications.shutil.which", return_value=None):
        n.notify(n.NotifLevel.P2, "hello", "world", agent="test_agent")

    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT level, agent, title, body, delivered FROM history"
    ).fetchone()
    conn.close()
    assert row == (2, "test_agent", "hello", "world", 0)


def test_notify_never_crashes_on_db_error(tmp_path, monkeypatch):
    """Даже если БД сломана — notify не падает."""
    monkeypatch.setattr(n, "DB", tmp_path / "sub" / ".." / "x" / "y.db")
    # Принудительно ломаем sqlite3.connect
    with patch("aura.core.notifications.sqlite3.connect", side_effect=sqlite3.OperationalError("boom")):
        with patch("aura.core.notifications.shutil.which", return_value=None):
            result = n.notify(n.NotifLevel.P0, "x", "y")
    assert result is False  # не упало, вернуло False


def test_notify_returns_true_when_delivered(tmp_path, monkeypatch):
    monkeypatch.setattr(n, "DB", tmp_path / "n.db")
    with patch("aura.core.notifications.shutil.which", return_value="/usr/bin/notify-send"):
        with patch("aura.core.notifications.subprocess.run"):
            assert n.notify(n.NotifLevel.P3, "a", "b") is True
