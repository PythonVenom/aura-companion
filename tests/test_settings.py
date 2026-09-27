"""Settings: JSON конфиг."""
from pathlib import Path
from unittest.mock import patch

from aura import settings


def _patch_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")


def test_defaults_on_empty(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    s = settings.load()
    assert s["wake_word"] == "аура"
    assert s["language"] == "ru"


def test_set_and_get(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    settings.set_value("volume", 50)
    assert settings.get("volume") == 50


def test_missing_key_default(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    assert settings.get("nonexistent", "default") == "default"
