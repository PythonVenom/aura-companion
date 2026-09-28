"""Persona + config_wizard 5 вопросов."""
from unittest.mock import patch
from pathlib import Path

from aura import config_wizard, settings


def _patch(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")


def test_persona_defaults(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    s = settings.load()
    assert "persona" in s
    assert s["persona"]["name"] == "Аура"
    assert s["persona"]["address"] == "ты"


def test_wizard_sets_persona(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    # Имя, обращение(1=ты), характер(1=тёплая), юмор(1=да), голос(1=женский)
    with patch("builtins.input", side_effect=["Катя", "1", "1", "1", "1"]):
        result = config_wizard.run()
    assert result["persona"]["name"] == "Катя"
    assert result["wake_word"] == "катя"


def test_wizard_vy(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["Аура", "2", "2", "2", "2"]):
        result = config_wizard.run()
    assert result["persona"]["address"] == "вы"
    assert result["persona"]["style"] == "нейтральная"


def test_persona_persist(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    s = settings.load()
    s["persona"]["humor"] = False
    settings.save(s)
    s2 = settings.load()
    assert s2["persona"]["humor"] is False
