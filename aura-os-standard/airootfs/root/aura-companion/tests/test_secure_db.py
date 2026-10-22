"""T-sec-1 — тесты secure_db (SQLCipher)."""
import sqlite3
from pathlib import Path

from aura.core import secure_db


def test_status_basic():
    s = secure_db.status()
    assert "sqlcipher_installed" in s
    assert "active" in s
    assert "algorithm" in s


def test_connect_plain_when_not_encrypt(tmp_path):
    db = tmp_path / "plain.db"
    conn = secure_db.connect(db, encrypt=False)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    row = conn.execute("SELECT x FROM t").fetchone()
    assert row[0] == 42
    conn.close()


def test_connect_encrypt_fallback(tmp_path, monkeypatch):
    """Если SQLCipher нет — warning + обычный SQLite."""
    monkeypatch.setattr(secure_db, "HAS_SQLCIPHER", False)
    db = tmp_path / "fb.db"
    with pytest.warns(RuntimeWarning):
        conn = secure_db.connect(db, encrypt=True)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()


def test_encrypt_legacy_requires_sqlcipher(tmp_path, monkeypatch):
    monkeypatch.setattr(secure_db, "HAS_SQLCIPHER", False)
    db = tmp_path / "legacy.db"
    sqlite3.connect(str(db)).close()
    import pytest
    with pytest.raises(RuntimeError, match="SQLCipher"):
        secure_db.encrypt_legacy(db)


def test_verify_plain_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(secure_db, "HAS_SQLCIPHER", False)
    db = tmp_path / "v.db"
    conn = secure_db.connect(db, encrypt=False)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.commit()
    conn.close()
    assert secure_db.verify(db) is True


def test_verify_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setattr(secure_db, "HAS_SQLCIPHER", False)
    # Файл не существует → SQLite создаст пустой при connect
    # verify должен вернуть True (схема читается, пустая)
    db = tmp_path / "empty.db"
    assert secure_db.verify(db) is True


import pytest  # noqa: E402  — для pytest.warns/raises
