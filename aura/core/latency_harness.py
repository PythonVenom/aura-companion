"""T082 — Latency harness.

Наука:
- Nielsen 1993 — Latency budget: <1s = «поток», >10s = потеря внимания
- Google RAIL 2015 — Response <100ms, Animation <16ms
- Kleppmann 2017 — p99 важнее mean (хвосты критичны)
- Kaldi docs — RTF (Real-Time Factor)
- Google SRE Book — «Latency, не throughput»

Цель: измерять p50/p95/p99 для ключевых операций Aura.
Триггер T082: p99 < 1000ms для voice→response цикла.
"""
from __future__ import annotations

import json
import statistics
import time
from collections.abc import Callable
from pathlib import Path

RESULTS_DIR = Path.home() / ".local/share/aura/latency"
RESULTS_FILE = RESULTS_DIR / "results.jsonl"

# Nielsen 1993: порог «мгновенного» восприятия
TARGET_P99_MS = 1000
TARGET_P50_MS = 300


def _ensure() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def measure(operation: str, fn: Callable, *args, **kwargs) -> dict:
    """Замерить одну операцию. Возвращает запись."""
    _ensure()
    t0 = time.perf_counter()
    error = None
    try:
        fn(*args, **kwargs)
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)[:200]}"
    dt_ms = (time.perf_counter() - t0) * 1000.0
    entry = {
        "ts": time.time(),
        "operation": operation,
        "latency_ms": round(dt_ms, 2),
        "error": error,
    }
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def run_suite(suite: dict[str, Callable], iterations: int = 3) -> dict:
    """Прогнать набор операций по N итераций каждая.

    suite = {"op_name": callable, ...}
    """
    _ensure()
    results: dict[str, list[float]] = {}
    for op, fn in suite.items():
        times = []
        for _ in range(iterations):
            entry = measure(op, fn)
            if entry["error"] is None:
                times.append(entry["latency_ms"])
        results[op] = times
    return results


def percentile(values: list[float], p: float) -> float:
    """p в [0, 100]. Nearest-rank (Wikipedia, Kleppmann 2017).

    rank = ceil(p/100 * n), clamp to [1, n], idx = rank - 1.
    Для [1..100]: p50=50, p95=95, p99=99.
    """
    import math
    if not values:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    rank = max(1, min(n, math.ceil(p / 100.0 * n)))
    return sorted_v[rank - 1]


def summarize(results: dict[str, list[float]]) -> dict:
    """Сводка p50/p95/p99 для каждого operation."""
    summary = {}
    for op, times in results.items():
        if not times:
            summary[op] = {"count": 0, "p50": None, "p95": None, "p99": None}
            continue
        summary[op] = {
            "count": len(times),
            "mean_ms": round(statistics.mean(times), 2),
            "p50": round(percentile(times, 50), 2),
            "p95": round(percentile(times, 95), 2),
            "p99": round(percentile(times, 99), 2),
            "max": round(max(times), 2),
            "target_p99_ms": TARGET_P99_MS,
            "pass": percentile(times, 99) < TARGET_P99_MS,
        }
    return summary


def load_history() -> list[dict]:
    """История замеров из RESULTS_FILE."""
    if not RESULTS_FILE.exists():
        return []
    out = []
    for line in RESULTS_FILE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def latency_report() -> dict:
    """Публичный API: сводка по всем замерам."""
    history = load_history()
    by_op: dict[str, list[float]] = {}
    for h in history:
        if h.get("error"):
            continue
        by_op.setdefault(h["operation"], []).append(h["latency_ms"])
    return {
        "operations": len(by_op),
        "total_measurements": len(history),
        "summary": summarize(by_op),
        "target_p99_ms": TARGET_P99_MS,
    }


def reset() -> None:
    """Публичный API: очистить историю."""
    if RESULTS_FILE.exists():
        RESULTS_FILE.unlink()


__all__ = [
    "TARGET_P50_MS",
    "TARGET_P99_MS",
    "latency_report",
    "load_history",
    "measure",
    "percentile",
    "reset",
    "run_suite",
    "summarize",
]
