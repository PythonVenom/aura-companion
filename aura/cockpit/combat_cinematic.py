"""CombatCinematic — кинематографический пошаговый бой.

Фазы одной попытки:
    ОБНАРУЖЕНИЕ → РАЗВЕДКА → НАВЕДЕНИЕ → ПРИЦЕЛ → ВЫСТРЕЛ → ВСПЫШКА → ОЦЕНКА

Если цель жива — цикл возвращается к НАВЕДЕНИЮ.
Если уничтожена — блок зачищен, курс на следующий.

Наука: McGonigal 2011 (игра как драма),
       Campbell 1949 (каждая попытка = микро-мономиф).
"""

from __future__ import annotations

import contextlib
import time

from aura.game.problem import Problem

PHASES = ["detect", "recon", "target", "aim", "fire", "flash", "assess"]


# ── Рендер фазы ────────────────────────────────────────
def _row(text: str, W: int = 62) -> str:
    try:
        from wcwidth import wcswidth
        visible = wcswidth(text)
    except ImportError:
        visible = len(text)
    pad = " " * max(0, W - visible - 2)
    return f"║ {text}{pad} ║"


def _wrap_row(text: str, W: int = 62) -> list[str]:
    """Длинный текст — по строкам."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > W - 4:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return [_row(t, W) for t in lines]


def render_phase(phase: str, problem: Problem, extra: dict | None = None) -> str:
    """Собирает кадр одной фазы."""
    W = 62
    top = "╔" + "═" * W + "╗"
    bot = "╚" + "═" * W + "╝"
    p = problem.pattern
    ex = extra or {}

    phase_titles = {
        "detect": "🔭 ОБНАРУЖЕНИЕ",
        "recon": "🔍 РАЗВЕДКА",
        "target": "🎯 НАВЕДЕНИЕ",
        "aim": "⚙️  ПРИЦЕЛ",
        "fire": "💥 ВЫСТРЕЛ",
        "flash": "✨ ВСПЫШКА",
        "assess": "📊 ОЦЕНКА",
    }
    lines = [top, _row(f"{phase_titles.get(phase, phase)}  [{problem.code}]")]

    if phase == "detect":
        lines += _wrap_row(f"Сектор: {problem.sector}:{problem.line}")
        lines += _wrap_row(f"Цель: {problem.raw_message or p.title}")
    elif phase == "recon":
        lines += _wrap_row(f"Наука: {p.science}")
        lines += _wrap_row(f"Паттерн: {p.title}")
        lines += _wrap_row(f"Стратегия: {p.strategy} ({p.difficulty}/5)")
    elif phase == "target":
        lines += _wrap_row("Код ДО:")
        for l in p.code_before.split("\n"):
            lines += _wrap_row(f"  {l}")
    elif phase == "aim":
        lines += _wrap_row("Код ПОСЛЕ (если угадаешь):")
        for l in p.code_after.split("\n"):
            lines += _wrap_row(f"  {l}")
        lines += _wrap_row(f"Попыток: {problem.attempts}  |  "
                           f"Разведка: {'✅' if problem.recon_done else '❌'}")
        if problem.history:
            lines += _wrap_row(f"История: {' → '.join(problem.history)}")
    elif phase == "fire":
        lines += _wrap_row(f"Оружие: {ex.get('weapon', '?')}")
    elif phase == "flash":
        lines += _wrap_row("...осед!..")
    elif phase == "assess":
        lines += _wrap_row(ex.get("message", ""))

    lines.append(bot)
    return "\n".join(lines)


# ── Диалог стратегии ───────────────────────────────────
def ask_strategy() -> str | None:
    print()
    print("Оружие:")
    print("  [1] 🔍 Разведка       — собрать данные")
    print("  [2] 🎯 Точечный залп  — правка одной строки")
    print("  [3] 🚀 Ракета         — переписать целиком")
    print("  [4] ⚡ Импульс         — ruff --fix")
    print("  [5] 🛡️  Щит            — откат")
    print("  [6] 🛸 Прыжок         — отложить")
    print("  [0] Отступить")
    raw = input("\nПриказ, капитан? > ").strip()
    mapping = {
        "1": "recon", "2": "patch", "3": "rewrite",
        "4": "autofix", "5": "reset", "6": "defer",
    }
    if raw in ("0", "q", ""):
        return None
    return mapping.get(raw)


# ── Главный цикл боя ───────────────────────────────────
def run_cinematic(problem: Problem, speak: bool = True) -> bool:
    """Полный бой с кинематографическими фазами.

    Returns:
        True — цель уничтожена.
        False — отступили.
    """
    orch = None
    if speak:
        try:
            from aura.voice.orchestrator import VoiceOrchestrator
            orch = VoiceOrchestrator()
        except Exception:
            pass

    def say(event, **ctx):
        if orch is None:
            return
        with contextlib.suppress(Exception):
            orch.say(event, **ctx)

    # ── Фаза ОБНАРУЖЕНИЕ ──
    print()
    print(render_phase("detect", problem))
    say("detect", file=f"{problem.sector}:{problem.line}")
    time.sleep(0.6)

    while not problem.solved:
        # ── Фаза РАЗВЕДКА ──
        if not problem.recon_done:
            print()
            print(render_phase("recon", problem))
            say("recon")
            time.sleep(0.5)
            problem.recon_done = True

        # ── Фаза НАВЕДЕНИЕ ──
        print()
        print(render_phase("target", problem))
        say("target", enemy=problem.code)
        time.sleep(0.3)

        # ── Фаза ПРИЦЕЛ: выбор ──
        print()
        print(render_phase("aim", problem))
        say("aim")
        strategy = ask_strategy()
        if strategy is None:
            print("\n🛸 Прыжок. Отступаем.")
            return False

        weapon_name = {
            "recon": "Разведка", "patch": "Точечный залп",
            "rewrite": "Ракета", "autofix": "Импульс",
            "reset": "Щит", "defer": "Прыжок",
        }.get(strategy, strategy)

        # ── Фаза ВЫСТРЕЛ ──
        print()
        print(render_phase("fire", problem, {"weapon": weapon_name}))
        say("fire", weapon=weapon_name)
        time.sleep(0.5)

        # Пробуем
        ok, msg = problem.try_solve(strategy)

        # ── Фаза ВСПЫШКА ──
        print()
        print(render_phase("flash", problem))
        time.sleep(0.6)

        # ── Фаза ОЦЕНКА ──
        print()
        print(render_phase("assess", problem, {"message": msg}))

        if problem.solved:
            say("assess_kill", shields=100, xp=25)
            print(f"\n🎉 {problem.code} УНИЧТОЖЕН за {problem.attempts} попыток!")
            return True
        else:
            say("assess_miss", shields=90)
            print("\n⚠️  Цель ещё активна. Повторяю цикл.")

    return True


__all__ = ["PHASES", "ask_strategy", "render_phase", "run_cinematic"]
