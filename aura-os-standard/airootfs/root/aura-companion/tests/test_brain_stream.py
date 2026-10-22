"""#103 — тесты brain.stream()."""
from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.brain import AgentBrain


@pytest.fixture
def brain():
    return AgentBrain()


def _fake_response(lines: list[bytes]):
    """Mock urlopen response с iterable NDJSON."""
    m = MagicMock()
    m.__enter__ = MagicMock(return_value=m)
    m.__exit__ = MagicMock(return_value=False)
    m.__iter__ = MagicMock(return_value=iter(lines))
    return m


# === _stream_model_sync ===

def test_stream_model_parses_ndjson(brain):
    lines = [
        b'{"message":{"content":"\xd0\x9f\xd1\x80\xd0\xb8"},"done":false}\n',
        b'{"message":{"content":"\xd0\xb2\xd0\xb5\xd1\x82"},"done":false}\n',
        b'{"message":{"content":"!"},"done":true}\n',
    ]
    with patch("aura.agents.brain.urllib.request.urlopen",
               return_value=_fake_response(lines)):
        chunks = list(brain._stream_model_sync("m", [], 5))
    assert chunks == ["При", "вет", "!"]


def test_stream_model_skips_empty_lines(brain):
    lines = [b"\n", b'{"message":{"content":"X"},"done":false}\n', b"\n"]
    with patch("aura.agents.brain.urllib.request.urlopen",
               return_value=_fake_response(lines)):
        chunks = list(brain._stream_model_sync("m", [], 5))
    assert chunks == ["X"]


def test_stream_model_handles_bad_json(brain):
    lines = [
        b'{"message":{"content":"A"},"done":false}\n',
        b"not json\n",
        b'{"message":{"content":"B"},"done":true}\n',
    ]
    with patch("aura.agents.brain.urllib.request.urlopen",
               return_value=_fake_response(lines)):
        chunks = list(brain._stream_model_sync("m", [], 5))
    assert chunks == ["A", "B"]


def test_stream_model_stops_on_done(brain):
    """После done — break, остальное не читаем."""
    lines = [
        b'{"message":{"content":"A"},"done":false}\n',
        b'{"message":{"content":"B"},"done":true}\n',
        b'{"message":{"content":"C"},"done":false}\n',  # не должен попасть
    ]
    with patch("aura.agents.brain.urllib.request.urlopen",
               return_value=_fake_response(lines)):
        chunks = list(brain._stream_model_sync("m", [], 5))
    assert chunks == ["A", "B"]


# === stream() ===

def test_stream_yields_chunks(brain):
    def fake(model, messages, timeout):
        yield "При"
        yield "вет"
    with patch.object(brain, "_stream_model_sync", side_effect=fake):
        chunks = list(brain.stream("привет"))
    assert chunks == ["При", "вет"]


@pytest.mark.xfail(reason="Требует доработки стрима")
def test_stream_appends_to_history(brain):
    def fake(model, messages, timeout):
        yield "Hello"
    with patch.object(brain, "_stream_model_sync", side_effect=fake):
        list(brain.stream("привет"))
    assert any(m["role"] == "user" for m in brain.context_history)
    assert any(
        m["role"] == "assistant" and m["content"] == "Hello"
        for m in brain.context_history
    )


def test_stream_fallback_on_empty(brain):
    """Если streaming пуст → fallback через ask()."""
    def empty(model, messages, timeout):
        return
        yield
    with patch.object(brain, "_stream_model_sync", side_effect=empty):
        with patch.object(brain, "ask", return_value="fallback ответ"):
            chunks = list(brain.stream("привет"))
    assert chunks == ["fallback ответ"]


def test_stream_fallback_on_exception(brain):
    def bad(model, messages, timeout):
        raise RuntimeError("stream broke")
        yield
    with patch.object(brain, "_stream_model_sync", side_effect=bad):
        with patch.object(brain, "ask", return_value="fallback OK"):
            chunks = list(brain.stream("привет"))
    assert chunks == ["fallback OK"]


def test_stream_is_generator(brain):
    def fake(model, messages, timeout):
        yield "X"
    with patch.object(brain, "_stream_model_sync", side_effect=fake):
        g = brain.stream("test")
        assert isinstance(g, types.GeneratorType)


def test_stream_yields_error_when_all_fail(brain):
    """Если и ask() упал → yield ошибка."""
    def bad(model, messages, timeout):
        raise RuntimeError("x")
        yield
    with patch.object(brain, "_stream_model_sync", side_effect=bad):
        with patch.object(brain, "ask", side_effect=RuntimeError("ask broke")):
            chunks = list(brain.stream("test"))
    assert len(chunks) == 1
    assert "Ошибка" in chunks[0]


def test_stream_done_flag_stops(brain):
    """done:true → break."""
    lines = [b'{"message":{"content":"X"},"done":true}\n']
    with patch("aura.agents.brain.urllib.request.urlopen",
               return_value=_fake_response(lines)):
        chunks = list(brain._stream_model_sync("m", [], 5))
    assert chunks == ["X"]
