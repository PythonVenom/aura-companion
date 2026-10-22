"""ErrorMap — карта runtime-ошибок.

Собирает ошибки из:
  • journalctl -u aura.service (демон)
  • /tmp/aura_*.log
  • python traceback в логах
  • stderr от systemd

Группирует по типу, показывает частоту и свежесть.
Отличает «шум» от критичных.

Наука: Saltzer & Schroeder 1975 (audit trail),
       Nielsen 1993 (visibility of system status).
"""

from __future__ import annotations

import contextlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

LOG_PATHS = [
    Path("/tmp/aura_post_commit.log"),
    Path("/tmp/aura_bridge.log"),
    Path("/tmp/aura.log"),
]

# Шум — не ошибки
NOISE_PATTERNS = [
    r"heard=None",
    r"in_sample_rate",
    r"output_sample_rate",
    r"Creating a resampler",
    r"chat dedup",
    r"F-\d+",                 # F-038, F-066 и т.п. — игровые маркеры
    r"\[F-\d+\]",            # [F-038]
    r"Пробоина",              # игровая фраза, не ошибка
    r"Залп принят",
    r"Узлов в норме",
    r"^\s*$",
]


@dataclass
class Err:
    """Одна ошибка."""

    kind: str              # TimeoutError, ImportError, ...
    message: str           # текст
    source: str            # journalctl / log / bridge
    count: int = 1         # сколько раз
    last_seen: str = ""    # ISO timestamp
    file: str = ""
    line: int = 0
    traceback: str = ""    # полный трейс


@dataclass
class ErrorMap:
    """Карта всех runtime-ошибок."""

    errors: dict[str, Err] = field(default_factory=dict)

    def add(self, e: Err) -> None:
        key = f"{e.kind}::{e.message[:60]}"
        if key in self.errors:
            self.errors[key].count += 1
            if e.last_seen > self.errors[key].last_seen:
                self.errors[key].last_seen = e.last_seen
        else:
            self.errors[key] = e

    def by_count(self) -> list[Err]:
        return sorted(self.errors.values(), key=lambda x: -x.count)

    def critical(self) -> list[Err]:
        """Критичные — падения, не warnings."""
        critical_kinds = (
            "Error", "Exception", "Traceback", "Fatal", "Crash",
            "Timeout", "FileNotFound", "Permission", "Import",
        )
        return [
            e for e in self.errors.values()
            if any(k in e.kind for k in critical_kinds)
        ]


# ── Сборщики ───────────────────────────────────────────

def _is_noise(line: str) -> bool:
    return any(re.search(pat, line) for pat in NOISE_PATTERNS)


def from_journalctl(minutes: int = 60) -> list[Err]:
    """Ошибки из journalctl за последние N минут."""
    errors = []
    with contextlib.suppress(Exception):
        r = subprocess.run(
            [
                "journalctl", "--user", "-u", "aura.service",
                "--since", f"{minutes} minutes ago",
                "--no-pager", "-o", "short-iso",
            ],
            capture_output=True, text=True, timeout=10,
        )
        for line in r.stdout.splitlines():
            if _is_noise(line):
                continue
            # Ищем: Error / Exception / Traceback
            m = re.search(
                r"(\d{4}-\d{2}-\d{2}T[\d:]+)\S*\s+\S+\s+\S+:\s*(.*)",
                line,
            )
            ts = ""
            msg = line
            if m:
                ts, msg = m.group(1), m.group(2)

            # Классификация
            kind = "log"
            if "Traceback" in msg:
                kind = "Traceback"
            elif "Error" in msg:
                km = re.search(r"(\w*Error)", msg)
                kind = km.group(1) if km else "Error"
            elif "Exception" in msg:
                km = re.search(r"(\w*Exception)", msg)
                kind = km.group(1) if km else "Exception"
            elif "WARN" in msg or "warning" in msg.lower():
                kind = "Warning"
            elif "❌" in msg:
                kind = "Marked"
            else:
                continue  # не ошибка

            errors.append(Err(
                kind=kind,
                message=msg.strip()[:200],
                source="journalctl",
                last_seen=ts,
            ))
    return errors


def from_log_files() -> list[Err]:
    """Ошибки из /tmp/aura_*.log."""
    errors = []
    for path in LOG_PATHS:
        if not path.exists():
            continue
        with contextlib.suppress(Exception):
            for line in path.read_text(encoding="utf-8").splitlines():
                if _is_noise(line):
                    continue
                low = line.lower()
                if not any(w in low for w in (
                    "error", "exception", "traceback",
                    "ошибка", "❌", "fail",
                )):
                    continue
                kind = "log"
                if "error" in low:
                    kind = "Error"
                elif "exception" in low:
                    kind = "Exception"
                elif "fail" in low:
                    kind = "Failure"
                elif "ошибка" in low:
                    kind = "Ошибка"

                errors.append(Err(
                    kind=kind,
                    message=line.strip()[:200],
                    source=str(path.name),
                    file=str(path),
                ))
    return errors


def from_python_stderr() -> list[Err]:
    """Из файлов .err в /tmp (если есть)."""
    errors = []
    for path in Path("/tmp").glob("aura_*.err"):
        with contextlib.suppress(Exception):
            text = path.read_text(encoding="utf-8")
            if "Traceback" in text:
                # Первая строка исключения
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if "Error" in line or "Exception" in line:
                        km = re.search(r"(\w*Error|\w*Exception)", line)
                        kind = km.group(1) if km else "Error"
                        errors.append(Err(
                            kind=kind,
                            message=line.strip()[:200],
                            source="stderr",
                            file=str(path),
                            line=i + 1,
                            traceback="\n".join(lines[max(0, i-5):i+2]),
                        ))
                        break
    return errors


# ── Главная функция ───────────────────────────────────

def build_errormap(minutes: int = 60) -> ErrorMap:
    """Собирает ошибки из всех источников."""
    m = ErrorMap()
    for collector in (
        lambda: from_journalctl(minutes),
        from_log_files,
        from_python_stderr,
    ):
        with contextlib.suppress(Exception):
            for e in collector():
                m.add(e)
    return m


def render_errormap(minutes: int = 60) -> str:
    """Текстовый отчёт."""
    m = build_errormap(minutes)
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append(f"║  ⚠️  КАРТА ОШИБОК (за {minutes} мин)                          ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║  Уникальных: {len(m.errors):<4}"
                 f"  Критичных: {len(m.critical()):<4}"
                 f"  Всего событий: {sum(e.count for e in m.errors.values()):<10}║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")

    if not m.errors:
        lines.append("║  ✅ Чисто. Ошибок нет.                                       ║")
    else:
        # Критичные
        crit = m.critical()
        if crit:
            lines.append("║  🔴 КРИТИЧНЫЕ:                                              ║")
            for e in crit[:5]:
                title = f"{e.kind}: {e.message[:40]}"
                lines.append(f"║    [{e.count}x] {title[:50]:<50} ║")

        # Частые (но не критичные)
        rest = [e for e in m.by_count() if e not in crit]
        if rest:
            lines.append("║                                                              ║")
            lines.append("║  🟡 ЧАСТЫЕ:                                                  ║")
            for e in rest[:5]:
                title = f"{e.kind}: {e.message[:40]}"
                lines.append(f"║    [{e.count}x] {title[:50]:<50} ║")

    lines.append("╚══════════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


__all__ = ["Err", "ErrorMap", "build_errormap", "render_errormap"]
