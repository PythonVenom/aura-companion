"""#101 UI Automation — тесты универсального API."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.core import ui_automation as UI


@pytest.fixture(autouse=True)
def reset():
    UI.reset_backend()
    yield
    UI.reset_backend()


# === Auto-detect backend ===

def test_linux_backend():
    with patch("platform.system", return_value="Linux"):
        b = UI._detect_backend()
        assert isinstance(b, UI.LinuxAtspiBackend)


def test_windows_backend():
    with patch("platform.system", return_value="Windows"):
        b = UI._detect_backend()
        assert isinstance(b, UI.WindowsUiaBackend)


def test_macos_backend():
    with patch("platform.system", return_value="Darwin"):
        b = UI._detect_backend()
        assert isinstance(b, UI.MacosAxapiBackend)


def test_unknown_platform():
    with patch("platform.system", return_value="FreeBSD"):
        b = UI._detect_backend()
        assert b is None


# === backend_name / is_ready ===

def test_backend_name_atspi():
    with patch("platform.system", return_value="Linux"):
        assert UI.backend_name() == "atspi"


def test_is_ready_false_without_gi():
    """Без gi → is_ready False (не краш)."""
    with patch("platform.system", return_value="Linux"):
        UI.reset_backend()
        # gi нет в venv → False
        assert UI.is_ready() is False


def test_is_ready_windows_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.is_ready() is False


# === Публичный API без backend ===

def test_list_windows_empty_on_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.list_windows() == []


def test_read_window_tree_empty_on_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.read_window_tree() == []


def test_click_false_on_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.click_element("button") is False


def test_type_false_on_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.type_text("text") is False


def test_active_window_empty_on_stub():
    with patch("platform.system", return_value="Windows"):
        UI.reset_backend()
        assert UI.get_active_window() == ""


# === Backend mocked ===

def test_click_with_mock_backend():
    mock = MagicMock()
    mock.click_element.return_value = True
    with patch.object(UI, "_BACKEND", mock):
        with patch.object(UI, "_BACKEND_CHECKED", True):
            assert UI.click_element("test") is True
            mock.click_element.assert_called_once_with("test")


def test_list_windows_with_mock():
    mock = MagicMock()
    mock.list_windows.return_value = ["Firefox", "Terminal"]
    with patch.object(UI, "_BACKEND", mock):
        with patch.object(UI, "_BACKEND_CHECKED", True):
            assert UI.list_windows() == ["Firefox", "Terminal"]


def test_read_window_tree_with_mock():
    mock = MagicMock()
    tree = [{"role": "frame", "name": "Main", "children": []}]
    mock.read_window_tree.return_value = tree
    with patch.object(UI, "_BACKEND", mock):
        with patch.object(UI, "_BACKEND_CHECKED", True):
            assert UI.read_window_tree(depth=3) == tree
            mock.read_window_tree.assert_called_once_with(3)


# === Protocol ===

def test_backend_is_protocol():
    """BaseBackend — runtime-checkable Protocol."""
    b = UI.WindowsUiaBackend()
    assert isinstance(b, UI.BaseBackend)


def test_reset_backend():
    UI.reset_backend()
    assert UI._BACKEND_CHECKED is False
    assert UI._BACKEND is None
