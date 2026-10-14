"""Tests for deterministic timing (P3 #159)."""
from aura.core.deterministic import (
    Deadline,
    DeterministicScheduler,
    JitterStats,
    monotonic_ns,
)


def test_monotonic_ns_positive():
    assert monotonic_ns() > 0


def test_deadline_missed():
    d = Deadline(ts_ns=monotonic_ns() - 1_000_000)
    assert d.is_missed()


def test_deadline_not_missed():
    d = Deadline(ts_ns=monotonic_ns() + 1_000_000_000)
    assert not d.is_missed()


def test_jitter_stats_empty():
    s = JitterStats()
    assert s.mean() == 0.0
    assert s.max() == 0.0
    assert s.p95() == 0.0


def test_jitter_stats_values():
    s = JitterStats()
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        s.add(v)
    assert s.mean() == 3.0
    assert s.max() == 5.0
    assert s.min() == 1.0


def test_scheduler_rejects_zero_tick():
    import pytest
    with pytest.raises(ValueError):
        DeterministicScheduler(tick_ms=0)


def test_scheduler_runs_iterations():
    sched = DeterministicScheduler(tick_ms=10.0)
    count = {"n": 0}

    def task():
        count["n"] += 1

    sched.run(task, iterations=5)
    assert count["n"] == 5
    assert len(sched.stats.samples) == 5


def test_scheduler_stop():
    sched = DeterministicScheduler(tick_ms=1000.0)
    count = {"n": 0}

    def task():
        count["n"] += 1
        if count["n"] >= 2:
            sched.stop()

    sched.run(task, iterations=10)
    assert count["n"] == 2
