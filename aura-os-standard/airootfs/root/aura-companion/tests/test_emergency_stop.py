"""T-eng-6 — тесты emergency stop."""
import signal
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from aura.core import emergency_stop


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    """Изолировать STOP-файл + сбросить состояние."""
    monkeypatch.setattr(emergency_stop, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(emergency_stop, "STATE_DIR", tmp_path)
    emergency_stop.resume()
    yield
    emergency_stop.resume()


def test_initially_not_stopped():
    assert emergency_stop.is_stopped() is False


def test_stop_sets_flag():
    r = emergency_stop.stop("test")
    assert r["stopped"] is True
    assert emergency_stop.is_stopped() is True


def test_stop_idempotent():
    r1 = emergency_stop.stop("first")
    r2 = emergency_stop.stop("second")
    assert r1["stopped"] is True
    assert r2["already"] is True


def test_callbacks_called():
    calls = []
    emergency_stop.register(lambda: calls.append("cb1"))
    emergency_stop.register(lambda: calls.append("cb2"))
    emergency_stop.stop("test")
    assert "cb1" in calls
    assert "cb2" in calls


def test_callback_error_doesnt_break():
    def boom():
        raise RuntimeError("bad callback")

    emergency_stop.register(boom)
    r = emergency_stop.stop("test")
    assert r["stopped"] is True


def test_resume_clears_flag():
    emergency_stop.stop("test")
    assert emergency_stop.is_stopped() is True
    emergency_stop.resume()
    assert emergency_stop.is_stopped() is False


def test_stop_file_written(tmp_path):
    emergency_stop.stop("test reason")
    f = emergency_stop.STOP_FILE
    assert f.exists()
    content = f.read_text()
    assert "test reason" in content


def test_check_and_raise_when_stopped():
    emergency_stop.stop("x")
    with pytest.raises(SystemExit):
        emergency_stop.check_and_raise()


def test_check_and_raise_when_running():
    emergency_stop.check_and_raise()  # не должен raise


def test_status():
    s = emergency_stop.status()
    assert "stopped" in s
    assert "stop_file_exists" in s
    assert "callbacks_registered" in s


def test_stop_file_detected_via_is_stopped(tmp_path):
    emergency_stop.STOP_FILE.write_text("external")
    assert emergency_stop.is_stopped() is True
