"""Тесты интеграции плагинов в orchestrator."""
from __future__ import annotations
from unittest.mock import MagicMock
import pytest


def test_plugin_manager_lists():
    from aura.core.plugin_manager import PluginManager
    m = PluginManager()
    plugins = m.list_plugins()
    assert isinstance(plugins, list)


def test_orchestrator_loads_plugins_if_installed():
    # Smoke: если плагин установлен — orchestrator может загрузить
    from aura.core.plugin_manager import PluginManager
    m = PluginManager()
    installed = m.list_plugins()
    for p in installed:
        assert p.id
        assert p.name
