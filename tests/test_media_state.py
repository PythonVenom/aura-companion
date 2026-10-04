"""Bug 14: помним последний источник медиа."""

import time
from aura.agents import media_state as ms


def setup_function():
    ms.clear()


def test_set_get():
    ms.set_active("vk", chat="Аня")
    assert ms.get_active() == "vk"
    assert ms.get_active_chat() == "Аня"


def test_invalid_source_ignored():
    ms.set_active("spotify")  # не в VALID
    assert ms.get_active() is None


def test_ttl_expires():
    ms.STATE_PATH.write_text('{"source":"vk","chat":"","ts":0}', encoding="utf-8")
    assert ms.get_active() is None


def test_empty_returns_none():
    ms.clear()
    assert ms.get_active() is None


def test_overwrite():
    ms.set_active("local")
    ms.set_active("vk")
    assert ms.get_active() == "vk"
