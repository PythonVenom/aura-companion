"""#137 Rate limit для LLM — защита Ollama от DDoS.

Наука:
- RFC 6585 (2012) — 429 Too Many Requests
- Token Bucket (Turner 1986) — стандартный алгоритм rate limiting
- OWASP A04:2021 (Insecure Design)

Зачем:
  Aura может случайно заDDoS'ить Ollama — например, при цикле
  в react_loop или при активном proactive. Нужен token bucket.

Алгоритм:
  Ёмкость = N токенов. Каждый запрос = 1 токен.
  Токены восстанавливаются со скоростью R/сек.
  Если токенов нет → отказ (429).
"""
from __future__ import annotations

import threading
import time


class TokenBucket:
    """Потокобезопасный token bucket.

    По умолчанию: 100 запросов/мин (ёмкость 100, refill 100/60 ≈ 1.67/сек).
    """

    def __init__(self, capacity: int = 100, refill_per_sec: float | None = None) -> None:
        if capacity <= 0:
            raise ValueError("capacity > 0")
        self.capacity = capacity
        self.refill_rate = refill_per_sec if refill_per_sec is not None else capacity / 60.0
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        added = elapsed * self.refill_rate
        if added > 0:
            self._tokens = min(self.capacity, self._tokens + added)
            self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Попробовать взять токены. True — OK, False — отказ (429)."""
        if tokens <= 0:
            return True
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def available(self) -> int:
        """Сколько токенов доступно сейчас."""
        with self._lock:
            self._refill()
            return int(self._tokens)

    def reset(self) -> None:
        """Сбросить (для тестов)."""
        with self._lock:
            self._tokens = float(self.capacity)
            self._last_refill = time.monotonic()


# Глобальный bucket для LLM
_LLM_BUCKET: TokenBucket | None = None
_LLM_LOCK = threading.Lock()


def get_llm_bucket() -> TokenBucket:
    """Глобальный bucket для LLM (100 req/min)."""
    global _LLM_BUCKET
    with _LLM_LOCK:
        if _LLM_BUCKET is None:
            import os
            cap = int(os.environ.get("AURA_LLM_RATE_LIMIT", "100"))
            _LLM_BUCKET = TokenBucket(capacity=cap)
        return _LLM_BUCKET


def reset_llm_bucket() -> None:
    """Сбросить глобальный bucket (для тестов)."""
    global _LLM_BUCKET
    with _LLM_LOCK:
        _LLM_BUCKET = None


def check_llm() -> bool:
    """Проверить и списать токен LLM. False — 429."""
    return get_llm_bucket().consume(1)


__all__ = [
    "TokenBucket",
    "get_llm_bucket", "reset_llm_bucket", "check_llm",
]
