"""Triple Modular Redundancy (P3 #157).

Три независимые реплики критичной задачи → голосование большинством.
Вдохновлено TMR (von Neumann, 1956) и space-grade вычислителями (RAD750).

Применение в AURA: критичные агенты (SOS, Fall, Meds) — защита от
single-event upsets и логических сбоев одной реплики.

Ключевые понятия:
- Реплика — независимый вызов task().
- Голосование — majority vote по ключу результата.
- Расхождение (disagreement) — реплики дали разные результаты.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class TMRError(Exception):
    """TMR: нет большинства или все реплики упали."""


_FAILED = object()


def _key(value: Any) -> Any:
    """Хешируемый ключ для голосования (для unhashable — repr)."""
    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


@dataclass
class TMRStats:
    total: int = 0
    agreed: int = 0
    disagreed: int = 0
    failed: int = 0

    def agreement_rate(self) -> float:
        return self.agreed / self.total if self.total else 0.0


class TripleModularRedundancy:
    """TMR: N реплик (нечётное, >=3) → majority vote.

    Пример:
        tmr = TripleModularRedundancy()
        result = tmr.run(lambda: sos_agent.check())
        print(tmr.stats.agreement_rate())
    """

    def __init__(self, replicas: int = 3):
        if replicas < 3 or replicas % 2 == 0:
            raise ValueError("replicas must be odd and >= 3")
        self.replicas = replicas
        self.stats = TMRStats()

    def run(self, task: Callable[[], Any]) -> Any:
        self.stats.total += 1
        results: list[Any] = []
        for _ in range(self.replicas):
            try:
                results.append(task())
            except Exception:
                results.append(_FAILED)

        counts: dict[Any, int] = {}
        for r in results:
            if r is _FAILED:
                continue
            k = _key(r)
            counts[k] = counts.get(k, 0) + 1

        if not counts:
            self.stats.failed += 1
            raise TMRError("All replicas failed")

        winner_key, winner_count = max(counts.items(), key=lambda kv: kv[1])
        if winner_count * 2 <= self.replicas:
            self.stats.failed += 1
            raise TMRError(f"No majority: counts={counts}")

        if len(counts) == 1:
            self.stats.agreed += 1
        else:
            self.stats.disagreed += 1

        for r in results:
            if r is not _FAILED and _key(r) == winner_key:
                return r
        raise TMRError("Unreachable: winner not found")
