"""Bug 29 regression — count×rows для Plasma 6."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents import desktop_control as D


# === _desktop_count ===

def test_desktop_count_4_desktops():
    """Plasma 6: count=1, rows=4 → всего 4."""
    def fake_run(cmd, **kw):
        r = MagicMock()
        if cmd[-1].endswith(".count"):
            r.returncode = 0
            r.stdout = "1"
        elif cmd[-1].endswith(".rows"):
            r.returncode = 0
            r.stdout = "4"
        else:
            r.returncode = 1
            r.stdout = ""
        return r
    with patch("aura.agents.desktop_control._has", return_value=True):
        with patch("aura.agents.desktop_control.subprocess.run", side_effect=fake_run):
            assert D._desktop_count() == 4


def test_desktop_count_1x1():
    """Один стол → 1×1=1."""
    def fake_run(cmd, **kw):
        r = MagicMock()
        r.returncode = 0
        r.stdout = "1"
        return r
    with patch("aura.agents.desktop_control._has", return_value=True):
        with patch("aura.agents.desktop_control.subprocess.run", side_effect=fake_run):
            assert D._desktop_count() == 1


def test_desktop_count_2x2():
    """2×2 сетка = 4 стола."""
    def fake_run(cmd, **kw):
        r = MagicMock()
        r.returncode = 0
        r.stdout = "2"
        return r
    with patch("aura.agents.desktop_control._has", return_value=True):
        with patch("aura.agents.desktop_control.subprocess.run", side_effect=fake_run):
            assert D._desktop_count() == 4


def test_desktop_count_no_qdbus():
    with patch("aura.agents.desktop_control._has", return_value=False):
        assert D._desktop_count() == 0


def test_desktop_count_bad_output():
    """Не-числовой вывод → 0."""
    def fake_run(cmd, **kw):
        r = MagicMock()
        r.returncode = 0
        r.stdout = "abc"
        return r
    with patch("aura.agents.desktop_control._has", return_value=True):
        with patch("aura.agents.desktop_control.subprocess.run", side_effect=fake_run):
            assert D._desktop_count() == 0


# === next_desktop ===

def test_next_desktop_single_returns_false():
    """Bug 29: 1 стол → next_desktop False."""
    with patch.object(D, "_desktop_count", return_value=1):
        assert D.next_desktop() is False


def test_next_desktop_multi_calls_qdbus():
    """4 стола → вызывается qdbus nextDesktop."""
    calls = []
    def fake_run(cmd, **kw):
        calls.append(cmd)
        r = MagicMock()
        r.returncode = 0
        r.stdout = ""
        return r
    with patch.object(D, "_desktop_count", return_value=4):
        with patch("aura.agents.desktop_control._has", return_value=True):
            with patch("aura.agents.desktop_control.subprocess.run", side_effect=fake_run):
                assert D.next_desktop() is True
    # Проверяем, что был вызов nextDesktop
    assert any("nextDesktop" in " ".join(c) for c in calls)


def test_prev_desktop_single_returns_false():
    with patch.object(D, "_desktop_count", return_value=1):
        assert D.prev_desktop() is False
