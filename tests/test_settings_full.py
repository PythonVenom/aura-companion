"""Settings: расширенные тесты."""
from aura import settings


def _patch(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")


def test_defaults_complete(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    s = settings.load()
    for key in ("wake_word", "wake_word_aliases", "tts_voice",
                "tts_speed", "volume", "notifications",
                "proactive_enabled", "language"):
        assert key in s


def test_wake_word_aliases_list(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    s = settings.load()
    assert isinstance(s["wake_word_aliases"], list)
    assert "ара" in s["wake_word_aliases"]


def test_set_overwrites(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    settings.set_value("volume", 50)
    settings.set_value("volume", 80)
    assert settings.get("volume") == 80


def test_get_default_when_missing(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    assert settings.get("nonexistent", "fallback") == "fallback"


def test_save_load_roundtrip(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    s = settings.load()
    s["wake_word"] = "катя"
    settings.save(s)
    s2 = settings.load()
    assert s2["wake_word"] == "катя"


def test_partial_config_merges(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    settings.SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.SETTINGS_PATH.write_text('{"volume": 42}', encoding="utf-8")
    s = settings.load()
    assert s["volume"] == 42
    assert s["wake_word"] == "аура"  # из DEFAULTS
