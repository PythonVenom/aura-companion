"""CLI profile."""
from argparse import Namespace
from aura import cli, settings


def test_profile_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")
    rc = cli.cmd_profile(Namespace(action="list", name=None))
    assert rc == 0
    out = capsys.readouterr().out
    assert "default" in out
    assert "medical" in out


def test_profile_set(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")
    rc = cli.cmd_profile(Namespace(action="set", name="medical"))
    assert rc == 0
    assert settings.get("voice_profile") == "medical"


def test_profile_set_invalid(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")
    rc = cli.cmd_profile(Namespace(action="set", name="xxx"))
    assert rc == 1


def test_profile_show(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "s.json")
    settings.set_value("voice_profile", "craft")
    rc = cli.cmd_profile(Namespace(action="show", name=None))
    assert rc == 0
    assert "craft" in capsys.readouterr().out
