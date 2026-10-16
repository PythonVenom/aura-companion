"""ContextMemory — ring buffer событий (ADR-096)."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

DEFAULT_MAX = 100


@dataclass
class ContextEvent:
    kind: str
    text: str
    ts: float
    meta: dict = field(default_factory=dict)


class ContextMemory:
    def __init__(self, maxlen: int = DEFAULT_MAX):
        self.events: deque = deque(maxlen=maxlen)

    def add(self, kind: str, text: str, meta: dict | None = None) -> None:
        self.events.append(ContextEvent(kind=kind, text=text, ts=time.time(), meta=meta or {}))

    def recent(self, minutes: int = 10) -> list:
        cutoff = time.time() - minutes * 60
        return [e for e in self.events if e.ts >= cutoff]

    def summary(self, minutes: int = 10) -> str:
        evs = self.recent(minutes)
        if not evs:
            return f"За последние {minutes} мин ничего не делал"
        lines = [f"За последние {minutes} мин ({len(evs)} событий):"]
        for e in evs[-10:]:
            t = time.strftime("%H:%M", time.localtime(e.ts))
            lines.append(f"  {t} [{e.kind}] {e.text}")
        return "\n".join(lines)


_context = ContextMemory()


def get_context() -> ContextMemory:
    return _context


__all__ = ["ContextEvent", "ContextMemory", "get_context"]
