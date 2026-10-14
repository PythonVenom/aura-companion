"""#146 PluginRegistry — тесты."""
from __future__ import annotations

import pytest

from aura.core import plugin_registry as PR
from aura.core.plugin_registry import PluginMeta


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(PR, "REGISTRY_PATH", tmp_path / "registry.json")
    yield


def test_default_registry():
    plugins = PR.load()
    assert len(plugins) >= 2
    ids = [p.id for p in plugins]
    assert "vk_music" in ids


def test_register_new():
    m = PluginMeta(id="test", name="Test", version="1.0.0")
    PR.register(m)
    assert PR.find("test") is not None


def test_register_updates():
    PR.register(PluginMeta(id="x", name="A", version="1.0.0"))
    PR.register(PluginMeta(id="x", name="B", version="2.0.0"))
    found = PR.find("x")
    assert found.name == "B"
    assert found.version == "2.0.0"


def test_unregister_existing():
    PR.register(PluginMeta(id="x", name="X", version="1.0.0"))
    assert PR.unregister("x") is True
    assert PR.find("x") is None


def test_unregister_unknown():
    assert PR.unregister("nonexistent") is False


def test_search_by_name():
    PR.register(PluginMeta(id="calc", name="Калькулятор", version="1.0.0"))
    results = PR.search("кальк")
    assert len(results) >= 1


def test_search_by_tag():
    PR.register(PluginMeta(
        id="z", name="Z", version="1.0.0", tags=["special"],
    ))
    assert len(PR.search("special")) >= 1


def test_search_empty():
    assert PR.search("") == []


def test_by_tag():
    PR.register(PluginMeta(id="x", name="X", version="1", tags=["ru"]))
    PR.register(PluginMeta(id="y", name="Y", version="1", tags=["en"]))
    assert len(PR.by_tag("ru")) == 1


def test_format_registry():
    out = PR.format_registry()
    assert "Реестр" in out or "Плагинов" in out


def test_format_registry_with_query():
    PR.register(PluginMeta(id="vk", name="VK", version="1"))
    out = PR.format_registry("vk")
    assert "VK" in out


def test_save_load_roundtrip():
    PR.register(PluginMeta(id="r", name="R", version="1.0.0",
                          author="Test", tags=["a", "b"]))
    plugins = PR.load()
    p = next(p for p in plugins if p.id == "r")
    assert p.author == "Test"
    assert p.tags == ["a", "b"]
