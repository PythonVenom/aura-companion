"""Working Memory — кольцевой буфер (ADR-122, слой 2).

Наука: Baddeley, A. D. & Hitch, G. (1974). Working Memory.
       Psychology of Learning and Motivation, 8, 47-89.
       Cowan, N. (2001). The magical number 4 in short-term memory.
       Behavioral and Brain Sciences, 24(1), 87-114.

В Aura: последние N реплик диалога, что LLM "держит в уме".
Не персистится. По умолчанию 20 сообщений (~ Cowan 4 chunks * 5).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Turn:
    role: str        # "user" | "aura"
    text: str
    ts: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    meta: dict = field(default_factory=dict)


class WorkingMemory:
    def __init__(self, capacity: int = 20) -> None:
        self.capacity = capacity
        self._buf: deque[Turn] = deque(maxlen=capacity)

    def push(self, role: str, text: str, **meta) -> None:
        self._buf.append(Turn(role=role, text=text, meta=meta))

    def last(self, n: int = 5) -> list[Turn]:
        return list(self._buf)[-n:]

    def all(self) -> list[Turn]:
        return list(self._buf)

    def as_messages(self, n: int = 10) -> list[dict]:
        """Формат для Ollama chat: [{role, content}, ...]."""
        out = []
        for t in self.last(n):
            r = "user" if t.role == "user" else "assistant"
            out.append({"role": r, "content": t.text})
        return out

    def clear(self) -> None:
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)


_SINGLETON: WorkingMemory | None = None


def get_working() -> WorkingMemory:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = WorkingMemory()
    return _SINGLETON
