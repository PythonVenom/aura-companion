"""Blender + Figma wrappers + registry (ADR-037)."""
import pytest
from unittest.mock import patch, MagicMock

from aura.wrappers.base import WrapperError
from aura.wrappers.blender import BlenderWrapper
from aura.wrappers.figma import FigmaWrapper
from aura.wrappers.registry import WrapperRegistry


# --- Blender ---

def test_blender_is_appwrapper():
    b = BlenderWrapper()
    assert b.name == "blender"
    assert b.transport == "tcp"


def test_blender_whitelist():
    b = BlenderWrapper()
    assert b.is_safe("scene_info") is True
    assert b.is_safe("render") is True
    assert b.is_safe("delete_all") is False


def test_blender_unsafe_raises():
    b = BlenderWrapper()
    with pytest.raises(WrapperError):
        b.execute("delete_all")


def test_blender_not_available():
    with patch("shutil.which", return_value=None):
        b = BlenderWrapper()
        assert b.is_available() is False


# --- Figma ---

def test_figma_no_token():
    f = FigmaWrapper(token="")
    assert f.is_available() is False


def test_figma_with_token():
    f = FigmaWrapper(token="test_token")
    assert f.is_available() is True


def test_figma_whitelist():
    f = FigmaWrapper(token="x")
    assert f.is_safe("get_file") is True
    assert f.is_safe("delete_file") is False


def test_figma_get_file_needs_key():
    f = FigmaWrapper(token="x")
    result = f.execute("get_file", {})
    assert result["ok"] is False
    assert "key" in result["error"].lower()


# --- registry ---

def test_registry_has_all_three():
    reg = WrapperRegistry()
    names = reg.list_names()
    assert "grbl" in names
    assert "blender" in names
    assert "figma" in names


def test_registry_status_all():
    reg = WrapperRegistry()
    st = reg.status_all()
    assert len(st) >= 3
