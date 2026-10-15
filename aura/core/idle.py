"""Idle — фоновая активность AURA (когда капитан не занят).

Наука: Naptime (AURA #142), Cron-style tasks.
Idle = проверки, чистки, обучение.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable
from pathlib import Path

IDLE_LOG = Path.home() / ".cache" / "aura" / "idle.log"
LAST_ACTIVITY_FILE = Path.home() / ".cache" / "aura" / "last_activity"


@dataclass
class IdleTask:
    name: str
    interval_sec: int
    fn: Callable[[], object]


def _mark_activity() -> None:
    LAST_ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_ACTIVITY_FILE.write_text(str(time.time()))


def last_activity() -> float:
    if LAST_ACTIVITY_FILE.exists():
        try:
            return float(LAST_ACTIVITY_FILE.read_text())
        except Exception:
            pass
    return 0.0


def idle_seconds() -> float:
    return time.time() - last_activity()


def is_idle(threshold_sec: int = 300) -> bool:
    return idle_seconds() >= threshold_sec


def run_idle_tasks(tasks: list[IdleTask]) -> list[str]:
    """Прогнать idle-задачи. Возврат: список результатов."""
    results = []
    for t in tasks:
        try:
            r = t.fn()
            results.append(f"  ✅ {t.name}: {r}")
        except Exception as e:
            results.append(f"  ❌ {t.name}: {e}")
    return results


def _default_tasks() -> list[IdleTask]:
    """Дефолтные idle-задачи."""
    def _scrub_receipts():
        from aura.core.receipts import stats
        return stats()

    def _consolidate_memory():
        from aura.core.memory.semantic import get_semantic
        sm = get_semantic()
        return f"consolidate: {sm.consolidate()} дублей"

    return [
        IdleTask("receipts_verify", 3600, _scrub_receipts),
        IdleTask("memory_consolidate", 7200, _consolidate_memory),
    ]


def main() -> None:
    _mark_activity()
    print(f"Idle: {idle_seconds():.0f}с")
    print(f"Is idle: {is_idle()}")
    print("Задачи:")
    for line in run_idle_tasks(_default_tasks()):
        print(line)


if __name__ == "__main__":
    main()


__all__ = ["IdleTask", "idle_seconds", "is_idle", "main", "run_idle_tasks"]
