"""Deterministic timing primitives (P3 #159 — TTEthernet-inspired).

Назначение: детерминированное планирование задач агентов с гарантиями
по дедлайнам. Вдохновлено Time-Triggered Ethernet (SAE AS6802).

Ключевые понятия:
- Монотонные часы (monotonic_ns) — независимы от системного времени.
- Deadline — абсолютный дедлайн в наносекундах.
- Jitter — отклонение фактического момента запуска от идеального.
- Fixed-tick scheduler — тактовая сетка с фиксированным шагом.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field


def monotonic_ns() -> int:
    """Монотонные часы в наносекундах. Не прыгают при NTP-синхронизации."""
    return time.monotonic_ns()


@dataclass
class Deadline:
    """Абсолютный дедлайн. Просрочка = missed."""
    ts_ns: int
    label: str = ""

    def is_missed(self, now_ns: int | None = None) -> bool:
        n = now_ns if now_ns is not None else monotonic_ns()
        return n > self.ts_ns

    def remaining_ms(self) -> float:
        return (self.ts_ns - monotonic_ns()) / 1e6


@dataclass
class JitterStats:
    """Статистика jitter в миллисекундах."""
    samples: list[float] = field(default_factory=list)

    def add(self, value_ms: float) -> None:
        self.samples.append(value_ms)

    def mean(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0.0

    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0

    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0

    def p95(self) -> float:
        if not self.samples:
            return 0.0
        s = sorted(self.samples)
        idx = int(0.95 * (len(s) - 1))
        return s[idx]


class DeterministicScheduler:
    """Fixed-tick scheduler с измерением jitter и подсчётом пропусков.

    Пример:
        sched = DeterministicScheduler(tick_ms=100.0)
        sched.run(my_task, iterations=10)
        print(sched.stats.mean(), sched.missed_deadlines)
    """

    def __init__(self, tick_ms: float = 100.0):
        if tick_ms <= 0:
            raise ValueError("tick_ms must be > 0")
        self.tick_ms = tick_ms
        self._tick_ns = int(tick_ms * 1e6)
        self._stats = JitterStats()
        self._missed = 0
        self._stopped = threading.Event()

    @property
    def stats(self) -> JitterStats:
        return self._stats

    @property
    def missed_deadlines(self) -> int:
        return self._missed

    def run(self, task: Callable[[], None], iterations: int = 10) -> None:
        """Выполнить task с фиксированным тактом.

        Jitter = отклонение факта запуска от идеальной тактовой сетки.
        """
        if iterations <= 0:
            return
        start = monotonic_ns()
        for i in range(iterations):
            if self._stopped.is_set():
                return
            target = start + i * self._tick_ns
            now = monotonic_ns()
            if now > target:
                self._missed += 1
            sleep_ns = target - now
            if sleep_ns > 0:
                time.sleep(sleep_ns / 1e9)
            jitter_ms = (monotonic_ns() - target) / 1e6
            self._stats.add(jitter_ms)
            task()

    def stop(self) -> None:
        self._stopped.set()
