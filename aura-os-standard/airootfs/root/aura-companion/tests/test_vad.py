"""Тесты для aura/core/vad.py — VoiceGate над webrtcvad."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aura.core.vad import VoiceGate


def _mock_vad(seq):
    """Mock vad.is_speech, отдаёт значения из seq по кругу."""
    m = MagicMock()
    it = iter(seq)
    def _is(pcm, sr):
        try:
            return next(it)
        except StopIteration:
            return False
    m.is_speech.side_effect = _is
    return m


def test_invalid_sample_rate():
    with pytest.raises(ValueError):
        VoiceGate(sample_rate=11025, _vad=_mock_vad([]))


def test_invalid_frame_size():
    gate = VoiceGate(sample_rate=16000, _vad=_mock_vad([]))
    with pytest.raises(ValueError):
        gate.is_speech(b"\x00" * 100)  # не 960


def test_single_frame_speech():
    gate = VoiceGate(sample_rate=16000, mode=0, _vad=_mock_vad([True]))
    assert gate.is_speech(b"\x00" * 960) is True


def test_single_frame_silence():
    gate = VoiceGate(sample_rate=16000, mode=0, _vad=_mock_vad([False]))
    assert gate.is_speech(b"\x00" * 960) is False


def test_window_2_of_3():
    gate = VoiceGate(sample_rate=16000, mode=2, _vad=_mock_vad([True, False, True]))
    gate.is_speech(b"\x00" * 960)  # T
    gate.is_speech(b"\x00" * 960)  # F
    assert gate.is_speech(b"\x00" * 960) is True  # 2/3


def test_window_1_of_3_blocks():
    gate = VoiceGate(sample_rate=16000, mode=2, _vad=_mock_vad([True, False, False]))
    gate.is_speech(b"\x00" * 960)  # T
    gate.is_speech(b"\x00" * 960)  # F
    assert gate.is_speech(b"\x00" * 960) is False  # 1/3


def test_reset_clears_window():
    gate = VoiceGate(sample_rate=16000, mode=2, _vad=_mock_vad([True, True, False]))
    gate.is_speech(b"\x00" * 960)
    gate.reset()
    assert gate.window == []
