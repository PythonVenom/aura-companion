"""#100 CDP Bridge — тесты."""
from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from aura.core import cdp_bridge as CDP


def _fake_response(payload, status=200):
    m = MagicMock()
    m.status = status
    m.read = MagicMock(return_value=json.dumps(payload).encode())
    m.__enter__ = MagicMock(return_value=m)
    m.__exit__ = MagicMock(return_value=False)
    return m


# === is_available ===

def test_is_available_true():
    payload = {"webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/abc"}
    with patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        assert CDP.is_available() is True


def test_is_available_false_no_ws():
    with patch("urllib.request.urlopen", return_value=_fake_response({"Browser": "Chrome"})):
        assert CDP.is_available() is False


def test_is_available_false_offline():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
        assert CDP.is_available() is False


# === discover ===

def test_discover_returns_ws_url():
    payload = {"webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/x"}
    with patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        assert CDP.discover() == "ws://127.0.0.1:9222/devtools/browser/x"


def test_discover_offline():
    with patch("urllib.request.urlopen", side_effect=OSError("nope")):
        assert CDP.discover() is None


# === list_tabs ===

def test_list_tabs_filters_pages():
    payload = [
        {"id": "1", "type": "page", "title": "A", "url": "https://a",
         "webSocketDebuggerUrl": "ws://x"},
        {"id": "2", "type": "service_worker", "title": "SW", "url": "sw"},
        {"id": "3", "type": "page", "title": "B", "url": "https://b"},
    ]
    with patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        tabs = CDP.list_tabs()
    assert len(tabs) == 2
    assert {t["id"] for t in tabs} == {"1", "3"}


def test_list_tabs_offline():
    with patch("urllib.request.urlopen", side_effect=OSError("nope")):
        assert CDP.list_tabs() == []


def test_list_tabs_not_list():
    with patch("urllib.request.urlopen", return_value=_fake_response({"a": 1})):
        assert CDP.list_tabs() == []


# === close_tab ===

def test_close_tab_ok():
    with patch("urllib.request.urlopen", return_value=_fake_response("OK", status=200)):
        assert CDP.close_tab("tab-1") is True


def test_close_tab_empty_id():
    assert CDP.close_tab("") is False


def test_close_tab_offline():
    with patch("urllib.request.urlopen", side_effect=OSError("nope")):
        assert CDP.close_tab("tab-1") is False


# === new_tab ===

def test_new_tab_via_put():
    payload = {"id": "new1", "title": "New", "url": "https://x",
               "webSocketDebuggerUrl": "ws://x"}
    with patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        tab = CDP.new_tab("https://x")
    assert tab is not None
    assert tab["id"] == "new1"


def test_new_tab_fallback_get():
    payload = {"id": "new2", "title": "New", "url": "https://y"}
    calls = {"n": 0}

    def side(*args, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("PUT not supported")
        return _fake_response(payload)

    with patch("urllib.request.urlopen", side_effect=side):
        tab = CDP.new_tab("https://y")
    assert tab is not None
    assert tab["id"] == "new2"


def test_new_tab_offline():
    with patch("urllib.request.urlopen", side_effect=OSError("nope")):
        assert CDP.new_tab("https://x") is None


# === navigate ===

def test_navigate_new_tab():
    payload = {"id": "n1", "title": "Nav", "url": "https://z"}
    with patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        assert CDP.navigate("https://z") is True


def test_navigate_with_tab_id_closes_first():
    payload = {"id": "n2", "title": "Nav", "url": "https://z"}
    calls = []

    def side(req, **kw):
        url = req if isinstance(req, str) else req.full_url
        calls.append(url)
        return _fake_response(payload)

    with patch("urllib.request.urlopen", side_effect=side):
        CDP.navigate("https://z", tab_id="old-tab")
    assert any("close/old-tab" in c for c in calls)


# === get_active_tab ===

def test_get_active_tab_none():
    with patch.object(CDP, "list_tabs", return_value=[]):
        assert CDP.get_active_tab() is None


def test_get_active_tab_first():
    tabs = [{"id": "1", "title": "A"}, {"id": "2", "title": "B"}]
    with patch.object(CDP, "list_tabs", return_value=tabs):
        assert CDP.get_active_tab()["id"] == "1"


# === Константы ===

def test_default_port():
    assert CDP.DEFAULT_PORT == 9222


def test_default_host():
    assert CDP.DEFAULT_HOST == "127.0.0.1"
