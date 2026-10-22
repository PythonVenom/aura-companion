"""Тесты Focus."""
from __future__ import annotations
import time
import pytest
from aura.core import focus


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    f = tmp_path / "focus"
    monkeypatch.setattr(focus, "FLAG", f)
    yield
    if f.exists():
        f.unlink()


def test_initially_off():
    assert focus.is_active() is False


def test_enable():
    focus.enable(seconds=10)
    assert focus.is_active() is True


def test_disable():
    focus.enable(seconds=10)
    focus.disable()
    assert focus.is_active() is False


def test_expires():
    focus.enable(seconds=1)
    time.sleep(1.2)
    assert focus.is_active() is False


def test_remaining():
    focus.enable(seconds=60)
    r = focus.remaining()
    assert 55 < r <= 60
