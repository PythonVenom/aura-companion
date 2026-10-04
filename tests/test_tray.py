"""Тесты для aura/core/tray.py — SNI трей через pystray (ADR-081)."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from aura.core.tray import TrayIcon, MENU_ITEMS, state_to_color


def test_menu_items_nonempty():
    assert len(MENU_ITEMS) >= 3
    names = [m[0] for m in MENU_ITEMS]
    assert "status" in names
    assert "pause" in names
    assert "quit" in names


def test_state_to_color_known():
    assert state_to_color("idle").startswith("#")
    assert state_to_color("listening").startswith("#")
    assert state_to_color("error").startswith("#")


def test_state_to_color_unknown():
    assert state_to_color("garbage").startswith("#")


def test_tray_init_no_icon():
    t = TrayIcon(api_url="http://127.0.0.1:8765", _icon=None)
    assert t.api_url == "http://127.0.0.1:8765"
    assert t.enabled is False


def test_tray_build_menu_count():
    t = TrayIcon(api_url="http://127.0.0.1:8765", _icon=None)
    menu = t.build_menu()
    # AURA_TRAY_TEST_V1 — separators не попадают в build_menu
    non_sep = [m for m in MENU_ITEMS if m[1] is not None]
    assert len(menu) >= len(non_sep)


def test_tray_get_status_url():
    t = TrayIcon(api_url="http://127.0.0.1:8765", _icon=None)
    assert t.status_url() == "http://127.0.0.1:8765/status"
    assert t.chat_url() == "http://127.0.0.1:8765/chat"


def test_tray_pause_url_via_ctl():
    t = TrayIcon(api_url="http://127.0.0.1:8765", _icon=None)
    # pause идёт через aura_ctl, не HTTP
    assert "aura_ctl" in t.pause_command()
