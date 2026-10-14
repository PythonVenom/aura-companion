"""Tests for Triple Modular Redundancy (P3 #157)."""
import pytest

from aura.core.tmr import TripleModularRedundancy, TMRError


def test_rejects_even_replicas():
    with pytest.raises(ValueError):
        TripleModularRedundancy(replicas=2)


def test_rejects_too_few():
    with pytest.raises(ValueError):
        TripleModularRedundancy(replicas=1)


def test_all_agree():
    tmr = TripleModularRedundancy()
    result = tmr.run(lambda: 42)
    assert result == 42
    assert tmr.stats.agreed == 1
    assert tmr.stats.disagreed == 0
    assert tmr.stats.agreement_rate() == 1.0


def test_majority_wins():
    tmr = TripleModularRedundancy()
    seq = iter([1, 1, 2])

    def task():
        return next(seq)

    result = tmr.run(task)
    assert result == 1
    assert tmr.stats.disagreed == 1


def test_no_majority_raises():
    tmr = TripleModularRedundancy()
    seq = iter([1, 2, 3])

    def task():
        return next(seq)

    with pytest.raises(TMRError):
        tmr.run(task)
    assert tmr.stats.failed == 1


def test_all_failed_raises():
    tmr = TripleModularRedundancy()

    def task():
        raise RuntimeError("boom")

    with pytest.raises(TMRError):
        tmr.run(task)
    assert tmr.stats.failed == 1


def test_partial_failure_with_majority():
    tmr = TripleModularRedundancy()
    calls = {"n": 0}

    def task():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("replica 2 died")
        return "ok"

    result = tmr.run(task)
    assert result == "ok"
    assert tmr.stats.agreed == 1


def test_five_replicas():
    tmr = TripleModularRedundancy(replicas=5)
    seq = iter([1, 1, 1, 2, 3])

    def task():
        return next(seq)

    assert tmr.run(task) == 1
    assert tmr.stats.disagreed == 1


def test_unhashable_result():
    tmr = TripleModularRedundancy()
    result = tmr.run(lambda: {"status": "ok"})
    assert result == {"status": "ok"}
