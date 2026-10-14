"""#131 Window control — тесты."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.core import window_control as WC


# === is_available ===

def test_is_available_true():
    """wmctrl установлен — True."""
    with patch("aura.core.window_control._has", return_value=True):
        assert WC.is_available() is True


def test_is_available_false():
    with patch("aura.core.window_control._has", return_value=False):
        assert WC.is_available() is False


# === _wmctrl helper ===

def test_wmctrl_missing():
    with patch("aura.core.window_control._has", return_value=False):
        assert WC._wmctrl("-l") is False


def test_wmctrl_ok():
    with patch("aura.core.window_control._has", return_value=True):
        with patch("aura.core.window_control.subprocess.run") as m:
            m.return_value = MagicMock(returncode=0)
            assert WC._wmctrl("-l") is True


def test_wmctrl_fail():
    with patch("aura.core.window_control._has", return_value=True):
        with patch("aura.core.window_control.subprocess.run") as m:
            m.return_value = MagicMock(returncode=1)
            assert WC._wmctrl("-r", "X", "-e", "0,0,0,-1,-1") is False


def test_wmctrl_exception():
    with patch("aura.core.window_control._has", return_value=True):
        with patch("aura.core.window_control.subprocess.run",
                   side_effect=OSError("boom")):
            assert WC._wmctrl("-l") is False


# === move_window ===

def test_move_window_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.move_window("Firefox", 100, 200) is True
        args = m.call_args[0]
        assert "-r" in args
        assert "Firefox" in args
        assert "0,100,200,-1,-1" in args


def test_move_window_empty_name():
    assert WC.move_window("", 100, 200) is False


# === resize_window ===

def test_resize_window_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.resize_window("Firefox", 800, 600) is True
        args = m.call_args[0]
        assert "0,-1,-1,800,600" in args


def test_resize_window_bad_size():
    assert WC.resize_window("Firefox", 0, 600) is False
    assert WC.resize_window("Firefox", 800, -1) is False


def test_resize_window_empty_name():
    assert WC.resize_window("", 800, 600) is False


# === move_resize ===

def test_move_resize_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.move_resize("X", 10, 20, 800, 600) is True
        args = m.call_args[0]
        assert "0,10,20,800,600" in args


def test_move_resize_empty_name():
    assert WC.move_resize("", 10, 20, 800, 600) is False


# === minimize / maximize / close ===

def test_minimize_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.minimize_window("X") is True
        assert "add,hidden" in m.call_args[0]


def test_maximize_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.maximize_window("X") is True
        assert "add,maximized_vert,maximized_horz" in m.call_args[0]


def test_close_ok():
    with patch("aura.core.window_control._wmctrl", return_value=True) as m:
        assert WC.close_window("X") is True
        assert "-c" in m.call_args[0]


def test_close_empty():
    assert WC.close_window("") is False


def test_minimize_empty():
    assert WC.minimize_window("") is False


# === center_window ===

def test_center_window():
    with patch("aura.core.window_control.move_resize", return_value=True) as m:
        WC.center_window("X", 1920, 1080, 800, 600)
        # 1920/2 - 800/2 = 560, 1080/2 - 600/2 = 240
        assert m.call_args[0] == ("X", 560, 240, 800, 600)


# === move_to_corner ===

def test_move_to_corner_tl():
    with patch("aura.core.window_control.move_resize", return_value=True) as m:
        WC.move_to_corner("X", "tl", 1920, 1080, 960, 540)
        assert m.call_args[0] == ("X", 0, 0, 960, 540)


def test_move_to_corner_br():
    with patch("aura.core.window_control.move_resize", return_value=True) as m:
        WC.move_to_corner("X", "br", 1920, 1080, 960, 540)
        assert m.call_args[0] == ("X", 960, 540, 960, 540)


def test_move_to_corner_invalid():
    assert WC.move_to_corner("X", "xx") is False


# === list_windows ===

def test_list_windows_no_wmctrl():
    with patch("aura.core.window_control._has", return_value=False):
        assert WC.list_windows() == []


def test_list_windows_parse():
    fake = (
        "0x01  0 hostname Firefox\n"
        "0x02  0 hostname Terminal\n"
    )
    with patch("aura.core.window_control._has", return_value=True):
        with patch("aura.core.window_control.subprocess.run") as m:
            m.return_value = MagicMock(returncode=0, stdout=fake)
            names = WC.list_windows()
    assert names == ["Firefox", "Terminal"]


def test_list_windows_exception():
    with patch("aura.core.window_control._has", return_value=True):
        with patch("aura.core.window_control.subprocess.run",
                   side_effect=OSError("boom")):
            assert WC.list_windows() == []


# === #139 Wayland ===

def test_is_wayland_false_on_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert WC.is_wayland() is False


def test_is_wayland_true(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert WC.is_wayland() is True


def test_mouse_click_left():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        assert WC.mouse_click(100, 200, "left") is True
    # 2 вызова: mousemove + click
    assert m.call_count == 2


def test_mouse_click_right():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        WC.mouse_click(50, 50, "right")
    calls = [c[0] for c in m.call_args_list]
    assert any("0xC1" in c for c in calls)


def test_mouse_click_no_ydotool():
    with patch.object(WC, "_has_ydotool", return_value=False):
        assert WC.mouse_click(0, 0) is False


def test_type_text_wayland():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        assert WC.type_text_wayland("привет") is True
    assert m.call_args[0] == ("type", "--", "привет")


def test_type_text_empty():
    assert WC.type_text_wayland("") is False


# === #139 Wayland ===

def test_is_wayland_false_on_x11(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert WC.is_wayland() is False


def test_is_wayland_true(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert WC.is_wayland() is True


def test_mouse_click_left():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        assert WC.mouse_click(100, 200, "left") is True
    # 2 вызова: mousemove + click
    assert m.call_count == 2


def test_mouse_click_right():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        WC.mouse_click(50, 50, "right")
    calls = [c[0] for c in m.call_args_list]
    assert any("0xC1" in c for c in calls)


def test_mouse_click_no_ydotool():
    with patch.object(WC, "_has_ydotool", return_value=False):
        assert WC.mouse_click(0, 0) is False


def test_type_text_wayland():
    with patch.object(WC, "_ydotool", return_value=True) as m:
        assert WC.type_text_wayland("привет") is True
    assert m.call_args[0] == ("type", "--", "привет")


def test_type_text_empty():
    assert WC.type_text_wayland("") is False
