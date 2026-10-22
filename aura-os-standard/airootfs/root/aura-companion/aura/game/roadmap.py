"""Roadmap — очередь задач из ROADMAP-V2 / TASKS-ALL-V2.

Аура читает roadmap, парсит квесты, отдаёт очередь.
После победы — сразу следующая цель. Никаких возвратов в меню.

Наука: Campbell 1949 (путешествие = череда актов),
       Suchman 1987 (план встроен в движение).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROADMAP_PATHS = [
    Path.home() / "aura_private" / "ROADMAP-V2.md",
    Path.home() / "aura_private" / "TASKS-ALL-V2.md",
]


@dataclass
class Quest:
    """Задача из roadmap."""

    code: str          # F-039, F-058
    title: str
    sector: str        # M1 STABILIZE, M2 FORMALIZE
    done: bool = False


def _parse_quests(text: str) -> list[Quest]:
    """Парсит строки вида 'F-039 ...' или '- [ ] F-039 ...'."""
    out: list[Quest] = []
    for line in text.splitlines():
        m = re.search(r"(F-\d+)[^\w]*(.{0,80})", line)
        if not m:
            continue
        code = m.group(1)
        title = m.group(2).strip(" :—-")
        done = "[x]" in line.lower() or "✅" in line
        sector = "M2 FORMALIZE"
        for mnum in ("M1", "M2", "M3", "M4", "M5"):
            if mnum in line:
                sector = mnum
                break
        out.append(Quest(code=code, title=title, sector=sector, done=done))
    return out


def load_roadmap() -> list[Quest]:
    """Читает все roadmap-файлы. Возвращает незакрытые задачи."""
    quests: dict[str, Quest] = {}
    for p in ROADMAP_PATHS:
        if not p.exists():
            continue
        for q in _parse_quests(p.read_text(encoding="utf-8")):
            quests[q.code] = q
    return [q for q in quests.values() if not q.done]


def next_quest(after: str | None = None) -> Quest | None:
    """Следующая задача после указанной (или первая)."""
    queue = load_roadmap()
    if not queue:
        return None
    if after is None:
        return queue[0]
    codes = [q.code for q in queue]
    if after in codes:
        idx = codes.index(after) + 1
        return queue[idx] if idx < len(queue) else None
    return queue[0]


def is_empty() -> bool:
    return len(load_roadmap()) == 0


__all__ = ["Quest", "is_empty", "load_roadmap", "next_quest"]
