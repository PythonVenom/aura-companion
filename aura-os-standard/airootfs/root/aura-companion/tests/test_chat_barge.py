"""Bug 33a — тесты интеграции barge_in в chat.py."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

from aura.chat import _stream_and_speak


# === _stream_and_speak: barge_in lifecycle ===

@pytest.mark.asyncio
async def test_stream_enables_barge_in():
    """При старте стриминга — set_aura_speaking(True)."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Тест."]))
    orch = MagicMock(brain=brain)
    barge_in = MagicMock()

    await _stream_and_speak(orch, "test", None, barge_in)

    barge_in.set_aura_speaking.assert_any_call(True)


@pytest.mark.asyncio
async def test_stream_disables_barge_in_finally():
    """После стриминга — set_aura_speaking(False)."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Тест."]))
    orch = MagicMock(brain=brain)
    barge_in = MagicMock()

    await _stream_and_speak(orch, "test", None, barge_in)

    barge_in.set_aura_speaking.assert_any_call(False)


@pytest.mark.asyncio
async def test_stream_clears_buffer_start():
    """Буфер barge_in очищается в начале."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Тест."]))
    orch = MagicMock(brain=brain)
    barge_in = MagicMock()

    await _stream_and_speak(orch, "test", None, barge_in)

    barge_in.clear_buffer.assert_called()


@pytest.mark.asyncio
async def test_stream_disables_on_exception():
    """Даже при ошибке — set_aura_speaking(False) в finally."""
    brain = MagicMock()
    brain.stream = MagicMock(side_effect=RuntimeError("boom"))
    orch = MagicMock(brain=brain)
    barge_in = MagicMock()

    await _stream_and_speak(orch, "test", None, barge_in)

    barge_in.set_aura_speaking.assert_any_call(False)


@pytest.mark.asyncio
async def test_stream_no_barge_in_works():
    """Без barge_in — работает (fallback)."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["A. ", "B."]))
    orch = MagicMock(brain=brain)

    text, spoke = await _stream_and_speak(orch, "test", None, None)
    assert text == "A. B."


@pytest.mark.asyncio
async def test_stream_barge_in_failure_tolerated():
    """Если barge_in падает — не крашим streaming."""
    brain = MagicMock()
    brain.stream = MagicMock(return_value=iter(["Тест."]))
    orch = MagicMock(brain=brain)
    barge_in = MagicMock()
    barge_in.set_aura_speaking.side_effect = RuntimeError("bad barge")

    # Не должно упасть
    text, spoke = await _stream_and_speak(orch, "test", None, barge_in)
    assert "Тест" in text


# === stop_command интеграция ===

def test_recognize_stop_imported():
    """stop_command доступен из chat."""
    from aura.chat import _stream_and_speak  # noqa
    from aura.core.stop_command import recognize_stop  # noqa
    assert callable(recognize_stop)


def test_barge_in_imported():
    """AgentBargeIn доступен."""
    from aura.agents.barge_in import AgentBargeIn
    assert hasattr(AgentBargeIn, "get_recent_pcm")
    assert hasattr(AgentBargeIn, "clear_buffer")
