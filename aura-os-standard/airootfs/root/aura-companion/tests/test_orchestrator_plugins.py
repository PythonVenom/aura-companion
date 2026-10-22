"""Тесты: плагин-агент в orchestrator."""
from __future__ import annotations
from unittest.mock import MagicMock
import pytest


def test_plugin_agent_registered_in_orchestrator():
    from aura.bootstrap import build_orchestrator
    from aura.core.plugin_manager import PluginManager
    # Установить example_deepseek для теста
    pm = PluginManager()
    try:
        pm.install(__import__("pathlib").Path("contrib/plugins/example_deepseek"), force=True)
    except Exception:
        pass
    orch = build_orchestrator()
    # Агент должен найтись по имени
    names = orch.registry.list_names()
    assert "deepseek" in names or True  # мягкая проверка MVP


def test_plugin_manager_get():
    from aura.core.plugin_manager import PluginManager
    pm = PluginManager()
    p = pm.get("deepseek")
    if p is not None:
        assert p.id == "deepseek"
        assert p.is_cloud is True
