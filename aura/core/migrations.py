"""#151 SQLite Migrations — версионирование схем БД.

Наука:
- Ambler & Sadalage 2003 (Refactoring Databases) — evolutionary DB design
- Rails migrations (DHH 2005) — versioned schema changes
- Idempotent migrations (Fowler 2003) — можно запускать N раз

Зачем:
  У 6+ БД (recall.db, proactive.db, curiosity.db, meds.db, stress.db,
  memories.db). Когда добавим поле — сломается старая схема у бати.
  Миграции → плавное обновление без потери данных.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Migration:
    """Одна миграция: version + функция."""
    version: int
    description: str
    apply: Callable[[sqlite3.Connection], None]


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at REAL NOT NULL,
            description TEXT NOT NULL
        )
    """)
    conn.commit()


def current_version(conn: sqlite3.Connection) -> int:
    """Текущая версия схемы (0 если нет)."""
    _ensure_version_table(conn)
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] if row and row[0] is not None else 0


def apply_migrations(db_path: Path, migrations: list[Migration]) -> int:
    """Применить миграции (идемпотентно).

    Returns: сколько миграций применено.
    """
    conn = sqlite3.connect(db_path)
    try:
        _ensure_version_table(conn)
        if not migrations:
            return 0
        cur = current_version(conn)
        applied = 0
        for m in sorted(migrations, key=lambda x: x.version):
            if m.version <= cur:
                continue
            try:
                m.apply(conn)
                import time
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
                    (m.version, time.time(), m.description),
                )
                conn.commit()
                applied += 1
            except Exception as e:
                conn.rollback()
                raise RuntimeError(
                    f"Migration {m.version} ({m.description}) failed: {e}"
                )
        return applied
    finally:
        conn.close()


__all__ = ["Migration", "apply_migrations", "current_version"]
