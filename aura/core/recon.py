"""Recon subsystem — парсер .tasks формата + runner + formatter.

ADR-068: структурированный протокол «задача → команды → вывод».
zsh обрывает paste >1024 → ассистент генерит .tasks, runner исполняет.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


_BLOCK_RE = re.compile(r"^##\s+id=(\S+)\s+name=(\S+)\s*$")
_ENTRY_RE = re.compile(r"^(cmd|file|heredoc):\s*(.*)$")


@dataclass
class TaskBlock:
    id: str
    name: str
    entries: list = field(default_factory=list)


def parse_tasks(text: str) -> list:
    """Распарсить .tasks файл в список TaskBlock."""
    blocks: list = []
    current: TaskBlock | None = None

    for raw in text.splitlines():
        line = raw.rstrip()

        if not line.strip():
            continue
        if line.lstrip().startswith("#") and not line.lstrip().startswith("## id="):
            continue

        m = _BLOCK_RE.match(line)
        if m:
            current = TaskBlock(id=m.group(1), name=m.group(2))
            blocks.append(current)
            continue

        m = _ENTRY_RE.match(line)
        if m and current is not None:
            kind, payload = m.group(1), m.group(2).strip()
            current.entries.append((kind, payload))
            continue

    # блоки без entries не считаются валидными
    return [b for b in blocks if b.entries]
