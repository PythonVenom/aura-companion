"""WakeWordDetector — openWakeWord обёртка (ADR-083)."""
from __future__ import annotations

import numpy as np

WAKE_PHRASES = ["aura"]
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1280
MIN_BYTES = CHUNK_SAMPLES * 2


class WakeWordDetector:
    def __init__(self, threshold: float = 0.5, model_names=None, _model=None):
        if not 0.0 < threshold < 1.0:
            raise ValueError("threshold must be in (0, 1)")
        self.threshold = threshold
        self.model_names = model_names or ["aura"]
        self._model = _model
        self._last_score = 0.0
        self.enabled = _model is not None

    def detect(self, pcm_bytes: bytes) -> bool:
        if not self.enabled:
            return False
        if not pcm_bytes or len(pcm_bytes) < MIN_BYTES:
            return False
        try:
            pcm = np.frombuffer(pcm_bytes, dtype=np.int16)
            result = self._model.predict(pcm)
        except Exception:
            return False
        if not isinstance(result, dict):
            return False
        score = max(result.values()) if result else 0.0
        self._last_score = float(score)
        return self._last_score >= self.threshold

    def reset(self) -> None:
        self._last_score = 0.0

    @classmethod
    def from_openwakeword(cls, threshold: float = 0.5, model_names=None):
        try:
            from openwakeword.model import Model
            m = Model(wakeword_models=model_names or ["aura"])
            return cls(threshold=threshold, model_names=model_names, _model=m)
        except Exception:
            return cls(threshold=threshold, model_names=model_names, _model=None)


__all__ = ["CHUNK_SAMPLES", "SAMPLE_RATE", "WAKE_PHRASES", "WakeWordDetector"]
