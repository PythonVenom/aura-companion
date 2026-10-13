"""#32 Profile Ledger — тесты Ed25519."""
from __future__ import annotations

import base64
import json
import sqlite3
from pathlib import Path

import pytest

from aura.core import ledger as L


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    """Каждый тест — своя конфиг-папка."""
    monkeypatch.setattr(L, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(L, "KEY_DIR", tmp_path / "keys")
    monkeypatch.setattr(L, "PRIV_PATH", tmp_path / "keys/ed25519.key")
    monkeypatch.setattr(L, "PUB_PATH", tmp_path / "keys/ed25519.pub")
    monkeypatch.setattr(L, "LEDGER_DB", tmp_path / "ledger.db")
    yield


def test_generate_keypair_creates_files():
    L.generate_keypair()
    assert L.PRIV_PATH.exists()
    assert L.PUB_PATH.exists()


def test_private_key_chmod_600():
    L.generate_keypair()
    mode = L.PRIV_PATH.stat().st_mode & 0o777
    assert mode == 0o600, f"priv key mode = {oct(mode)}"


def test_generate_keypair_idempotent():
    L.generate_keypair()
    first = L.PRIV_PATH.read_bytes()
    L.generate_keypair()  # без force — не должен перезаписать
    assert L.PRIV_PATH.read_bytes() == first


def test_generate_keypair_force_overwrites():
    L.generate_keypair()
    first = L.PRIV_PATH.read_bytes()
    L.generate_keypair(force=True)
    assert L.PRIV_PATH.read_bytes() != first


def test_sign_returns_64_bytes():
    L.generate_keypair()
    sig = L.sign({"hello": "world"})
    assert isinstance(sig, bytes)
    assert len(sig) == 64


def test_sign_verify_roundtrip():
    L.generate_keypair()
    data = {"user": "Батя", "age": 78, "meds": ["A", "B"]}
    sig = L.sign(data)
    assert L.verify(data, sig) is True


def test_verify_rejects_tampered_payload():
    L.generate_keypair()
    sig = L.sign({"user": "Батя", "age": 78})
    assert L.verify({"user": "Хакер", "age": 78}, sig) is False


def test_verify_rejects_truncated_sig():
    L.generate_keypair()
    data = {"x": 1}
    sig = L.sign(data)
    assert L.verify(data, sig[:32]) is False


def test_verify_rejects_random_garbage():
    L.generate_keypair()
    assert L.verify({"x": 1}, b"\x00" * 64) is False


def test_canonical_is_stable():
    """Один и тот же dict — одинаковые байты, независимо от порядка ключей."""
    a = {"b": 2, "a": 1, "c": 3}
    b = {"a": 1, "c": 3, "b": 2}
    assert L._canonical(a) == L._canonical(b)


def test_canonical_unicode():
    """UTF-8 кириллица должна канонизироваться корректно."""
    data = {"имя": "Батя", "город": "Москва"}
    payload = L._canonical(data)
    assert isinstance(payload, bytes)
    assert "Батя".encode("utf-8") in payload


def test_sign_logs_to_db():
    L.generate_keypair()
    L.sign({"test": "data"}, agent="unit_test")
    conn = sqlite3.connect(L.LEDGER_DB)
    row = conn.execute("SELECT agent, payload FROM ledger").fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "unit_test"
    assert "data" in row[1]


def test_sign_never_crashes_on_db_error(monkeypatch):
    """Если БД сломана — sign всё равно возвращает подпись."""
    L.generate_keypair()
    monkeypatch.setattr(L.sqlite3, "connect", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("boom")))
    sig = L.sign({"x": 1})
    assert len(sig) == 64


def test_public_key_b64_format():
    L.generate_keypair()
    b64 = L.public_key_b64()
    # Ed25519 pubkey — 32 байта → base64 = 44 символа (с '=')
    raw = base64.b64decode(b64)
    assert len(raw) == 32


def test_public_key_b64_stable():
    L.generate_keypair()
    assert L.public_key_b64() == L.public_key_b64()


def test_verify_with_explicit_pubkey():
    """Если передан явный pubkey — используется он."""
    L.generate_keypair()
    priv_path, pub_path = L.PRIV_PATH, L.PUB_PATH
    pub = L._load_pub()

    # Генерируем второй ключ
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    other_priv = Ed25519PrivateKey.generate()
    other_pub = other_priv.public_key()

    sig = L.sign({"x": 1})
    # Наш pubkey валиден
    assert L.verify({"x": 1}, sig, pubkey=pub) is True
    # Чужой pubkey — невалиден
    assert L.verify({"x": 1}, sig, pubkey=other_pub) is False


def test_multiple_signs_different_data():
    L.generate_keypair()
    sig1 = L.sign({"a": 1})
    sig2 = L.sign({"a": 2})
    assert sig1 != sig2
