"""Тесты для aura/heartbeat.py."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from aura.heartbeat import Heartbeat, MAX_STALE_SEC


def test_beat_updates_timestamp():
    hb = Heartbeat()
    old = hb._last
    time.sleep(0.01)
    hb.beat()
    assert hb._last > old


def test_start_returns_true():
    hb = Heartbeat()
    assert hb.start() is True
    hb.stop()


def test_start_idempotent():
    hb = Heartbeat()
    hb.start()
    assert hb.start() is True
    hb.stop()


def test_stop_sets_running_false():
    hb = Heartbeat()
    hb.start()
    hb.stop()
    assert hb._running is False


def test_stale_triggers_callback():
    """Если цикл не бился — callback вызван."""
    called = {"n": 0}

    def on_stale():
        called["n"] += 1

    hb = Heartbeat(on_stale=on_stale)
    hb._last = time.time() - MAX_STALE_SEC - 1
    hb._running = True

    # Один прогон loop с малым интервалом
    with patch("aura.heartbeat.CHECK_INTERVAL_SEC", 0.01):
        hb._loop()

    assert called["n"] == 1


def test_fresh_does_not_trigger():
    """Если цикл живой — callback не вызван."""
    called = {"n": 0}

    def on_stale():
        called["n"] += 1

    hb = Heartbeat(on_stale=on_stale)
    hb.beat()
    hb._running = True

    # Останавливаемся после одного цикла
    def stopper():
        time.sleep(0.05)
        hb.stop()

    import threading
    threading.Thread(target=stopper, daemon=True).start()

    with patch("aura.heartbeat.CHECK_INTERVAL_SEC", 0.01):
        hb._loop()

    assert called["n"] == 0


def test_callback_exception_does_not_crash():
    def bad():
        raise RuntimeError("boom")

    hb = Heartbeat(on_stale=bad)
    hb._last = time.time() - MAX_STALE_SEC - 1
    hb._running = True

    with patch("aura.heartbeat.CHECK_INTERVAL_SEC", 0.01):
        hb._loop()  # не должно упасть
