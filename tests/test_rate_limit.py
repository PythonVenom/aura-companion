"""#137 Rate limit — тесты."""
from __future__ import annotations

import threading
import time

import pytest

from aura.core.rate_limit import (
    TokenBucket, check_llm, get_llm_bucket, reset_llm_bucket,
)


@pytest.fixture(autouse=True)
def reset():
    reset_llm_bucket()
    yield
    reset_llm_bucket()


# === TokenBucket ===

def test_capacity_validation():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0)
    with pytest.raises(ValueError):
        TokenBucket(capacity=-1)


def test_consume_full_bucket():
    b = TokenBucket(capacity=5, refill_per_sec=0)
    for _ in range(5):
        assert b.consume() is True
    assert b.consume() is False


def test_available_decreases():
    b = TokenBucket(capacity=10, refill_per_sec=0)
    assert b.available() == 10
    b.consume(3)
    assert b.available() == 7


def test_consume_multiple_tokens():
    b = TokenBucket(capacity=10, refill_per_sec=0)
    assert b.consume(5) is True
    assert b.available() == 5
    assert b.consume(6) is False
    assert b.available() == 5


def test_consume_zero_or_negative():
    b = TokenBucket(capacity=5, refill_per_sec=0)
    assert b.consume(0) is True
    assert b.consume(-1) is True
    assert b.available() == 5


def test_refill_over_time():
    b = TokenBucket(capacity=10, refill_per_sec=100)
    b.consume(10)
    assert b.available() == 0
    time.sleep(0.05)  # 5 токенов
    assert b.available() >= 3


def test_refill_capped_at_capacity():
    b = TokenBucket(capacity=10, refill_per_sec=1000)
    b.consume(10)
    time.sleep(0.05)
    assert b.available() <= 10


def test_reset():
    b = TokenBucket(capacity=5, refill_per_sec=0)
    b.consume(5)
    assert b.available() == 0
    b.reset()
    assert b.available() == 5


# === Thread safety ===

def test_thread_safety_no_overconsume():
    """100 потоков × 1 токен при capacity 50 → 50 успешных."""
    b = TokenBucket(capacity=50, refill_per_sec=0)
    success = []
    lock = threading.Lock()

    def worker():
        ok = b.consume()
        with lock:
            success.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(success) == 50


# === Global LLM bucket ===

def test_get_llm_bucket_singleton():
    b1 = get_llm_bucket()
    b2 = get_llm_bucket()
    assert b1 is b2


def test_reset_creates_new():
    b1 = get_llm_bucket()
    reset_llm_bucket()
    b2 = get_llm_bucket()
    assert b1 is not b2


def test_check_llm_ok():
    assert check_llm() is True


def test_check_llm_exhausted():
    """100 запросов → 101-й False."""
    reset_llm_bucket()
    for _ in range(100):
        check_llm()
    assert check_llm() is False


def test_env_override_capacity(monkeypatch):
    monkeypatch.setenv("AURA_LLM_RATE_LIMIT", "5")
    reset_llm_bucket()
    b = get_llm_bucket()
    assert b.capacity == 5
