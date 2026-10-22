"""PC UI — управление железом из кабинета.

Меню: яркость 0-10, громкость 0-10, mute.

Наука: Nielsen 1993 (recognition over recall).
"""

from __future__ import annotations

from aura.agents.pc_control import (
    brightness_get,
    brightness_set,
    mute_toggle,
    volume_get,
    volume_set,
)


def _bar(pct: int, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def show_pc_status() -> None:
    b = brightness_get()
    v = volume_get()
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🖥  УПРАВЛЕНИЕ ПК                                            ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    b_str = f"{b:>3}%" if b >= 0 else " n/a"
    v_str = f"{v:>3}%" if v >= 0 else " n/a"
    print(f"║  🔆 Яркость:  {_bar(b if b >= 0 else 0)} {b_str}             ║")
    print(f"║  🔊 Громкость: {_bar(v if v >= 0 else 0)} {v_str}             ║")
    print("╚══════════════════════════════════════════════════════════════╝")


def pc_menu() -> None:
    """Меню управления ПК. Возвращает когда игрок жмёт 0."""
    while True:
        show_pc_status()
        print()
        print("  [1] 🔆 Яркость 0-10")
        print("  [2] 🔊 Громкость 0-10")
        print("  [3] 🔇 Mute переключить")
        print("  [4] 🔆 Ярче (+10%)")
        print("  [5] 🔅 Темнее (−10%)")
        print("  [6] 🔊 Громче (+10%)")
        print("  [7] 🔉 Тише (−10%)")
        print("  [0] Назад")
        try:
            raw = input("\nКапитан? > ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if raw in ("0", "q", ""):
            return
        elif raw == "1":
            try:
                n = int(input("Яркость 0-10: ").strip())
            except (ValueError, EOFError, KeyboardInterrupt):
                continue
            n = max(0, min(10, n))
            brightness_set(n * 10)
        elif raw == "2":
            try:
                n = int(input("Громкость 0-10: ").strip())
            except (ValueError, EOFError, KeyboardInterrupt):
                continue
            n = max(0, min(10, n))
            volume_set(n * 10)
        elif raw == "3":
            mute_toggle()
        elif raw == "4":
            cur = brightness_get()
            brightness_set(min(100, (cur if cur >= 0 else 50) + 10))
        elif raw == "5":
            cur = brightness_get()
            brightness_set(max(0, (cur if cur >= 0 else 50) - 10))
        elif raw == "6":
            cur = volume_get()
            volume_set(min(100, (cur if cur >= 0 else 50) + 10))
        elif raw == "7":
            cur = volume_get()
            volume_set(max(0, (cur if cur >= 0 else 50) - 10))


__all__ = ["pc_menu", "show_pc_status"]
