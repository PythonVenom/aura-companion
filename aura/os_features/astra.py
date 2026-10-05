"""astra — OS feature adapters (T-os-10).

Placeholder. Реализация — отдельные задачи:
- T-os-1..9 (по ОС)
- T-os-10 — этот framework

Каждый класс: методы + graceful fallback.
"""
from __future__ import annotations


class NotImplementedAdapter:
    """База: все методы возвращают None (graceful)."""

    def __getattr__(self, name: str):
        return lambda *a, **kw: None

