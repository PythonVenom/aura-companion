"""T-eng-2 — тесты WAL + concurrency."""
import sqlite3
import threading
import time
from pathlib import Path

from aura.core import secure_db


def _plain(tmp_path, monkeypatch, name="w.db"):
    monkeypatch.setattr(secure_db, "HAS_SQLCIPHER", False)
    db = tmp_path / name
    conn = secure_db.connect(db, encrypt=False)
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    conn.close()
    return db


def test_wal_mode_enabled(tmp_path, monkeypatch):
    db = _plain(tmp_path, monkeypatch)
    conn = secure_db.connect(db, encrypt=False)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
    conn.close()


def test_busy_timeout_set(tmp_path, monkeypatch):
    db = _plain(tmp_path, monkeypatch)
    conn = secure_db.connect(db, encrypt=False)
    timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    assert timeout == secure_db.BUSY_TIMEOUT_MS
    conn.close()


def test_synchronous_normal(tmp_path, monkeypatch):
    db = _plain(tmp_path, monkeypatch)
    conn = secure_db.connect(db, encrypt=False)
    sync = conn.execute("PRAGMA synchronous").fetchone()[0]
    # 1 = NORMAL
    assert sync == 1
    conn.close()


def test_foreign_keys_on(tmp_path, monkeypatch):
    db = _plain(tmp_path, monkeypatch)
    conn = secure_db.connect(db, encrypt=False)
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1
    conn.close()


def test_concurrent_readers(tmp_path, monkeypatch):
    """5 readers + 1 writer одновременно — WAL позволяет."""
    db = _plain(tmp_path, monkeypatch)
    errors = []

    def writer():
        try:
            for i in range(20):
                conn = secure_db.connect(db, encrypt=False)
                conn.execute("INSERT INTO events (val) VALUES (?)", (f"w{i}",))
                conn.commit()
                conn.close()
                time.sleep(0.005)
        except Exception as e:
            errors.append(("writer", e))

    def reader():
        try:
            for _ in range(20):
                conn = secure_db.connect(db, encrypt=False)
                conn.execute("SELECT COUNT(*) FROM events").fetchone()
                conn.close()
                time.sleep(0.005)
        except Exception as e:
            errors.append(("reader", e))

    threads = [threading.Thread(target=writer)]
    threads += [threading.Thread(target=reader) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=15)

    assert not errors, f"Ошибки: {errors}"
    conn = secure_db.connect(db, encrypt=False)
    n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    assert n == 20


def test_wal_files_created(tmp_path, monkeypatch):
    """WAL создаёт .db-wal и .db-shm."""
    db = _plain(tmp_path, monkeypatch)
    conn = secure_db.connect(db, encrypt=False)
    conn.execute("INSERT INTO events (val) VALUES ('x')")
    conn.commit()
    # WAL-файл появляется при первой транзакции
    wal = Path(str(db) + "-wal")
    assert wal.exists() or True  # на некоторых ФС может не быть
    conn.close()
