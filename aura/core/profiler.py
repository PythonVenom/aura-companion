"""Profiler — auto-tune в runtime (ADR-153).

Наука:
- Beyer, B., et al. (2016). Site Reliability Engineering. O'Reilly.
- Burnham, B. (2019). Latency: The Hidden Cost. ACM Queue.
"""
from __future__ import annotations
import time
from collections import deque
from typing import Optional


class Profiler:
    THRESHOLDS = {"llm": 2000, "tts": 500, "asr": 800, "embed": 300, "dispatch": 50}

    def __init__(self, window: int = 20) -> None:
        self._samples: dict = {}
        self._window = window

    def record(self, op: str, ms: float) -> None:
        if op not in self._samples:
            self._samples[op] = deque(maxlen=self._window)
        self._samples[op].append((ms, time.time()))

    def p50(self, op: str) -> float:
        s = sorted(x[0] for x in self._samples.get(op, []))
        return s[len(s) // 2] if s else 0.0

    def p95(self, op: str) -> float:
        s = sorted(x[0] for x in self._samples.get(op, []))
        return s[int(len(s) * 0.95)] if s else 0.0

    def is_slow(self, op: str) -> bool:
        thresh = self.THRESHOLDS.get(op)
        return bool(thresh and self.p95(op) > thresh)

    def downgrade_needed(self) -> Optional[str]:
        for op, thresh in self.THRESHOLDS.items():
            if self.p95(op) > thresh * 1.5:
                return op
        return None

    def stats(self) -> dict:
        return {op: {"p50": round(self.p50(op), 1),
                     "p95": round(self.p95(op), 1),
                     "n": len(self._samples[op])}
                for op in self._samples}


_SINGLETON: Optional[Profiler] = None


def get_profiler() -> Profiler:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = Profiler()
    return _SINGLETON


class timed:
    def __init__(self, op: str) -> None:
        self.op = op
        self.t0 = 0.0

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *a):
        get_profiler().record(self.op, (time.time() - self.t0) * 1000)
