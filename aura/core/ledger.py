"""#32 Profile Ledger — Ed25519 подписи профилей.

Наука:
- Ed25519 (Bernstein et al. 2011) — 32-байт ключ, 64-байт подпись
- Self-sovereign identity (Allen 2016) — пользователь владеет ключом
- Verifiable Credentials (W3C 2019) — стандарт подписанных данных

Применение в Aura:
- Профиль пользователя подписан ключом → tamper-proof
- Агенты обмениваются подписанными сообщениями → защита от MITM
- Ротация ключей через SQLite-историю

Пути:
- Приватный ключ:  ~/.config/aura/keys/ed25519.key (chmod 600)
- Публичный ключ:  ~/.config/aura/keys/ed25519.pub
- История подписей: ~/.config/aura/ledger.db
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

CONFIG_DIR = Path.home() / ".config/aura"
KEY_DIR = CONFIG_DIR / "keys"
PRIV_PATH = KEY_DIR / "ed25519.key"
PUB_PATH = KEY_DIR / "ed25519.pub"
LEDGER_DB = CONFIG_DIR / "ledger.db"


def _ensure_dirs() -> None:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(KEY_DIR, 0o700)


def generate_keypair(force: bool = False) -> tuple[Path, Path]:
    """Сгенерировать Ed25519-пару. Если ключ есть и force=False — не перезаписывать."""
    _ensure_dirs()
    if PRIV_PATH.exists() and not force:
        return PRIV_PATH, PUB_PATH

    priv = Ed25519PrivateKey.generate()
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIV_PATH.write_bytes(priv_bytes)
    os.chmod(PRIV_PATH, 0o600)
    PUB_PATH.write_bytes(pub_bytes)
    os.chmod(PUB_PATH, 0o644)
    return PRIV_PATH, PUB_PATH


def _load_priv() -> Ed25519PrivateKey:
    if not PRIV_PATH.exists():
        generate_keypair()
    return serialization.load_pem_private_key(PRIV_PATH.read_bytes(), password=None)  # type: ignore


def _load_pub() -> Ed25519PublicKey:
    if not PUB_PATH.exists():
        generate_keypair()
    return serialization.load_pem_public_key(PUB_PATH.read_bytes())  # type: ignore


def _canonical(data: dict[str, Any]) -> bytes:
    """Канонический JSON (sorted keys, no spaces, UTF-8)."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sign(data: dict[str, Any], agent: str | None = None) -> bytes:
    """Подписать dict. Возвращает 64-байтную подпись."""
    priv = _load_priv()
    payload = _canonical(data)
    sig = priv.sign(payload)
    _log(agent, data, sig, verified=True)
    return sig


def verify(data: dict[str, Any], signature: bytes, pubkey: Ed25519PublicKey | None = None) -> bool:
    """Проверить подпись dict. True если валидна."""
    try:
        pub = pubkey or _load_pub()
        pub.verify(signature, _canonical(data))
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


def _ensure_db() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LEDGER_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            agent TEXT,
            payload TEXT NOT NULL,
            sig_b64 TEXT NOT NULL,
            verified INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _log(agent: str | None, data: dict, sig: bytes, verified: bool) -> None:
    try:
        _ensure_db()
        conn = sqlite3.connect(LEDGER_DB)
        conn.execute(
            "INSERT INTO ledger (ts, agent, payload, sig_b64, verified) VALUES (?, ?, ?, ?, ?)",
            (time.time(), agent, json.dumps(data, ensure_ascii=False), base64.b64encode(sig).decode(), int(verified)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # никогда не падаем из-за логирования


def public_key_b64() -> str:
    """Публичный ключ в base64 (для обмена)."""
    pub = _load_pub()
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode()


__all__ = ["generate_keypair", "sign", "verify", "public_key_b64", "PRIV_PATH", "PUB_PATH", "LEDGER_DB"]
