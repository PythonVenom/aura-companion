"""Guided UI — простой бой: АТАКА / ПОЧИТАТЬ / РАЗВЕДКА.

Флоу:
    1. Показать цель
    2. Три действия: атака / почитать / разведка
    3. После атаки — подтверждение
    4. Готово — цель уничтожена

Наука: Nielsen 1993 (recognition over recall),
       Juul 2005 (Half-Real — правила ведут сюжет).
"""

from __future__ import annotations

import contextlib
import time

from aura.game.problem import Problem


# ── Рендер ─────────────────────────────────────────────
def _row(text: str, W: int = 60) -> str:
    try:
        from wcwidth import wcswidth
        v = wcswidth(text)
    except ImportError:
        v = len(text)
    pad = " " * max(0, W - v - 2)
    return f"║ {text}{pad} ║"


def _frame(lines: list[str], W: int = 60) -> None:
    print()
    print("╔" + "═" * W + "╗")
    for l in lines:
        print(_row(l, W))
    print("╚" + "═" * W + "╝")


def _wrap(text: str, W: int = 60) -> list[str]:
    words = text.split()
    out, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > W - 4:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def _ask() -> str:
    try:
        return input("\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _say(orch, event: str, **ctx) -> None:
    if orch is None:
        return
    with contextlib.suppress(Exception):
        orch.say(event, **ctx)


# ── Экран цели ─────────────────────────────────────────
def _show_target(problem: Problem, shields: int, attempts: int) -> None:
    pat = problem.pattern
    hp = problem.hp
    max_hp = problem.max_hp
    diff = pat.difficulty
    bar_len = 20
    filled = int(hp / max_hp * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    _frame([
        f"⚠️  ЦЕЛЬ: {problem.code}  —  {pat.title}",
        f"📍 Сектор: {problem.sector}:{problem.line}",
        "",
        f"📊 HP цели: {bar} {hp}/{max_hp}",
        f"🔥 Сложность: {diff}/5  ({problem.importance})  |  Попыток: {attempts}",
        f"🛡  Щиты корабля: {shields}%",
    ])
    # Пояснение что делать
    print()
    print("  ℹ️  Что делать:")
    if attempts == 0:
        print("     Сначала ПОЧИТАЙ — узнаешь паттерн и код.")
        print("     Потом АТАКА — применишь фикс.")
    else:
        print(f"     HP цели: {hp}/{max_hp}. Правильное оружие — "
              f"то, что соответствует стратегии паттерна.")
    print()
    print("  💡 Урон при промахе:", pat.difficulty * 5,
          "(разведка −30%, чтение −50%)")


# ── Экран трёх действий ────────────────────────────────
def _menu_actions() -> str | None:
    print()
    print("  [1] ⚔️  АТАКА     — применить фикс  ← Enter по умолчанию")
    print("  [2] 📖 ПОЧИТАТЬ  — паттерн и код")
    print("  [3] 🔍 РАЗВЕДКА  — собрать данные")
    print("  [0] 🛸 Отступить")
    raw = _ask()
    if raw == "":
        return "attack"  # Enter = атака
    return {"1": "attack", "2": "read", "3": "recon",
            "0": None}.get(raw)


# ── Экран "почитать" ───────────────────────────────────
def _show_read(problem: Problem) -> None:
    p = problem.pattern
    lines = [
        f"📖 ПАТТЕРН: {p.title}  [{p.code}]",
        "",
        f"🔥 Сложность: {p.difficulty}/5  ·  "
        f"Стратегия: {p.strategy}",
        "",
        "🔬 Наука (откуда правило):",
    ]
    lines += ["   " + l for l in _wrap(p.science, 56)]
    lines += ["", "📝 Почему так (объяснение):"]
    lines += ["   " + l for l in _wrap(p.why, 56)]
    lines += ["", "🔧 Что нужно сделать:"]
    lines += ["   " + l for l in _wrap(
        f"Применить стратегию '{p.strategy}' "
        f"к {problem.sector}:{problem.line}.", 56)]
    lines += ["", "📄 Код ДО (плохо):"]
    lines += ["   " + l for l in p.code_before.split("\n")]
    lines += ["", "✨ Код ПОСЛЕ (хорошо):"]
    lines += ["   " + l for l in p.code_after.split("\n")]
    lines += ["", "=" * 58]
    lines += ["💡 Теперь жми [1] АТАКА и применяй."]
    _frame(lines)

  # ── Экран подтверждения ────────────────────────────────
def _menu_confirm() -> str:
    print()
    print("  [1] ✅ ПОДТВЕРЖДАЮ — применить фикс  ← Enter")
    print("  [2] 🔄 СМЕНИТЬ стратегию")
    print("  [0] ⬅️  Отмена")
    raw = _ask()
    if raw == "":
        return "1"  # Enter = подтверждение
    return raw


def _menu_strategies() -> str | None:
    print()
    print("  [1] 🎯 Точечный залп   — patch  ← Enter")
    print("  [2] 🚀 Ракета          — rewrite")
    print("  [3] ⚡ Импульс         — ruff --fix")
    print("  [0] Отмена")
    raw = _ask()
    if raw == "":
        return "patch"
    return {"1": "patch", "2": "rewrite", "3": "autofix"}.get(raw)


# ── Главный цикл боя ───────────────────────────────────
def run_guided(problem: Problem, speak: bool = True) -> bool:
    """Простой бой. Три действия, подтверждение атаки.

    Returns:
        True — цель уничтожена.
        False — отступили.
    """
    orch = None
    if speak:
        with contextlib.suppress(Exception):
            from aura.voice.orchestrator import VoiceOrchestrator
            orch = VoiceOrchestrator()

    shields = 100
    attempts = 0

    _say(orch, "enemy_spotted", file=f"{problem.sector}:{problem.line}")

    while not problem.solved:
        _show_target(problem, shields, attempts)

        action = _menu_actions()
        if action is None:
            print("\n🛸 Прыжок.")
            return False

        # ── ПОЧИТАТЬ ──
        if action == "read":
            _show_read(problem)
            problem.read_done = True
            with contextlib.suppress(EOFError, KeyboardInterrupt):
                input("\nEnter — назад...")
            continue

        # ── РАЗВЕДКА ──
        if action == "recon":
            if not problem.recon_done:
                print()
                print(problem.apply_recon())
                attempts += 1
            else:
                print("\n✅ Разведка уже проведена.")
            with contextlib.suppress(EOFError, KeyboardInterrupt):
                input("\nEnter — назад...")
            continue

        # ── АТАКА: подтверждение ──
        if action == "attack":
            pat = problem.pattern
            print()
            print(f"  Рекомендуемая стратегия: {pat.strategy}")
            confirm = _menu_confirm()

            if confirm == "0":
                continue
            if confirm == "2":
                strat = _menu_strategies()
                if strat is None:
                    continue
            else:
                strat = pat.strategy

            # Вспышка
            print()
            print("  💥 Залп...")
            _say(orch, "fire", weapon=strat)
            time.sleep(0.5)

            attempts += 1
            ok, msg = problem.try_solve(strat)

            print()
            print("  ✨ Вспышка... осадок...")
            time.sleep(0.4)

            if ok:
                print()
                print(f"  ✅ {msg}")
                print()
                print(f"  🎉 {problem.code} УНИЧТОЖЕН за {attempts} попыток.")
                _say(orch, "fix_success", hull=100)
                # Записать в state
                with contextlib.suppress(Exception):
                    from aura.game.state import StateStore
                    from aura.lore.story import StoryLog
                    store = StateStore()
                    st = store.load()
                    st.add_xp(25)
                    StoryLog().log_maneuver(
                        commit=problem.code,
                        description=f"Уничтожен {problem.code} @ {problem.sector}",
                        day=st.days_on_planet(),
                        sector=st.sector,
                    )
                    store.save(st)
                    store.close()
                return True
            else:
                damage = pat.difficulty * 5
                if problem.recon_done:
                    damage = int(damage * 0.7)
                if problem.read_done:
                    damage = int(damage * 0.5)
                shields = max(0, shields - max(1, damage // 10))
                print()
                print(f"  ❌ {msg}")
                print(f"  💥 Урон: {damage}  |  HP цели: {problem.hp}/{problem.max_hp}")
                print(f"  🛡 Щиты корабля: {shields}%")
                if shields < 30:
                    print("  ⚠️  Щиты критичны. Рекомендую ПОЧИТАТЬ/РАЗВЕДКА.")
                _say(orch, "miss", shields=shields)

    return True


__all__ = ["run_guided"]
