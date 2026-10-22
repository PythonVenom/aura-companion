"""OneShot — одна кнопка: почини всё, что можно.

Аналог «спустить воздух в трубе»:
  1. Снимок ДО (bugmap + errormap)
  2. Авто-фиксы (ruff --fix и безопасное)
  3. Снимок ПОСЛЕ
  4. Отчёт: что починил, что осталось

Идемпотентность: второй раз — ничего не делает,
если система чиста. Пока новый «воздух» не появился.

Наука: Goldratt 1984 (Theory of Constraints),
       Duhigg 2012 (habit loop — триггер один),
       Nielsen 1993 (минимум действий).
"""

from __future__ import annotations

import contextlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO = Path.home() / "aura-companion"
VENV_PY = str(REPO / "venv" / "bin" / "python3")
SNAPSHOT_PATH = Path.home() / ".config" / "aura" / "health.snapshot.json"


@dataclass
class OneShotReport:
    """Что сделала кнопка."""

    bugs_before: int = 0
    bugs_after: int = 0
    errors_before: int = 0
    errors_after: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    ruff_fixed: int = 0
    ruff_left: int = 0
    daemon_restarted: bool = False
    actions: list[str] = field(default_factory=list)
    verdict: str = ""  # clean | minor | major | critical
    notes: list[str] = field(default_factory=list)

    def is_clean(self) -> bool:
        return (
            self.bugs_after == 0
            and self.errors_after == 0
            and self.tests_failed == 0
            and self.ruff_left == 0
        )


# ── Снимок ─────────────────────────────────────────────

def _snapshot() -> dict:
    """Что в системе прямо сейчас."""
    snap: dict = {
        "ts": datetime.now(UTC).isoformat(),
        "bugs": 0,
        "errors": 0,
        "tests_failed": 0,
        "ruff": 0,
    }
    with contextlib.suppress(Exception):
        from aura.system.bugmap import build_bugmap
        snap["bugs"] = len(build_bugmap().bugs)
    with contextlib.suppress(Exception):
        from aura.system.errormap import build_errormap
        snap["errors"] = len(build_errormap(minutes=30).errors)
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        snap["ruff"] = len(
            [l for l in r.stdout.splitlines() if l and l[0].isupper()]
        )
    return snap


def _load_previous() -> dict | None:
    if not SNAPSHOT_PATH.exists():
        return None
    with contextlib.suppress(Exception):
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return None


def _save_snapshot(snap: dict) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Фиксы ──────────────────────────────────────────────

def _ruff_autofix() -> tuple[int, int]:
    """ruff --fix. Возвращает (починено, осталось)."""
    with contextlib.suppress(Exception):
        # Считаем до
        r0 = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        before = len([l for l in r0.stdout.splitlines() if l and l[0].isupper()])

        # Фиксим
        subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "--fix", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=60,
        )
        # Second pass (unsafe)
        subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "--fix", "--unsafe-fixes", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=60,
        )

        # Считаем после
        r1 = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        after = len([l for l in r1.stdout.splitlines() if l and l[0].isupper()])
        return max(0, before - after), after
    return 0, 0


def _quick_pytest() -> tuple[int, int]:
    """Быстрый прогон тестов. Возвращает (passed, failed)."""
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [VENV_PY, "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=str(REPO), capture_output=True, text=True, timeout=120,
        )
        import re
        passed = 0
        failed = 0
        m = re.search(r"(\d+)\s+passed", r.stdout)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", r.stdout)
        if m:
            failed = int(m.group(1))
        return passed, failed
    return 0, 0


def _restart_daemon() -> bool:
    """Перезапуск systemd (только если активен)."""
    with contextlib.suppress(Exception):
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aura.service"],
            capture_output=True, text=True, timeout=5,
        )
        if r.stdout.strip() != "active":
            return False
        subprocess.run(
            ["systemctl", "--user", "restart", "aura.service"],
            capture_output=True, text=True, timeout=15,
        )
        return True
    return False


# ── Главная: одна кнопка ──────────────────────────────

def run_oneshot(
    dry_run: bool = False,
    restart_daemon: bool = True,
    verbose: bool = True,
) -> OneShotReport:
    """Одна кнопка. Idempotent.

    Если система чиста — ничего не меняет, только отчёт.
    """
    r = OneShotReport()

    # Снимок ДО
    snap_before = _snapshot()
    r.bugs_before = snap_before["bugs"]
    r.errors_before = snap_before["errors"]
    r.ruff_left = snap_before["ruff"]

    # Проверка: есть ли вообще что чинить?
    prev = _load_previous()
    is_air_released = (
        prev is not None
        and prev.get("bugs") == r.bugs_before
        and prev.get("errors") == r.errors_before
        and prev.get("ruff") == r.ruff_left
        and r.ruff_left == 0
    )

    if is_air_released and not dry_run:
        r.verdict = "clean"
        r.notes.append("Воздуха нет. Система стабильна с прошлого раза.")
        _save_snapshot(snap_before)
        if verbose:
            print("✅ Чисто. Ничего не делаю.")
        return r

    # ruff auto-fix
    if not dry_run:
        fixed, left = _ruff_autofix()
        r.ruff_fixed = fixed
        r.ruff_left = left
        if fixed > 0:
            r.actions.append(f"Ruff: починил {fixed} ошибок")
    else:
        r.notes.append("Dry-run: фиксы не применены")

    # pytest
    if not dry_run:
        passed, failed = _quick_pytest()
        r.tests_passed = passed
        r.tests_failed = failed
        if failed > 0:
            r.actions.append(f"Pytest: {failed} упавших (проверь errormap)")

    # Перезапуск демона
    if restart_daemon and not dry_run and (r.ruff_fixed > 0 or r.tests_failed > 0):
        if _restart_daemon():
            r.daemon_restarted = True
            r.actions.append("Демон перезапущен")

    # Снимок ПОСЛЕ
    snap_after = _snapshot()
    r.bugs_after = snap_after["bugs"]
    r.errors_after = snap_after["errors"]

    # Вердикт
    if r.is_clean():
        r.verdict = "clean"
    elif r.ruff_left == 0 and r.tests_failed == 0:
        r.verdict = "minor"
    elif r.errors_after > 0 or r.tests_failed > 0:
        r.verdict = "major"
    else:
        r.verdict = "critical"

    # Сохраняем снимок
    _save_snapshot(snap_after)

    if verbose:
        print(render_report(r))
    return r


def render_report(r: OneShotReport) -> str:
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  🩹 ONE-SHOT: СПУСТИТЬ ВОЗДУХ                                ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Баги:    {r.bugs_before:>3} → {r.bugs_after:<3}                                              ║")
    lines.append(f"║  Ошибки:  {r.errors_before:>3} → {r.errors_after:<3}                                              ║")
    lines.append(f"║  Ruff:    {r.ruff_fixed} починил, {r.ruff_left} осталось                                  ║")
    lines.append(f"║  Pytest:  {r.tests_passed} passed, {r.tests_failed} failed                            ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    if r.actions:
        for a in r.actions[:5]:
            lines.append(f"║  ✅ {a[:54]:<54} ║")
    else:
        lines.append("║  (ничего не менялось)                                        ║")
    if r.notes:
        for n in r.notes[:3]:
            lines.append(f"║  ℹ️  {n[:53]:<53} ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    verdict_map = {
        "clean":    "✅ СИСТЕМА ЧИСТА — воздух спущен",
        "minor":    "🟡 Мелочи остались (не критично)",
        "major":    "🔴 Есть ошибки — см. errormap",
        "critical": "🚨 Критично — нужна ручная правка",
    }
    lines.append(f"║  {verdict_map.get(r.verdict, r.verdict):<60} ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


__all__ = ["OneShotReport", "render_report", "run_oneshot"]
