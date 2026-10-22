"""Combat UI — интерфейс боя для капитана.

Показывает врага, варианты оружия, ждёт приказ, озвучивает результат.
Голос через VoiceOrchestrator, броски через aura.game.combat.

Наука: Hunicke 2004 (MDA), Csikszentmihalyi 1990 (flow).
"""

from __future__ import annotations

from aura.game.combat import ARSENAL, Enemy, resolve_combat
from aura.game.state import StateStore
from aura.lore.story import StoryLog
from aura.voice.orchestrator import VoiceOrchestrator

# Порядок показа оружия в интерфейсе
WEAPON_ORDER = ["fix_anchor", "rewrite", "debug", "autofix", "rollback", "skip"]


W = 60


def _row(text: str, width: int = W) -> str:
    """Строка с рамкой. Кириллица считается как 2 символа (wcwidth)."""
    try:
        from wcwidth import wcswidth
        visible = wcswidth(text)
    except ImportError:
        visible = len(text)
    if visible < 0:
        visible = len(text)
    pad = " " * max(0, width - visible)
    return f"║ {text}{pad} ║"


def show_encounter(enemy: Enemy, shields: int = 100, hull: int = 1616,
                   reactor: int = 100) -> str:
    """Собирает текст сцены боя. Возвращает для печати."""
    top = "╔" + "═" * (W + 2) + "╗"
    mid = "╠" + "═" * (W + 2) + "╣"
    bot = "╚" + "═" * (W + 2) + "╝"
    lines = [
        top,
        _row(f"⚔️  ВСТРЕЧА: {enemy.name}"),
        _row(f"Тип: {enemy.enemy_type}    Угроза: {enemy.threat}/5"),
        _row(f"Сектор: {enemy.sector}:{enemy.line}"),
        mid,
        _row(f"Щиты: {shields}%  |  Корпус: {hull} узлов  |  Энергоблок: {reactor}%"),
        bot,
        "",
        "Твоё оружие:",
    ]
    for i, key in enumerate(WEAPON_ORDER, 1):
        w = ARSENAL[key]
        sign = "+" if w.xp_reward >= 0 else ""
        lines.append(
            f"  [{i}] {w.name:<18} — шанс {w.base_chance}%, "
            f"урон {w.damage}, XP {sign}{w.xp_reward}"
        )
    return "\n".join(lines)


def ask_weapon(prompt: str = "Приказ, капитан? [1-6] ") -> str | None:
    """Спрашивает выбор 1-6. Возвращает ключ оружия или None."""
    try:
        raw = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not raw:
        return None
    if not raw.isdigit():
        return None
    idx = int(raw)
    if 1 <= idx <= len(WEAPON_ORDER):
        return WEAPON_ORDER[idx - 1]
    return None


def fight(enemy: Enemy, level: int = 1, shields: int = 100,
          hull: int = 1616, reactor: int = 100,
          speak: bool = True) -> dict:
    """Полный цикл боя: показать → выбор → бросок → голос.

    Returns:
        {"weapon": str, "result": BattleResult, "aborted": bool}
    """
    orch = VoiceOrchestrator() if speak else None

    # 1. Показать сцену
    print(show_encounter(enemy, shields, hull, reactor))
    if orch:
        orch.say("enemy_spotted",
                 file=f"{enemy.sector}:{enemy.line}")

    # 2. Спросить оружие
    action = ask_weapon()
    if action is None:
        print("\n❌ Отменено.")
        return {"weapon": None, "result": None, "aborted": True}

    weapon = ARSENAL[action]

    # 3. Бросок
    print(f"\n🎲 {weapon.name}...")
    if orch:
        orch.say("shot_fired")

    result = resolve_combat(enemy, weapon, level=level)
    print(f"\n{result.message}")

    # 4. Озвучить результат
    if orch:
        if result.enemy_destroyed:
            orch.say("fix_success", hull=hull)
        elif not result.hit:
            orch.say("miss")
        else:
            orch.say("shot_fired")

    # 5. Записать в state и журнал
    _record_battle(enemy, weapon, result, hull=hull)

    return {"weapon": action, "result": result, "aborted": False}


def _record_battle(enemy: Enemy, weapon, result, hull: int = 1616) -> None:
    """Сохранить бой в GameState и бортовой журнал."""
    try:
        store = StateStore()
        state = store.load()
        story = StoryLog()

        # XP
        if result.xp:
            state.add_xp(result.xp)

        # Щиты при промахе
        if not result.hit:
            state.shields = max(0, state.shields - 10)

        # Корпус обновляем
        state.hull = hull

        # Запись в журнал
        day = state.days_on_planet()
        desc = f"{'Победа' if result.enemy_destroyed else 'Бой'} над {enemy.name}"
        story.log_maneuver(
            commit=weapon.action,
            description=desc,
            day=day,
            sector=state.sector,
        )

        store.save(state)
        store.close()
    except Exception as e:
        print(f"⚠️ [Battle record] {e}")


# ── Turn-based: рендер проблемы ─────────────────────────
def render_problem(problem, state) -> str:
    """Показать фазу: проблема → наука → варианты."""
    p = problem.pattern
    W = 64
    top = "╔" + "═" * W + "╗"
    mid = "╠" + "═" * W + "╣"
    bot = "╚" + "═" * W + "╝"

    def row(text):
        visible = len(text)
        try:
            from wcwidth import wcswidth
            visible = wcswidth(text)
        except ImportError:
            pass
        pad = " " * max(0, W - visible - 2)
        return f"║ {text}{pad} ║"

    lines = [
        top,
        row(f"⚠️  ПРОБЛЕМА: {p.title}  [{problem.code}]"),
        row(f"📍 Сектор: {problem.sector}:{problem.line}"),
        mid,
        row(f"🔬 НАУКА: {p.science}"),
        row(f"📖 Почему: {p.why[:56]}"),
        mid,
        row(f"💡 Стратегия паттерна: {p.strategy} ({p.difficulty}/5)"),
        row(f"🎯 Попыток: {problem.attempts}  |  Разведка: {'✅' if problem.recon_done else '❌'}"),
        bot,
        "",
        "Код ДО:",
        "  " + p.code_before.replace("\n", "\n  "),
        "",
        "Код ПОСЛЕ (если угадаешь):",
        "  " + p.code_after.replace("\n", "\n  "),
    ]
    if problem.history:
        lines += ["", f"История: {' → '.join(problem.history)}"]
    return "\n".join(lines)


def ask_strategy() -> str | None:
    """Спросить стратегию решения."""
    print()
    print("Стратегии:")
    print("  [1] 🔍 Разведка (собери контекст)")
    print("  [2] 🎯 Точечная правка (patch)")
    print("  [3] 🚀 Переписать (rewrite)")
    print("  [4] ⚡ Автофикс (ruff --fix)")
    print("  [5] 🛡️ Откат (reset)")
    print("  [6] 🛸 Отложить (defer)")
    print("  [0] Выйти из боя")
    raw = input("\nРешение, капитан? > ").strip()
    mapping = {
        "1": "recon", "2": "patch", "3": "rewrite",
        "4": "autofix", "5": "reset", "6": "defer",
    }
    if raw in ("0", "q", ""):
        return None
    return mapping.get(raw)
