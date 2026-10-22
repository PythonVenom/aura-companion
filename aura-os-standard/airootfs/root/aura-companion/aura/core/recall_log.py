"""#141 RecallLog — журнал событий для «что делал N минут назад».

Наука:
- Episodic memory (Tulving 1972) — автобиографические события
- Time-anchored recall (Nielsen #6) — «что было тогда?»
- Leon AI memory layers (2025) — day-to-day context

Зачем:
  Батя спрашивает «что я делал 10 минут назад?» — Aura отвечает.
  Врач: «когда вы последний раз принимали таблетки?»

БД: ~/.local/share/aura/recall.db
  events (ts REAL, agent TEXT, action TEXT, detail TEXT)
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB = Path.home() / ".local/share/aura/recall.db"


def _ensure() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT DEFAULT ''
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON events(ts)")
    conn.commit()
    conn.close()


def record(agent: str, action: str, detail: str = "") -> None:
    """Записать событие (вызывается другими агентами)."""
    try:
        _ensure()
        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO events (ts, agent, action, detail) VALUES (?, ?, ?, ?)",
            (time.time(), agent, action, detail[:500]),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def recall(minutes: int = 10) -> list[dict]:
    """Что было за последние N минут."""
    if not DB.exists():
        return []
    since = time.time() - minutes * 60
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT ts, agent, action, detail FROM events WHERE ts >= ? ORDER BY ts DESC",
            (since,),
        ).fetchall()
        conn.close()
        return [
            {"ts": r[0], "agent": r[1], "action": r[2], "detail": r[3]}
            for r in rows
        ]
    except Exception:
        return []


def format_recall(minutes: int = 10) -> str:
    """Человекочитаемый отчёт."""
    events = recall(minutes)
    if not events:
        return f"📋 За последние {minutes} мин — ничего не записано."
    lines = [f"📋 За последние {minutes} мин ({len(events)} событий):"]
    for e in events[:20]:
        t = time.strftime("%H:%M", time.localtime(e["ts"]))
        line = f"  {t} — [{e['agent']}] {e['action']}"
        if e["detail"]:
            line += f": {e['detail'][:60]}"
        lines.append(line)
    return "\n".join(lines)


__all__ = ["DB", "format_recall", "recall", "record"]
