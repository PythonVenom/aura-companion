"""Combat — боевая система корабля.

Задачи = вражеские корабли. Оружие = подход к фиксу.
Бросок = шанс попадания. Крит = удача. Промах = щиты падают.

Наука: Hunicke 2004 (MDA), Skinner 1938 (variable reward),
       Csikszentmihalyi 1990 (flow 60-85%).
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Enemy:
    name: str
    enemy_type: str          # drone, frigate, leviathan
    sector: str              # aura/agents/speaker.py
    line: int
    hp: int
    threat: int              # 1-5


@dataclass
class Weapon:
    name: str
    action: str              # fix_anchor, rewrite, debug, autofix
    base_chance: int         # 0-100
    damage: int
    xp_reward: int


@dataclass
class BattleResult:
    hit: bool
    crit: bool
    roll: int
    effective_chance: int
    damage: int = 0
    xp: int = 0
    enemy_destroyed: bool = False
    message: str = ""


# Арсенал — 6 стволов
ARSENAL: dict[str, Weapon] = {
    "fix_anchor": Weapon("Точный залп", "fix_anchor", 85, 100, 25),
    "rewrite":    Weapon("Ракета",        "rewrite",    60, 150, 40),
    "debug":      Weapon("Дрон-разведчик", "debug",     95,  30, 10),
    "autofix":    Weapon("Импульс",        "autofix",   75,  80, 15),
    "rollback":   Weapon("Щит",            "rollback", 100,  0, -20),
    "skip":       Weapon("Прыжок",         "skip",     100,  0,   0),
}


def roll_hit(chance: int, level: int = 1, familiarity: int = 0) -> tuple[bool, bool, int]:
    """(попал, крит, бросок 1-100). Крит — если бросок ≤ chance/5."""
    effective = min(95, max(5, chance + (level - 1) * 2 + familiarity * 5))
    throw = random.randint(1, 100)
    crit = throw <= effective // 5
    return throw <= effective, crit, throw


def resolve_combat(enemy: Enemy, weapon: Weapon, level: int = 1,
                   familiarity: int = 0) -> BattleResult:
    """Считает бой. Обновляет enemy.hp. Возвращает результат."""
    hit, crit, throw = roll_hit(weapon.base_chance, level, familiarity)
    effective = min(95, max(5, weapon.base_chance + (level - 1) * 2 + familiarity * 5))

    if not hit:
        return BattleResult(
            hit=False, crit=False, roll=throw, effective_chance=effective,
            message=f"Промах. Бросок {throw} (порог {effective}).",
        )

    dmg = weapon.damage * (2 if crit else 1)
    enemy.hp = max(0, enemy.hp - dmg)
    xp = weapon.xp_reward * (2 if crit else 1)
    destroyed = enemy.hp <= 0

    if crit:
        msg = f"Критическое попадание! Урон {dmg}. Опыт +{xp}."
    else:
        msg = f"Попадание. Урон {dmg}. Опыт +{xp}."

    if destroyed:
        msg += f" {enemy.name} уничтожен."

    return BattleResult(
        hit=True, crit=crit, roll=throw, effective_chance=effective,
        damage=dmg, xp=xp, enemy_destroyed=destroyed, message=msg,
    )


def weapon_for(action: str) -> Weapon | None:
    """Оружие по коду действия."""
    return ARSENAL.get(action)
