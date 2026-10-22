"""T-sec-1 — SQLCipher: шифрование данных покоя.

Наука:
- NIST SP 800-111 — Guide to Storage Encryption Technologies
- NIST FIPS 197 — AES
- RFC 8018 — PBKDF2 (KDF для пароля)
- SQLCipher (Zetetic 2008) — SQLite + AES-256-CBC
- freedesktop Secret Service (keyring) — хранение мастер-пароля

Идея: все БД с личными данными (медицина, память, эмоции)
шифруются. Ключ — в системном keyring (не в файле).

Fallback:
- Если sqlcipher3 установлен → шифрование активно.
- Если нет → warning + обычный SQLite (graceful degradation).
"""
from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

KEYRING_SERVICE = "aura-db"
KEYRING_USER = "master-key"

# Пытаемся импортировать sqlcipher3 (drop-in замена sqlite3)
try:
    from sqlcipher3 import dbapi2 as sqlcipher  # type: ignore
    HAS_SQLCIPHER = True
except ImportError:
    sqlcipher = None
    HAS_SQLCIPHER = False


def _get_or_create_key() -> str | None:
    """Получить мастер-пароль из keyring или создать."""
    try:
        import keyring
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        if key:
            return key
        # Генерируем 32 байта, base64
        import base64
        import secrets
        key = base64.b64encode(secrets.token_bytes(32)).decode()
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key)
        return key
    except Exception:
        return None


def is_available() -> bool:
    """Проверить, доступен ли SQLCipher."""
    if not HAS_SQLCIPHER:
        return False
    return _get_or_create_key() is not None


# --- T-eng-2: WAL + concurrency ---
# Наука: SQLite WAL (sqlite.org), Kleppmann 2017 (DDIA)
# Readers не блокируют writer, writer не блокирует readers.
# busy_timeout — ждать до 10 сек, не падать сразу.
BUSY_TIMEOUT_MS = 10_000


def _configure_concurrency(conn) -> None:
    """WAL mode + busy_timeout (T-eng-2).

    WAL: readers + 1 writer параллельно (SQLite 3.7+).
    NORMAL synchronous: быстрее FULL, безопаснее OFF.
    """
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA cache_size = -2000")  # 2 MB кэш
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.secure_db').warning(
            'secure_db error: %s', e, exc_info=True)


def _configure_cipher(conn) -> None:
    """Настроить SQLCipher: AES-256-CBC, PBKDF2-HMAC-SHA512, 256k итераций."""
    if not HAS_SQLCIPHER:
        return
    try:
        # SQLCipher 4.x defaults (Zetetic docs)
        conn.execute("PRAGMA cipher_page_size = 4096")
        conn.execute("PRAGMA kdf_iter = 256000")
        conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
        conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.secure_db').warning(
            'secure_db error: %s', e, exc_info=True)


def connect(path: Path | str, *, encrypt: bool = True):
    """Открыть БД. Если encrypt=True и SQLCipher доступен → шифрование.

    Возвращает sqlite3.Connection (обычный или SQLCipher-совместимый).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not encrypt:
        conn = sqlite3.connect(str(path))  # AURA_WAL_V1
        _configure_concurrency(conn)
        return conn

    if not HAS_SQLCIPHER:
        warnings.warn(
            "SQLCipher не установлен. Данные НЕ шифруются. "
            "Установи: pip install sqlcipher3-binary",
            RuntimeWarning,
            stacklevel=2,
        )
        conn = sqlite3.connect(str(path))  # AURA_WAL_V1
        _configure_concurrency(conn)
        return conn

    key = _get_or_create_key()
    if not key:
        warnings.warn(
            "Keyring недоступен. Данные НЕ шифруются.",
            RuntimeWarning,
            stacklevel=2,
        )
        conn = sqlite3.connect(str(path))  # AURA_WAL_V1
        _configure_concurrency(conn)
        return conn

    conn = sqlcipher.connect(str(path))
    # ВАЖНО: сначала PRAGMA key, потом всё остальное
    conn.execute(f"PRAGMA key = \"{key}\"")
    _configure_cipher(conn)
    _configure_concurrency(conn)  # AURA_WAL_V1
    # Проверка: читается ли схема (если нет — wrong key)
    try:
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except Exception as exc:
        conn.close()
        raise RuntimeError(f"SQLCipher: неверный ключ или повреждённая БД: {exc}")
    return conn


def encrypt_legacy(legacy_path: Path, *, keep_backup: bool = True) -> Path:
    """Зашифровать существующую незашифрованную SQLite.

    Наука: SQLCipher `sqlcipher_export()`. Безопасно: backup сохраняется.
    Возвращает путь зашифрованной БД (с суффиксом .enc).
    """
    if not HAS_SQLCIPHER:
        raise RuntimeError("SQLCipher не установлен. pip install sqlcipher3-binary")
    legacy_path = Path(legacy_path)
    if not legacy_path.exists():
        raise FileNotFoundError(legacy_path)

    key = _get_or_create_key()
    if not key:
        raise RuntimeError("Keyring недоступен")

    enc_path = legacy_path.with_suffix(legacy_path.suffix + ".enc")
    if enc_path.exists():
        enc_path.unlink()

    # Открываем legacy как обычный SQLite → ATTACH зашифрованную → export
    plain = sqlite3.connect(str(legacy_path))
    try:
        plain.execute(f"ATTACH DATABASE '{enc_path}' AS encrypted KEY \"{key}\"")
        plain.execute("SELECT sqlcipher_export('encrypted')")
        plain.execute("DETACH DATABASE encrypted")
    finally:
        plain.close()

    # Настраиваем KDF на новом файле
    conn = sqlcipher.connect(str(enc_path))
    conn.execute(f"PRAGMA key = \"{key}\"")
    _configure_cipher(conn)
    conn.close()

    if keep_backup:
        backup = legacy_path.with_suffix(legacy_path.suffix + ".plain.bak")
        legacy_path.rename(backup)
        enc_path.rename(legacy_path)
    return enc_path


def verify(path: Path) -> bool:
    """Проверить, что БД читается с текущим ключом."""
    try:
        conn = connect(path, encrypt=True)
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        conn.close()
        return True
    except Exception:
        return False


def status() -> dict:
    """Публичный API: статус шифрования."""
    return {
        "sqlcipher_installed": HAS_SQLCIPHER,
        "keyring_available": _get_or_create_key() is not None,
        "active": HAS_SQLCIPHER and _get_or_create_key() is not None,
        "algorithm": "AES-256-CBC + PBKDF2-HMAC-SHA512" if HAS_SQLCIPHER else None,
        "kdf_iterations": 256000 if HAS_SQLCIPHER else 0,
    }


__all__ = [
    "HAS_SQLCIPHER",
    "connect",
    "encrypt_legacy",
    "is_available",
    "status",
    "verify",
]
