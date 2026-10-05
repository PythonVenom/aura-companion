"""T-os-1 — тесты Astra Parsec adapter."""
from pathlib import Path
from unittest.mock import patch

from aura.os_features import astra


def test_not_astra_returns_false():
    """На не-Astra системе адаптер не активен."""
    with patch.object(astra, "_is_astra", return_value=False):
        a = astra.ParsecAdapter()
        assert a.available() is False


def test_astra_without_parsec():
    """Astra без Parsec — адаптер не активен."""
    with patch.object(astra, "_is_astra", return_value=True), \
         patch.object(astra, "_has_parsec", return_value=False):
        a = astra.ParsecAdapter()
        assert a.available() is False


def test_astra_with_parsec():
    """Astra + Parsec — адаптер активен."""
    with patch.object(astra, "_is_astra", return_value=True), \
         patch.object(astra, "_has_parsec", return_value=True):
        a = astra.ParsecAdapter()
        assert a.available() is True


def test_set_label_when_unavailable(tmp_path):
    """Когда Parsec нет — set_label возвращает False (graceful)."""
    with patch.object(astra, "_is_astra", return_value=False):
        a = astra.ParsecAdapter()
        f = tmp_path / "meds.db"
        f.write_bytes(b"")
        assert a.set_label(f, level=2) is False


def test_set_label_invalid_level(tmp_path):
    with patch.object(astra, "_is_astra", return_value=True), \
         patch.object(astra, "_has_parsec", return_value=True):
        a = astra.ParsecAdapter()
        f = tmp_path / "x.db"
        f.write_bytes(b"")
        # level=99 нет в MAC_LEVELS
        assert a.set_label(f, level=99) is False


def test_set_label_file_missing(tmp_path):
    with patch.object(astra, "_is_astra", return_value=True), \
         patch.object(astra, "_has_parsec", return_value=True):
        a = astra.ParsecAdapter()
        assert a.set_label(tmp_path / "nope.db", level=2) is False


def test_elevate_and_declassify(tmp_path):
    """elevate_for = set_label(level=2); declassify = set_label(level=0)."""
    with patch.object(astra, "_is_astra", return_value=False):
        a = astra.ParsecAdapter()
        f = tmp_path / "meds.db"
        f.write_bytes(b"")
        assert a.elevate_for(f, level=2) is False
        assert a.declassify(f) is False


def test_status_structure():
    s = astra.ParsecAdapter().status()
    assert "is_astra" in s
    assert "has_parsec" in s
    assert "available" in s
    assert "levels" in s
    assert 0 in s["levels"]
    assert 4 in s["levels"]


def test_mac_levels_constants():
    assert astra.MAC_LEVELS[0] == "0"
    assert astra.MAC_LEVELS[2] == "2"
    assert astra.MAC_LEVELS[4] == "4"


def test_gost_adapter_unavailable():
    with patch.object(astra, "_is_astra", return_value=False):
        g = astra.GOSTAdapter()
        assert g.available() is False
        assert g.sign("x") is None
        assert g.verify("x", "y") is False


def test_parsec_via_framework(tmp_path):
    """Проверка через общий framework os_features."""
    from aura.core import os_features
    with patch.object(os_features, "current_os", return_value="astra"):
        adapter = os_features.get("astra.mac_parsec")
        assert adapter is not None
        assert hasattr(adapter, "set_label")
        assert hasattr(adapter, "get_label")
