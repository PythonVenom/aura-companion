"""Config wizard (5 вопросов)."""
from unittest.mock import patch
from aura import config_wizard, settings


def _patch(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")


def test_wizard_sets_wake_word(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["Маруся", "1", "1", "1", "1"]):
        result = config_wizard.run()
    assert result["wake_word"] == "маруся"


def test_wizard_keeps_defaults_on_empty(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    # Пустые inputs → берутся defaults
    with patch("builtins.input", side_effect=["", "", "", "", ""]):
        result = config_wizard.run()
    assert result["persona"]["name"] == "Аура"
    assert result["persona"]["address"] == "ты"


def test_wizard_handles_invalid_choice(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    # Невалидные индексы → default
    with patch("builtins.input", side_effect=["Аура", "999", "abc", "999", "999"]):
        result = config_wizard.run()
    assert result["persona"]["address"] == "ты"


def test_wizard_persists(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["Света", "2", "3", "2", "2"]):
        config_wizard.run()
    s = settings.load()
    assert s["persona"]["name"] == "Света"
    assert s["persona"]["address"] == "вы"
