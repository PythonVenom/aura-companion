"""EgressBroker — фильтр исходящих к внешним AI (ADR-091).

Задачи:
1. Whitelist endpoint (allowed_endpoints)
2. Фильтр payload (только разрешённые поля)
3. Бюджет per-day
4. Логирование в Logbook

Pareto: 80% защиты = whitelist + фильтр payload.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


DEFAULT_ALLOWED_FIELDS = frozenset({
    "prompt", "text", "query", "messages", "model", "max_tokens",
    "temperature", "stream",
})

DEFAULT_FORBIDDEN_PREFIXES = (
    "user_", "device_", "system_", "personal_", "private_",
)


@dataclass
class BrokerPolicy:
    allowed_endpoints: list = field(default_factory=list)
    allowed_fields: frozenset = DEFAULT_ALLOWED_FIELDS
    forbidden_prefixes: tuple = DEFAULT_FORBIDDEN_PREFIXES
    daily_budget: float = 100.0  # ₽ или $

    def allow(self, host: str) -> bool:
        return host in self.allowed_endpoints


class EgressBroker:
    def __init__(self, policy: Optional[BrokerPolicy] = None):
        self.policy = policy or BrokerPolicy()
        self._spent_today = 0.0
        self._day_start = time.time()

    def _reset_if_new_day(self) -> None:
        if time.time() - self._day_start > 86400:
            self._spent_today = 0.0
            self._day_start = time.time()

    def validate_endpoint(self, url: str) -> None:
        host = urlparse(url).hostname or ""
        if not self.policy.allow(host):
            raise PermissionError(f"endpoint not allowed: {host}")

    def filter_payload(self, payload: dict) -> dict:
        out = {}
        for k, v in payload.items():
            if k in self.policy.allowed_fields:
                out[k] = v
                continue
            if any(k.startswith(p) for p in self.policy.forbidden_prefixes):
                continue
            # Неизвестные — пропускаем (whitelist выше)
        return out

    def check_budget(self, cost: float = 0.0) -> bool:
        self._reset_if_new_day()
        return (self._spent_today + cost) <= self.policy.daily_budget

    def record_spend(self, cost: float) -> None:
        self._reset_if_new_day()
        self._spent_today += cost

    @property
    def spent_today(self) -> float:
        return self._spent_today


__all__ = ["EgressBroker", "BrokerPolicy", "DEFAULT_ALLOWED_FIELDS"]
