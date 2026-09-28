"""Wrappers: base + GRBL + registry (ADR-037)."""
import pytest

from aura.wrappers.base import AppWrapper, WrapperError
from aura.wrappers.grbl import GRBLWrapper
from aura.wrappers.registry import WrapperRegistry, get_registry


# --- base ---

def test_appwrapper_is_abstract():
    with pytest.raises(TypeError):
        AppWrapper()


def test_grbl_is_appwrapper():
    assert issubclass(GRBLWrapper, AppWrapper)


def test_grbl_status():
    g = GRBLWrapper(port=None)
    st = g.status()
    assert st["name"] == "grbl"
    assert st["transport"] == "serial"
    assert st["connected"] is False


def test_grbl_safe_whitelist():
    g = GRBLWrapper()
    assert g.is_safe("?") is True
    assert g.is_safe("$$") is True
    assert g.is_safe("G0 X10") is False
    assert g.is_safe("$J=X10") is False


def test_grbl_unsafe_raises():
    g = GRBLWrapper()
    g._connected = True  # simulate
    with pytest.raises(WrapperError):
        g.execute("G0 X10")


# --- parse_status ---

def test_parse_status_idle():
    line = "<Idle|MPos:0.000,0.000,0.000|FS:0,0>"
    st = GRBLWrapper.parse_status(line)
    assert st["state"] == "Idle"
    assert st["mpos"]["x"] == 0.0


def test_parse_status_run():
    line = "<Run|MPos:10.500,-5.200,1.000|FS:1200,0>"
    st = GRBLWrapper.parse_status(line)
    assert st["state"] == "Run"
    assert st["feed"] == 1200.0


def test_parse_status_garbage():
    assert GRBLWrapper.parse_status("not a status") == {}


# --- registry ---

def test_registry_lists_grbl():
    reg = WrapperRegistry()
    assert "grbl" in reg.list_names()


def test_registry_get():
    reg = WrapperRegistry()
    g = reg.get("grbl")
    assert isinstance(g, GRBLWrapper)


def test_registry_unknown():
    reg = WrapperRegistry()
    with pytest.raises(WrapperError):
        reg.get("nonexistent")


def test_registry_singleton():
    assert get_registry() is get_registry()


def test_registry_status_all():
    reg = WrapperRegistry()
    st = reg.status_all()
    assert len(st) >= 1
    assert any(x.get("name") == "grbl" for x in st)
