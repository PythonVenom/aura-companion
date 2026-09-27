"""Config wizard: тесты с mock input."""
from unittest.mock import patch
from aura import config_wizard, settings


def _patch_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")


def test_wizard_sets_wake_word(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["катя", "1.0", "80"]):
        result = config_wizard.run()
    assert result["wake_word"] == "катя"


def test_wizard_keeps_defaults_on_empty(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["", "", ""]):
        result = config_wizard.run()
    assert result["wake_word"] == "аура"
    assert result["tts_speed"] == 1.0
    assert result["volume"] == 100


def test_wizard_handles_invalid_float(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["аура", "not_a_number", "100"]):
        result = config_wizard.run()
    # Не упало, tts_speed остался default
    assert result["tts_speed"] == 1.0


def test_wizard_handles_invalid_int(tmp_path, monkeypatch):
    _patch_path(tmp_path, monkeypatch)
    with patch("builtins.input", side_effect=["аура", "1.0", "abc"]):
        result = config_wizard.run()
    assert result["volume"] == 100
