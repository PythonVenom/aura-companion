"""
Тесты для AgentListener.listen() — streaming с endpoint detection.

Проверяет фикс дублей T-one (проблема 3 из ADR-002).
Мокаем recognizer — живой T-one не используется.
"""

from __future__ import annotations

import queue
import time

import numpy as np

from aura.agents.listener import AgentListener


class FakeStream:
    def accept_waveform(self, sample_rate, samples):
        pass
    def input_finished(self):
        pass


class FakeRecognizer:
    """
    Возвращает final_text всегда.
    is_endpoint → True после endpoint_after вызовов.
    """

    def __init__(self, final_text, endpoint_after=0):
        self.final_text = final_text
        self.endpoint_after = endpoint_after
        self.call_count = 0
        self.reset_count = 0

    def create_stream(self):
        return FakeStream()

    def is_ready(self, s):
        return False

    def decode_stream(self, s):
        pass

    def get_result(self, s):
        return self.final_text

    def is_endpoint(self, s):
        self.call_count += 1
        return self.call_count > self.endpoint_after

    def reset(self, s):
        self.reset_count += 1


def _make_listener(final_text, endpoint_after=0):
    lst = AgentListener.__new__(AgentListener)
    lst.ready = True
    lst.active = True
    lst.sample_rate = 8000
    lst.recognizer = FakeRecognizer(final_text, endpoint_after)
    lst.audio_queue = queue.Queue()
    lst.np = np
    lst.get_stream = lambda: "fake_stream"
    return lst


def test_listen_returns_text_on_endpoint():
    """Услышали фразу + endpoint → вернули сразу."""
    lst = _make_listener("аура который час", endpoint_after=3)

    t0 = time.time()
    result = lst.listen(timeout=5)
    elapsed = time.time() - t0

    assert result == "аура который час"
    assert elapsed < 3.0, "должны выйти по эндпоинту, не ждать 5 секунд"


def test_listen_resets_after_endpoint():
    """После endpoint — reset(s), чтобы не склеить фразы."""
    lst = _make_listener("аура который час", endpoint_after=2)
    lst.listen(timeout=5)

    assert lst.recognizer.reset_count == 1


def test_listen_timeout_returns_partial():
    """Таймаут без эндпоинта: отдаём то, что успели."""
    lst = _make_listener("аура погода", endpoint_after=9999)

    result = lst.listen(timeout=1)

    assert result == "аура погода"


def test_listen_not_ready_returns_none():
    lst = _make_listener("текст")
    lst.ready = False
    assert lst.listen(timeout=1) is None


def test_listen_not_active_returns_none():
    lst = _make_listener("текст")
    lst.active = False
    assert lst.listen(timeout=1) is None


def test_listen_short_text_ignored():
    """Текст длиной <= 2 символа игнорируется."""
    lst = _make_listener("аб", endpoint_after=1)
    assert lst.listen(timeout=1) is None
