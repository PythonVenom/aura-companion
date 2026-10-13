"""Бортовой журнал Ауры.

Хранит сюжет: дни на планете, собранные модули, манёвры, закрытые сектора.
Формат — Markdown в ~/aura_private/STORY.md (приватно, не в Git).

Использование:
    log = StoryLog()
    log.log_maneuver("f9f8390", "GameState собран", day=4, sector="STABILIZE")
    print(log.get_journal_tail(5))
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


def _default_story_path() -> Path:
    """~/aura_private/STORY.md или ~/.local/share/aura/STORY.md."""
    private = Path.home() / "aura_private"
    if private.exists():
        return private / "STORY.md"
    fallback = Path.home() / ".local" / "share" / "aura"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback / "STORY.md"


HEADER = """# БОРТОВОЙ ЖУРНАЛ — КОРАБЛЬ «AURA»

> Сюжет: аварийная посадка на планете. Капитан собирает бортовой ИИ
> по модулям, чтобы взлететь. Каждая задача — деталь Ауры.
> Каждый манёвр — запись в журнале.

"""


@dataclass
class LogEntry:
    day: int
    timestamp: str
    commit: str
    description: str


class StoryLog:
    """Читает и пишет бортовой журнал (Markdown)."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else _default_story_path()
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(HEADER, encoding="utf-8")

    def log_maneuver(
        self,
        commit: str,
        description: str,
        day: int = 1,
        sector: str = "STABILIZE",
    ) -> LogEntry:
        """Записать манёвр в журнал. Дописывает в конец файла."""
        ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
        short = commit[:7] if commit else "-------"
        entry_md = (
            f"\n## День {day}: {description}\n"
            f"> Сектор: {sector} | Координаты: {short} | {ts}\n"
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry_md)
        return LogEntry(day=day, timestamp=ts, commit=short, description=description)

    def get_journal_tail(self, n: int = 5) -> str:
        """Последние N записей (по заголовкам '## День')."""
        if not self.path.exists():
            return ""
        text = self.path.read_text(encoding="utf-8")
        blocks = re.split(r"\n(?=## День )", text)
        entries = [b for b in blocks if b.startswith("## День ")]
        return "\n".join(entries[-n:]).strip()

    def count_maneuvers(self) -> int:
        """Сколько манёвров записано (число '## День' блоков)."""
        if not self.path.exists():
            return 0
        text = self.path.read_text(encoding="utf-8")
        return len(re.findall(r"^## День ", text, flags=re.MULTILINE))


def get_briefing(state, story: StoryLog | None = None) -> str:
    """Короткий брифинг по текущему состоянию корабля.

    Args:
        state: GameState с полями days_on_planet(), sector, modules_active, modules_total.
        story: опционально StoryLog для счётчика манёвров.

    Returns:
        Строка для голоса: «День 4. Сектор STABILIZE. Собрано 4 из 10. Манёвров: 12.»
    """
    log = story or StoryLog()
    try:
        day = state.days_on_planet()
    except Exception:
        day = 1
    modules_a = len(getattr(state, "modules_active", []) or [])
    modules_t = getattr(state, "modules_total", 10)
    sector = getattr(state, "sector", "STABILIZE")
    maneuvers = log.count_maneuvers()
    return (
        f"День {day}. Сектор {sector}. "
        f"Собрано {modules_a} из {modules_t} модулей. Манёвров: {maneuvers}."
    )
