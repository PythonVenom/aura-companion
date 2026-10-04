"""Тесты RouteTree (v3.0: 7 листьев)."""
from __future__ import annotations
from aura.core.route_tree import build_route_tree


def _route(text):
    return build_route_tree().handle(text, {})


def test_control_pause():
    assert _route("пауза")["route"] == "control"


def test_control_panic():
    assert _route("panic")["route"] == "control"


def test_control_resume():
    r = _route("продолжи")
    assert r["route"] == "control" and r["action"] == "resume"


def test_power_lock():
    r = _route("заблокируй экран")
    assert r["route"] == "power" and r["action"] == "lock"


def test_music_play():
    r = _route("включи кино")
    assert r["route"] == "music" and r["action"] == "play"


def test_music_next():
    r = _route("следующий трек")
    assert r["route"] == "music" and r["action"] == "next"


def test_time_now():
    r = _route("который час")
    assert r["route"] == "time" and r["action"] == "now"


def test_time_date():
    r = _route("какое сегодня число")
    assert r["route"] == "time" and r["action"] == "date"


def test_app_launch():
    r = _route("открой firefox")
    assert r["route"] == "app" and r["action"] == "launch"
    assert "firefox" in r["args"]["name"].lower()


def test_browser_open():
    r = _route("открой https://ya.ru")
    assert r["route"] == "browser" and r["action"] == "open"
    assert r["args"]["url"].startswith("https://")


def test_fallback_ask():
    r = _route("расскажи анекдот")
    assert r["route"] == "ask"


def test_unknown_ask():
    assert _route("бла бла")["route"] == "ask"
