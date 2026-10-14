"""#151 Migrations — тесты."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aura.core.migrations import (
    Migration, apply_migrations, current_version,
)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "test.db"


def _m_add_column(name: str, default: str = "''"):
    def _apply(conn):
        conn.execute(f"CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT DEFAULT {default})")
    return Migration(version=1, description="create users", apply=_apply)


def test_current_version_empty(db):
    conn = sqlite3.connect(db)
    assert current_version(conn) == 0
    conn.close()


def test_apply_single(db):
    m = _m_add_column("users")
    n = apply_migrations(db, [m])
    assert n == 1
    conn = sqlite3.connect(db)
    assert current_version(conn) == 1
    conn.close()


def test_apply_idempotent(db):
    m = _m_add_column("users")
    apply_migrations(db, [m])
    n = apply_migrations(db, [m])  # повтор
    assert n == 0  # уже применена


def test_apply_multiple_ordered(db):
    def _m2(conn):
        conn.execute("ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0")

    m1 = _m_add_column("users")
    m2 = Migration(version=2, description="add age", apply=_m2)
    n = apply_migrations(db, [m2, m1])  # порядок нарушен
    assert n == 2
    conn = sqlite3.connect(db)
    assert current_version(conn) == 2
    conn.close()


def test_apply_failed_rolls_back(db):
    def _bad(conn):
        conn.execute("THIS IS NOT SQL")

    m = Migration(version=1, description="bad", apply=_bad)
    with pytest.raises(RuntimeError):
        apply_migrations(db, [m])


def test_empty_migrations(db):
    assert apply_migrations(db, []) == 0


def test_version_table_created(db):
    apply_migrations(db, [])
    conn = sqlite3.connect(db)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert ("schema_version",) in tables
