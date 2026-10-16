"""VoiceGate — VAD-гейт перед ASR.

ADR-075: Bug 72 — ASR ест фоновую речь (ТВ/музыка/чужой разговор).
webrtcvad (уже в venv, используется barge_in) режет не-речевые фреймы.

Модель:
- mode=0 (strict): пропускает только speech-фреймы
- mode=2 (balanced): окно 3 фрейма, ≥2 speech → пропуск

Фрейм = 10/20/30 ms (требование webrtcvad). При 16kHz: 160/320/480 samples.
"""
from __future__ import annotations

import webrtcvad

VALID_RATES = (8000, 16000, 32000, 48000)
VALID_FRAME_MS = (10, 20, 30)


class VoiceGate:
    def __init__(self, sample_rate=16000, aggressiveness=3, mode=2,
                 frame_ms=30, window_size=3, _vad=None):
        if sample_rate not in VALID_RATES:
            raise ValueError(f"sample_rate must be one of {VALID_RATES}")
        if frame_ms not in VALID_FRAME_MS:
            raise ValueError(f"frame_ms must be one of {VALID_FRAME_MS}")
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_samples = sample_rate * frame_ms // 1000
        self.frame_bytes = self.frame_samples * 2  # int16
        self.mode = mode
        self.window_size = window_size
        self.window: list = []
        self.vad = _vad if _vad is not None else webrtcvad.Vad(aggressiveness)

    def is_speech(self, pcm_bytes: bytes) -> bool:
        """True если фрейм (или окно) = речь."""
        if len(pcm_bytes) != self.frame_bytes:
            raise ValueError(
                f"frame must be {self.frame_bytes} bytes, got {len(pcm_bytes)}"
            )
        voice = self.vad.is_speech(pcm_bytes, self.sample_rate)
        self.window.append(voice)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        if self.mode == 0:
            return voice
        # mode >= 1: нужно ≥mode из window_size
        need = max(1, self.mode)
        return sum(self.window) >= need

    def reset(self) -> None:
        self.window = []


__all__ = ["VALID_FRAME_MS", "VALID_RATES", "VoiceGate"]
