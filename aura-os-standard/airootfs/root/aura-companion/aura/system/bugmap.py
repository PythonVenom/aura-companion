"""BugMap — карта багов с зависимостями.

Собирает баги из:
  • deep_check (провалившиеся системы)
  • pytest (упавшие тесты)
  • ruff (ошибки в коде)
  • TODO/FIXME в коде
  • заметки из STORY.md

Строит граф зависимостей: какой баг блокирует какие.
Показывает корневые баги (критический путь).

Наука: Goldratt 1984 (Theory of Constraints),
       Brooks 1975 (база > фичи).
"""

from __future__ import annotations

import contextlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path.home() / "aura-companion"
VENV_PY = str(REPO / "venv" / "bin" / "python3")


@dataclass
class Bug:
    """Один баг."""

    id: str                    # уникальный ID
    title: str                 # краткое описание
    source: str                # откуда: deep_check/pytest/ruff/todo/note
    severity: int              # 1-5
    file: str = ""             # где
    line: int = 0
    detail: str = ""           # подробнее
    blocks: list[str] = field(default_factory=list)  # блокирует IDs
    blocked_by: list[str] = field(default_factory=list)  # заблокирован IDs


@dataclass
class BugMap:
    """Карта всех багов."""

    bugs: dict[str, Bug] = field(default_factory=dict)

    def add(self, bug: Bug) -> None:
        self.bugs[bug.id] = bug

    def roots(self) -> list[Bug]:
        """Корневые баги — ни от кого не зависят, но что-то блокируют."""
        return [
            b for b in self.bugs.values()
            if not b.blocked_by and b.blocks
        ]

    def leaves(self) -> list[Bug]:
        """Зависимые — ждут других."""
        return [b for b in self.bugs.values() if b.blocked_by]

    def by_severity(self) -> list[Bug]:
        return sorted(self.bugs.values(), key=lambda b: -b.severity)

    def critical_path(self) -> list[Bug]:
        """Критический путь: корни → листья."""
        result: list[Bug] = []
        seen: set[str] = set()

        def visit(bug_id: str) -> None:
            if bug_id in seen or bug_id not in self.bugs:
                return
            seen.add(bug_id)
            bug = self.bugs[bug_id]
            for dep in bug.blocked_by:
                visit(dep)
            result.append(bug)

        for b in self.bugs.values():
            visit(b.id)
        return result


# ── Сборщики багов ─────────────────────────────────────

def from_deep_check() -> list[Bug]:
    """Баг из провалившихся систем."""
    bugs = []
    with contextlib.suppress(Exception):
        from aura.system.deep_check import run_deep_check
        report = run_deep_check()
        for r in report.failures():
            bugs.append(Bug(
                id=f"dc_{r.name.lower().replace(' ', '_')}",
                title=f"Система: {r.name}",
                source="deep_check",
                severity=3,
                detail=f"{r.detail} → {r.fix}",
            ))
    return bugs


def from_pytest() -> list[Bug]:
    """Баг из упавших тестов."""
    bugs = []
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [VENV_PY, "-m", "pytest", "tests/", "-q", "--tb=no", "--co", "-q"],
            cwd=str(REPO), capture_output=True, text=True, timeout=60,
        )
        # Быстрая проверка — только список
        fail_match = re.search(r"(\d+) failed", r.stdout)
        if fail_match:
            n = int(fail_match.group(1))
            bugs.append(Bug(
                id="pytest_failures",
                title=f"Тестов упало: {n}",
                source="pytest",
                severity=4,
                detail="Flaky тесты (isolation issue)",
            ))
    return bugs


def from_ruff() -> list[Bug]:
    """Баг из ошибок ruff."""
    bugs = []
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [VENV_PY, "-m", "ruff", "check", "aura/"],
            cwd=str(REPO), capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            count = len(re.findall(r"^[A-Z]+\d+", r.stdout, re.MULTILINE))
            bugs.append(Bug(
                id="ruff_errors",
                title=f"Ruff: {count} ошибок",
                source="ruff",
                severity=2,
                detail="ruff check --fix aura/",
            ))
    return bugs


def from_todo() -> list[Bug]:
    """TODO/FIXME в коде."""
    bugs = []
    pattern = re.compile(r"#\s*(TODO|FIXME|XXX|HACK)[\s:]+(.{0,80})")
    for py in (REPO / "aura").rglob("*.py"):
        with contextlib.suppress(Exception):
            text = py.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                m = pattern.search(line)
                if m:
                    kind, msg = m.group(1), m.group(2).strip()
                    rel = str(py.relative_to(REPO))
                    bugs.append(Bug(
                        id=f"todo_{rel}_{i}".replace("/", "_").replace(".", "_"),
                        title=f"{kind}: {msg[:50]}",
                        source="todo",
                        severity=1,   # F-067: TODO = заметка, не баг
                        file=rel,
                        line=i,
                    ))
    return bugs[:20]  # не больше 20


def from_notes() -> list[Bug]:
    """Из STORY.md — заметки с пометкой баг."""
    bugs = []  # type: ignore[var-annotated]
    story = Path.home() / "aura_private" / "STORY.md"
    if not story.exists():
        return bugs
    with contextlib.suppress(Exception):
        text = story.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if "баг" in low or "bug" in low or "не работает" in low:
                if line.startswith(">") or line.startswith("-"):
                    bugs.append(Bug(
                        id=f"note_{i}",
                        title=line.strip("> -#")[:60],
                        source="note",
                        severity=3,
                        file="STORY.md",
                        line=i,
                    ))
    return bugs[-5:]  # последние 5


# ── Главная функция ───────────────────────────────────

def build_bugmap() -> BugMap:
    """Собирает все баги и строит карту."""
    m = BugMap()
    for collector in (
        from_deep_check,
        from_ruff,
        from_pytest,
        from_todo,
        from_notes,
    ):
        with contextlib.suppress(Exception):
            for b in collector():
                m.add(b)

    # Простая эвристика зависимостей:
    # deep_check провал → часто блокирует всё остальное
    for b in m.bugs.values():
        if b.source == "deep_check":
            for other in m.bugs.values():
                if other.source in ("pytest", "todo"):
                    other.blocked_by.append(b.id)
                    b.blocks.append(other.id)

    return m


def render_bugmap() -> str:
    """Текстовый отчёт с критическим путём."""
    m = build_bugmap()
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  🐛 КАРТА БАГОВ                                              ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Всего багов: {len(m.bugs):<4}"
                 f"  Корневых: {len(m.roots()):<4}"
                 f"  Зависимых: {len(m.leaves()):<15}║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")

    if not m.bugs:
        lines.append("║  ✅ Чисто. Багов нет.                                        ║")
    else:
        # Корневые
        if m.roots():
            lines.append("║  🌳 КОРНЕВЫЕ (сначала их):                                   ║")
            for b in m.roots()[:5]:
                lines.append(f"║    [{b.severity}] {b.title[:48]:<48} ║")
                if b.blocks:
                    lines.append(f"║       блокирует: {len(b.blocks)} других{' ' * 35}║")

        # Зависимые
        if m.leaves():
            lines.append("║                                                              ║")
            lines.append("║  🍃 ЗАВИСИМЫЕ (подождут):                                    ║")
            for b in m.leaves()[:5]:
                lines.append(f"║    [{b.severity}] {b.title[:48]:<48} ║")

        # Критический путь
        path = m.critical_path()
        if path:
            lines.append("║                                                              ║")
            lines.append("║  🎯 ПОРЯДОК РЕШЕНИЯ (критический путь):                       ║")
            for i, b in enumerate(path[:8], 1):
                lines.append(f"║    {i}. {b.title[:54]:<54} ║")

    lines.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


__all__ = ["Bug", "BugMap", "build_bugmap", "render_bugmap"]
