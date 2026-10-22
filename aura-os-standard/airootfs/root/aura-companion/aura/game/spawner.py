"""Spawner — рождение врагов из реальных ошибок.

ruff/pytest → список Enemy. Каждая ошибка = пробоина в корпусе.

Наука: Brooks 1975 (база > фичи) — реальный код = реальные враги.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from aura.game.combat import Enemy

REPO = Path.home() / "aura-companion"
VENV_PY = str(REPO / "venv" / "bin" / "python3")

# Ruff код → (тип врага, угроза, hp)
RUFF_MAP: dict[str, tuple[str, int, int]] = {
    "F401": ("drone", 1, 50),        # unused import — дрон
    "F841": ("drone", 1, 50),        # unused variable
    "E501": ("interceptor", 2, 80),  # line too long
    "I001": ("interceptor", 2, 80),  # unsorted imports
    "E401": ("interceptor", 2, 80),  # multiple imports
    "RUF022": ("frigate", 3, 120),   # unsorted __all__
    "SIM105": ("frigate", 3, 150),   # suppressible exception
    "B023": ("leviathan", 4, 250),   # loop variable
}
DEFAULT = ("frigate", 3, 150)


def classify_ruff(code: str) -> tuple[str, int, int]:
    """Ruff код → (тип, угроза, hp)."""
    return RUFF_MAP.get(code, DEFAULT)


def _parse_ruff_line(line: str) -> dict | None:
    """'aura/foo.py:34:1: F401 unused' → dict."""
    m = re.match(r"^(.+?):(\d+):(\d+):\s+([A-Z]+\d+)\s+(.*)$", line.strip())
    if not m:
        return None
    return {
        "file": m.group(1),
        "line": int(m.group(2)),
        "col": int(m.group(3)),
        "code": m.group(4),
        "message": m.group(5),
    }


def spawn_enemies_from_ruff(target: str = "aura/") -> list[Enemy]:
    """Прогнать ruff, каждый код → Enemy."""
    try:
        r = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", target,
             "--output-format=concise"],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
    except Exception:
        return []

    enemies = []
    for raw in r.stdout.splitlines():
        parsed = _parse_ruff_line(raw)
        if not parsed:
            continue
        etype, threat, hp = classify_ruff(parsed["code"])
        enemies.append(Enemy(
            name=f"{parsed['code']}",
            enemy_type=etype,
            sector=parsed["file"],
            line=parsed["line"],
            hp=hp,
            threat=threat,
        ))
    return enemies


def count_threat(enemies: list[Enemy]) -> int:
    """Суммарная угроза флота."""
    return sum(e.threat for e in enemies)
