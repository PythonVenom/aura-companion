"""Тесты модульной архитектуры (ADR-011)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aura.bootstrap import (
    is_module_enabled,
    load_modules_config,
    MODULES_CONFIG_PATH,
)
from aura.agents.time import AgentTime
from aura.agents.vk_music import AgentVKMusic


def test_base_agent_has_module_attrs():
    """BaseAgent имеет MODULE_* атрибуты."""
    from aura.core.protocol import BaseAgent
    assert hasattr(BaseAgent, "MODULE_NAME")
    assert hasattr(BaseAgent, "MODULE_DESCRIPTION")
    assert hasattr(BaseAgent, "MODULE_REQUIRES")
    assert hasattr(BaseAgent, "MODULE_ALWAYS")


def test_auto_module_name_from_name():
    """MODULE_NAME авто-заполняется из name."""
    assert AgentTime.MODULE_NAME == "time"
    assert AgentTime.name == "time"


def test_always_module_enabled_without_config(tmp_path, monkeypatch):
    """MODULE_ALWAYS включён всегда."""
    fake_config = tmp_path / "modules.toml"
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    assert is_module_enabled(AgentTime, {}) is True


def test_optional_module_default_no_config(tmp_path, monkeypatch):
    """Без конфига — все включены (обратная совместимость)."""
    fake_config = tmp_path / "modules.toml"
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    assert is_module_enabled(AgentVKMusic, {}) is True


def test_optional_module_enabled_with_config(tmp_path, monkeypatch):
    """С конфигом — модуль включён если True."""
    fake_config = tmp_path / "modules.toml"
    fake_config.write_text("[modules]\nvk_music = true\n")
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    assert is_module_enabled(AgentVKMusic, {"vk_music": True}) is True


def test_optional_module_disabled_with_config(tmp_path, monkeypatch):
    """С конфигом — модуль выключен если False."""
    fake_config = tmp_path / "modules.toml"
    fake_config.write_text("[modules]\nvk_music = false\n")
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    assert is_module_enabled(AgentVKMusic, {"vk_music": False}) is False


def test_load_config_missing(tmp_path, monkeypatch):
    """Нет файла → пустой dict."""
    fake_config = tmp_path / "modules.toml"
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    assert load_modules_config() == {}


def test_load_config_valid(tmp_path, monkeypatch):
    """Есть файл → читается."""
    fake_config = tmp_path / "modules.toml"
    fake_config.write_text("[modules]\nvk_music = true\nvision = false\n")
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_config)
    cfg = load_modules_config()
    assert cfg["vk_music"] is True
    assert cfg["vision"] is False
