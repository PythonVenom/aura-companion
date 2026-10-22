"""#121 Fuzzing native messaging (Bug 121 — OOM защита).

Наука: OWASP A03:2021 (Injection), hypothesis (MacIver 2015).
Атака: поддельная length → OOM/hang.
Защита: MAX_MSG_SIZE = 10 МБ.
"""
from __future__ import annotations

import io
import json
import struct
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Добавляем scripts в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from aura_bridge_host import MAX_MSG_SIZE, read_msg, write_msg  # noqa


# === Константы ===

def test_max_msg_size_is_10mb():
    assert MAX_MSG_SIZE == 10 * 1024 * 1024


# === read_msg: корректные данные ===

def test_read_msg_valid():
    """Валидный JSON → dict."""
    payload = json.dumps({"cmd": "list_tabs"}).encode("utf-8")
    raw = struct.pack("<I", len(payload)) + payload
    stream = io.BytesIO(raw)
    result = read_msg(stream)
    assert result == {"cmd": "list_tabs"}


def test_read_msg_empty_stream():
    stream = io.BytesIO(b"")
    assert read_msg(stream) is None


def test_read_msg_partial_header():
    stream = io.BytesIO(b"\x01\x02")  # только 2 байта заголовка
    assert read_msg(stream) is None


# === Bug 121: атаки ===

def test_read_msg_oversized_length_rejected():
    """4 ГБ length → None (не OOM)."""
    raw = struct.pack("<I", 0xFFFFFFFF) + b"x" * 100
    stream = io.BytesIO(raw)
    assert read_msg(stream) is None


def test_read_msg_zero_length_rejected():
    """length=0 → None (защита)."""
    raw = struct.pack("<I", 0) + b"x" * 100
    stream = io.BytesIO(raw)
    assert read_msg(stream) is None


def test_read_msg_just_above_max_rejected():
    """MAX+1 → None."""
    raw = struct.pack("<I", MAX_MSG_SIZE + 1) + b"x"
    stream = io.BytesIO(raw)
    assert read_msg(stream) is None


def test_read_msg_exactly_max_accepted_if_valid_json():
    """MAX — граница (валидный JSON не влезет, но проверяем границу)."""
    # 10 МБ JSON — невозможно как dict. Проверяем что не отсекается
    # по границе. Подсовываем мусор — получим exception.
    body = b"x" * 100  # не JSON
    raw = struct.pack("<I", MAX_MSG_SIZE) + body
    stream = io.BytesIO(raw)
    with pytest.raises((json.JSONDecodeError, UnicodeDecodeError)):
        read_msg(stream)


# === Fuzzing: случайные 4 байта заголовка ===

@given(st.binary(min_size=4, max_size=4))
@settings(max_examples=200, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_fuzz_random_header_no_crash(header):
    """Случайный 4-байтный заголовок → не краш."""
    raw = header + b"body"
    stream = io.BytesIO(raw)
    try:
        result = read_msg(stream)
        # Либо None, либо dict, либо exception на json.loads
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, struct.error):
        pass  # ОК — пойман


@given(st.integers(min_value=0, max_value=0xFFFFFFFF))
@settings(max_examples=100)
def test_fuzz_length_values(length):
    """Случайная length → не OOM, только None или exception."""
    raw = struct.pack("<I", length) + b"\x00" * 10
    stream = io.BytesIO(raw)
    if length == 0 or length > MAX_MSG_SIZE:
        # Должно быть отклонено БЕЗ попытки чтения
        assert read_msg(stream) is None
    else:
        # length валиден, но body недостаточно → либо None, либо exception
        try:
            read_msg(stream)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass


@given(st.binary(min_size=0, max_size=100))
@settings(max_examples=200)
def test_fuzz_random_bytes_no_crash(data):
    """Случайные байты → не краш."""
    stream = io.BytesIO(data)
    try:
        read_msg(stream)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, struct.error):
        pass  # ОК


# === write_msg roundtrip ===

def test_write_read_roundtrip():
    """write_msg → read_msg → идентично."""
    original = {"cmd": "test", "value": 42, "ru": "привет"}
    buf = io.BytesIO()
    write_msg(buf, original)
    buf.seek(0)
    result = read_msg(buf)
    assert result == original


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.one_of(st.integers(), st.text(max_size=100), st.booleans()),
    max_size=10,
))
@settings(max_examples=50)
def test_fuzz_roundtrip(obj):
    """Случайный dict → write → read → идентично."""
    buf = io.BytesIO()
    write_msg(buf, obj)
    buf.seek(0)
    result = read_msg(buf)
    assert result == obj
