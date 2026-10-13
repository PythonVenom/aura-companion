"""Hyperjump — объявление обновлений системы.

Аура сообщает, что корабль прошёл гиперпрыжок (обновление):
новый commit, свежие модули, стабильная система.

Триггеры: git pull / restart / загрузка ОС.
Наука: Nielsen 1993 (visibility of system status),
       Campbell 1949 (переход между актами).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path("/home/pythonvenom/aura-companion")


def current_commit() -> str:
    """Короткий хеш HEAD или '?'."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--pretty=%h"],
            cwd=REPO, capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() or "?"
    except Exception:
        return "?"


def count_modules() -> int:
    """Сколько активных модулей в aura/agents/ (приблизительно)."""
    agents_dir = REPO / "aura" / "agents"
    if not agents_dir.exists():
        return 0
    return sum(1 for f in agents_dir.glob("*.py") if f.name != "__init__.py")


def did_hyperjump(last_commit: str, current: str | None = None) -> bool:
    """True, если commit сменился с прошлого визита."""
    now = current if current is not None else current_commit()
    if not last_commit:
        return False
    return last_commit != now


def hyperjump_context(state) -> dict:
    """Контекст для speak_line('hyperjump', **ctx)."""
    return {
        "modules": count_modules(),
        "day": state.days_on_planet(),
        "sector": state.sector,
        "commit": current_commit(),
    }
