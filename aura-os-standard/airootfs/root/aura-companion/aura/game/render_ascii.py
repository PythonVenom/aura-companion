"""RenderAscii — L1 рендер игры.

Принимает RenderData от GameEngine → возвращает строки для печати.
Никакой логики игры. Только вид.

Наука: Hunicke 2004 (MDA — эстетика отделена от механики).
"""

from __future__ import annotations

from aura.game.engine import RenderData

W = 60


def _row(text: str, width: int = W) -> str:
    """Строка с рамкой. Кириллица = 2 символа (wcwidth)."""
    try:
        from wcwidth import wcswidth
        visible = wcswidth(text)
    except ImportError:
        visible = len(text)
    if visible < 0:
        visible = len(text)
    pad = " " * max(0, width - visible)
    return f"║ {text}{pad} ║"


class RenderAscii:
    """ASCII-рендер. Совместим с любым терминалом."""

    def __init__(self, width: int = W):
        self.width = width

    def render(self, data: RenderData) -> str:
        """Собирает текст для print()."""
        top = "╔" + "═" * (self.width + 2) + "╗"
        bot = "╚" + "═" * (self.width + 2) + "╝"
        lines = [top, _row(f"⚔️  {data.title}"), bot, ""]
        for line in data.lines:
            lines.append(line)
        if data.options:
            lines.append("")
            lines.append("Варианты:")
            for num, key in data.options:
                lines.append(f"  [{num}] {key}")
        return "\n".join(lines)

    def render_menu(self, title: str, options: list[str]) -> str:
        """Плоское меню — не из RenderData, отдельно."""
        top = "╔" + "═" * (self.width + 2) + "╗"
        bot = "╚" + "═" * (self.width + 2) + "╝"
        lines = [top, _row(f"🛸 {title}"), bot]
        for i, opt in enumerate(options, 1):
            lines.append(f"  [{i}] {opt}")
        lines.append("  [0] Назад / Выход")
        return "\n".join(lines)

    def render_hud(self, state, story=None) -> str:
        """Панель корабля: щиты, корпус, XP, день."""
        try:
            day = state.days_on_planet()
        except Exception:
            day = 1
        maneuvers = story.count_maneuvers() if story else 0
        top = "╔" + "═" * (self.width + 2) + "╗"
        bot = "╚" + "═" * (self.width + 2) + "╝"
        return "\n".join([
            top,
            _row(f"🛸 AURA — БОРТОВОЙ ИИ    Сектор: {state.sector}"),
            _row(f"Щиты {state.shields}%  |  "
                 f"Корпус {state.hull}  |  Энергоблок 100%"),
            _row(f"XP {state.xp}  |  Ранг: {state.rank}  |  День {day}"),
            _row(f"Манёвров: {maneuvers}"),
            bot,
        ])


__all__ = ["RenderAscii"]
