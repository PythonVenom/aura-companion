"""GameEngine — ядро игры без UI.

Разделяет логику и рендер. Engine не знает про print/input/ANSI.
Возвращает данные — рендер показывает.

Наука: Brooks 1975 (база > фичи), Licklider 1960 (симбиоз),
       Hunicke 2004 (MDA — механика отдельно от эстетики).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from aura.game.combat import ARSENAL, Enemy, resolve_combat
from aura.game.state import GameState


class Phase(StrEnum):
    """Фазы игры."""

    MENU = "menu"
    SCAN = "scan"
    TARGET = "target"
    AIM = "aim"
    SHOOT = "shoot"
    RESULT = "result"
    BATTLE_END = "battle_end"
    QUIT = "quit"


@dataclass
class RenderData:
    """Что рендер должен показать. Без логики."""

    phase: Phase
    title: str = ""
    lines: list[str] = field(default_factory=list)
    options: list[tuple[str, str]] = field(default_factory=list)
    voice_event: str | None = None
    voice_ctx: dict = field(default_factory=dict)


@dataclass
class GameEngine:
    """Ядро игры. Без UI, без print, без голоса."""

    state: GameState
    phase: Phase = Phase.MENU
    current_enemy: Enemy | None = None
    enemies: list[Enemy] = field(default_factory=list)
    last_result: object | None = None
    message: str = ""

    # ── публичное API ───────────────────────────────────
    def scan(self, enemies: list[Enemy]) -> RenderData:
        """Загрузить врагов в текущий сектор."""
        self.enemies = list(enemies)
        if not self.enemies:
            self.phase = Phase.MENU
            return RenderData(
                phase=self.phase,
                title="Сектор чист",
                lines=["✅ Врагов нет. Энергоблок в норме."],
                voice_event="status",
                voice_ctx={
                    "shields": self.state.shields,
                    "reactor": "чист",
                    "sector": self.state.sector,
                    "xp": self.state.xp,
                },
            )
        self.phase = Phase.TARGET
        self.current_enemy = self.enemies[0]
        return self._render_target()

    def choose_weapon(self, action: str) -> RenderData:
        """Выбор оружия → бросок → результат."""
        if self.current_enemy is None:
            self.phase = Phase.MENU
            return RenderData(phase=self.phase, title="Нет цели")

        weapon = ARSENAL.get(action)
        if weapon is None:
            return RenderData(
                phase=self.phase,
                title="Неизвестное оружие",
                lines=[f"❌ Нет оружия '{action}'"],
            )

        if action == "skip":
            self.phase = Phase.BATTLE_END
            self.message = "Прыжок. Отступаем."
            return RenderData(
                phase=self.phase,
                title="Отступление",
                lines=["🛸 Прыжок."],
                voice_event="miss",
            )

        result = resolve_combat(
            self.current_enemy, weapon, level=self.state.level,
        )
        self.last_result = result

        # Обновляем state
        if result.hit:
            if result.xp:
                self.state.add_xp(result.xp)
        else:
            self.state.shields = max(0, self.state.shields - 10)
        self.state.hull = self.state.hull  # без изменения
        self.state.reactor = 100

        self.phase = Phase.RESULT
        return self._render_result()

    def next_target(self) -> RenderData:
        """Следующий враг или конец боя."""
        if self.current_enemy and self.current_enemy.hp > 0:
            return self._render_target()
        # Враг мёртв — берём следующего живого
        alive = [e for e in self.enemies if e.hp > 0]
        if not alive:
            self.phase = Phase.BATTLE_END
            return RenderData(
                phase=self.phase,
                title="Сектор чист",
                lines=[f"🎉 Все враги уничтожены ({len(self.enemies)} шт.)"],
                voice_event="sector_clear",
                voice_ctx={
                    "old": self.state.sector,
                    "new": self._next_sector(),
                },
            )
        self.current_enemy = alive[0]
        self.phase = Phase.TARGET
        return self._render_target()

    def to_menu(self) -> RenderData:
        self.phase = Phase.MENU
        self.current_enemy = None
        return RenderData(
            phase=self.phase,
            title="Мостик",
            lines=["Готов к приказу."],
        )

    # ── приватные рендер-данные ─────────────────────────
    def _render_target(self) -> RenderData:
        e = self.current_enemy
        assert e is not None
        lines = [
            f"⚔️  {e.name} — {e.enemy_type}, угроза {e.threat}/5",
            f"   Сектор: {e.sector}:{e.line}",
            f"   HP врага: {e.hp}",
            "",
            f"Щиты: {self.state.shields}%  |  "
            f"Корпус: {self.state.hull}  |  XP: {self.state.xp}",
            "",
            "Оружие:",
        ]
        options = []
        for i, (key, w) in enumerate(ARSENAL.items(), 1):
            sign = "+" if w.xp_reward >= 0 else ""
            lines.append(
                f"  [{i}] {w.name:<18} — шанс {w.base_chance}%, "
                f"урон {w.damage}, XP {sign}{w.xp_reward}"
            )
            options.append((str(i), key))

        return RenderData(
            phase=self.phase,
            title=f"ЦЕЛЬ: {e.name}",
            lines=lines,
            options=options,
            voice_event="enemy_spotted",
            voice_ctx={"file": f"{e.sector}:{e.line}"},
        )

    def _render_result(self) -> RenderData:
        r = self.last_result
        assert r is not None
        e = self.current_enemy
        assert e is not None
        status = "✅ Попадание" if r.hit else "❌ Промах"  # type: ignore[attr-defined]
        if r.crit:  # type: ignore[attr-defined]
            status = "🎯 КРИТ"
        return RenderData(
            phase=self.phase,
            title=status,
            lines=[
                r.message,  # type: ignore[attr-defined]
                f"HP врага: {e.hp}",
                f"XP: {self.state.xp}  |  Щиты: {self.state.shields}%",
            ],
            voice_event="fix_success" if r.hit else "miss",  # type: ignore[attr-defined]
            voice_ctx={"hull": self.state.hull} if r.hit else {},  # type: ignore[attr-defined]
        )

    def _next_sector(self) -> str:
        order = ["STABILIZE", "FORMALIZE", "MONETIZE", "EXPAND", "FRONTIER"]
        try:
            idx = order.index(self.state.sector)
            return order[min(idx + 1, len(order) - 1)]
        except ValueError:
            return "FORMALIZE"


__all__ = ["GameEngine", "Phase", "RenderData"]
