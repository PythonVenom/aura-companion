"""Quest — сюжетная миссия с врагами.

Квест = задача (например, "Зачистить aura/").
Внутри — флот врагов (реальные ошибки ruff).
Бой зациклен до победы или отступления.

Наука: Campbell 1949 (Hero's Journey), Hunicke 2004 (MDA),
       Skinner 1938 (reward loop).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.game.combat import Enemy


@dataclass
class Quest:
    """Сюжетная миссия."""

    name: str                    # "Зачистить aura/"
    sector_from: str             # "STABILIZE"
    sector_to: str               # "FORMALIZE"
    enemies: list[Enemy] = field(default_factory=list)
    defeated: list[str] = field(default_factory=list)
    xp_earned: int = 0
    battles: int = 0
    aborted: bool = False

    @property
    def total(self) -> int:
        return len(self.enemies)

    @property
    def remaining(self) -> list[Enemy]:
        return [e for e in self.enemies if e.hp > 0]

    @property
    def killed(self) -> int:
        return len([e for e in self.enemies if e.hp <= 0])

    @property
    def is_clear(self) -> bool:
        return len(self.remaining) == 0

    @property
    def progress(self) -> str:
        return f"{self.killed}/{self.total}"


def make_quest_from_ruff(sector_from: str = "STABILIZE",
                         sector_to: str = "FORMALIZE",
                         target: str = "aura/") -> Quest:
    """Собирает квест из текущих ошибок ruff."""
    from aura.game.spawner import spawn_enemies_from_ruff
    enemies = spawn_enemies_from_ruff(target)
    return Quest(
        name=f"Зачистить сектор {target}",
        sector_from=sector_from,
        sector_to=sector_to,
        enemies=enemies,
    )


def make_training_quest() -> Quest:
    """Тренировочный квест — 3 врага, чтобы протестировать цикл."""
    return Quest(
        name="Тренировочный бой",
        sector_from="STABILIZE",
        sector_to="STABILIZE",
        enemies=[
            Enemy("Drone-1", "drone", "aura/train.py", 10, 50, 1),
            Enemy("Frigate-2", "frigate", "aura/train.py", 20, 120, 2),
            Enemy("Interceptor-3", "interceptor", "aura/train.py", 30, 80, 2),
        ],
    )
