"""Тесты HandsFree — режим без активации (ADR-095)."""
from __future__ import annotations
import time
from pathlib import Path
import pytest
from aura.core import hands_free


@pytest.fixture(autouse=True)
def clean_flag(tmp_path, monkeypatch):
    f = tmp_path / "handsfree"
    monkeypatch.setattr(hands_free, "FLAG", f)
    yield
    if f.exists():
        f.unlink()


def test_initially_disabled():
    assert hands_free.is_active() is False


def test_enable():
    hands_free.enable(seconds=10)
    assert hands_free.is_active() is True


def test_disable():
    hands_free.enable(seconds=10)
    hands_free.disable()
    assert hands_free.is_active() is False


def test_expires():
    hands_free.enable(seconds=1)
    time.sleep(1.2)
    assert hands_free.is_active() is False


def test_remaining():
    hands_free.enable(seconds=60)
    r = hands_free.remaining()
    assert 55 < r <= 60


def test_corrupt_file():
    hands_free.FLAG.write_text("garbage")
    assert hands_free.is_active() is False
