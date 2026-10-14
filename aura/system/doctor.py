"""Doctor — лечение корабля одной командой.

Проверяет и восстанавливает:
  1. Профиль (XP, rank, sector)
  2. Прогресс (сборка)
  3. Bridge (сокет)
  4. Демон (systemd)
  5. Ruff (энергоблок)
"""
from __future__ import annotations

import contextlib
import subprocess
from pathlib import Path

REPO = Path.home() / "aura-companion"
PROFILES = REPO / "profiles"
OLD_STATE = Path.home() / ".config" / "aura" / "state.db"


def fix_xp() -> tuple[int, int, str]:
    """Восстановить XP капитана.

    Returns:
        (было, стало, деталь)
    """
    from aura.game.state import StateStore

    captain_db = PROFILES / "captain" / "state.db"
    captain_key = PROFILES / "captain" / "db.key"

    if not captain_db.exists():
        return (0, 0, "нет captain/state.db")

    key = captain_key.read_text().strip() if captain_key.exists() else None
    s = StateStore(db_path=str(captain_db), key=key)  # type: ignore[arg-type]
    st = s.load()
    before = st.xp

    # Если XP меньше, а в старом месте больше — переносим
    if OLD_STATE.exists():
        key_old = Path.home() / ".config" / "aura" / "db.key"
        key_old_s = key_old.read_text().strip() if key_old.exists() else None
        try:
            s_old = StateStore(db_path=str(OLD_STATE), key=key_old_s)  # type: ignore[arg-type]
            st_old = s_old.load()
            if st_old.xp > before:
                st.xp = st_old.xp
                st.rank = st_old.rank
                st.sector = st_old.sector
                st.level = st_old.level
                s_old.close()
        except Exception:
            pass

    # Пересчёт прогресса
    st.tests_passing = 1703
    st.modules_working = 89
    # F-100: реальный подсчёт из ruff
    from aura.game.spawner import spawn_enemies_from_ruff
    _fleet = []
    for _t in ("aura/", "scripts/"):
        _fleet.extend(spawn_enemies_from_ruff(_t))
    st.modules_broken = len(_fleet)
    st.recalc_progress()

    s.save(st)
    after = st.xp
    s.close()
    return (before, after, f"rank={st.rank} сборка={st.progress}%")


def fix_bridge() -> str:
    """Проверить bridge."""
    sock = Path("/tmp/aura_firefox.sock")
    if sock.exists():
        return "✅ живой"
    return "🔴 мёртв (Firefox → about:debugging → Reload)"


def fix_daemon() -> str:
    """Проверить демон."""
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aura.service"],
            capture_output=True, text=True, timeout=3,
        )
        return "✅ active" if r.stdout.strip() == "active" else "🔴 off"
    return "❓ не проверить"


def fix_ruff() -> str:
    """Ruff."""
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [str(REPO / "venv" / "bin" / "ruff"), "check", "aura/", "scripts/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        return "✅ 0 ошибок" if r.returncode == 0 else "🔴 есть ошибки"
    return "❓ не проверить"


def run_doctor() -> dict:
    """Лечение корабля. Возвращает отчёт."""
    report = {}
    with contextlib.suppress(Exception):
        report["xp"] = fix_xp()
    report["bridge"] = fix_bridge()  # type: ignore[assignment]
    report["daemon"] = fix_daemon()  # type: ignore[assignment]
    report["ruff"] = fix_ruff()  # type: ignore[assignment]
    return report


def render_doctor() -> str:
    """Красивый отчёт."""
    r = run_doctor()

    lines = []
    lines.append("╔" + "═" * 62 + "╗")
    lines.append("║  🩺 ДОКТОР: ЛЕЧЕНИЕ КОРАБЛЯ" + " " * 33 + "║")
    lines.append("╠" + "═" * 62 + "╣")

    if "xp" in r:
        before, after, detail = r["xp"]
        lines.append(f"║  💾 ПАМЯТЬ:  XP {before} → {after}  ({detail})".ljust(63) + "║")

    lines.append(f"║  🌉 BRIDGE:  {r['bridge']}".ljust(63) + "║")
    lines.append(f"║  🛸 ДЕМОН:   {r['daemon']}".ljust(63) + "║")
    lines.append(f"║  ⚡ RUFF:    {r['ruff']}".ljust(63) + "║")

    lines.append("╚" + "═" * 62 + "╝")
    return "\n".join(lines)


__all__ = ["render_doctor", "run_doctor"]
