"""Guide — наставник боя.

Аура видит ситуацию и подталкивает капитана к решению.
3 варианта → 3 подварианта → оценка → снова 3, пока не решится.

Если 3 промаха — автоперебор: Аура сама применяет верную стратегию.

Наука: Campbell 1949 (наставник ведёт),
       Propp 1928 (функции сказки — все пути к финалу),
       Juul 2005 (Half-Real — правила ведут сюжет).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.game.patterns import has_pattern
from aura.game.problem import Problem


@dataclass
class Situation:
    """Что видит Аура прямо сейчас."""

    problem: Problem
    attempts: int = 0
    history: list[str] = field(default_factory=list)
    shields: int = 100
    hp: int = 0

    @property
    def known(self) -> bool:
        return has_pattern(self.problem.code)

    @property
    def desperate(self) -> bool:
        return self.attempts >= 3

    @property
    def critical(self) -> bool:
        return self.shields <= 30


# ── Аура видит, что нужно ──────────────────────────────
def best_action(s: Situation) -> str:
    """Рекомендация Ауры по ситуации."""
    if s.problem.solved:
        return "done"
    if s.critical:
        return "shield"
    if not s.known and not s.problem.recon_done:
        return "recon"
    if s.known and s.attempts == 0:
        return "attack"
    if s.desperate:
        return "ai"
    return "attack"


# ── Три варианта верхнего уровня ───────────────────────
def three_actions(s: Situation) -> list[tuple[str, str]]:
    """Верхние 3 варианта. Возвращает [(key, label), ...]."""
    rec = best_action(s)

    def star(k: str) -> str:
        return "⭐ " if k == rec else ""

    return [
        ("attack", f"{star('attack')}🎯 СТРЕЛЯТЬ    — применить фикс"),
        ("recon",  f"{star('recon')}🔍 РАЗВЕДАТЬ   — собрать данные"),
        ("maneuver", f"{star('maneuver')}🛸 МАНЁВР     — щит / прыжок / совет"),
    ]


def three_attacks() -> list[tuple[str, str]]:
    return [
        ("patch",   "🎯 Точный залп — patch (85%, 100)"),
        ("rewrite", "🚀 Ракета      — rewrite (60%, 150)"),
        ("autofix", "⚡ Импульс     — ruff --fix (75%, 80)"),
    ]


def three_recons(s: Situation) -> list[tuple[str, str]]:
    recon_done = s.problem.recon_done
    return [
        ("recon", "🔬 Наука паттерна" + (" ✅" if recon_done else "")),
        ("patch", "📖 Показать код ДО/ПОСЛЕ"),
        ("patch", "🗂️  Поиск в базе паттернов"),
    ]


def three_maneuvers(s: Situation) -> list[tuple[str, str]]:
    return [
        ("reset", "🛡️  Щит       — откат (−20 XP)"),
        ("defer", "🛸 Прыжок    — отложить"),
        ("recon", "📡 Спросить Дядю Р2"),
    ]


# ── Подталкивание ──────────────────────────────────────
def nudge_text(s: Situation) -> str:
    """Что Аура говорит, когда капитан промахнулся."""
    if s.problem.solved:
        return ""
    if s.desperate:
        p = s.problem.pattern
        return (
            f"⚠️  3 попытки. Автоперебор.\n"
            f"   Верная стратегия: {p.strategy}\n"
            f"   Применяю."
        )
    if s.critical:
        return "⚠️  Щиты критичны. Рекомендую щит."
    if not s.known:
        return "❓ Паттерн неизвестен. Рекомендую разведку."
    p = s.problem.pattern
    return f"💡 Подсказка: {p.why[:70]}"


__all__ = [
    "Situation",
    "best_action",
    "nudge_text",
    "three_actions",
    "three_attacks",
    "three_maneuvers",
    "three_recons",
]
