"""CLI timer/reminder."""
import pytest
from argparse import Namespace

from aura import cli
from aura.agents import time_agent, health


def test_parse_duration_s():
    assert cli._parse_duration("30s") == 30


def test_parse_duration_m():
    assert cli._parse_duration("5m") == 300


def test_parse_duration_h():
    assert cli._parse_duration("2h") == 7200


def test_parse_duration_invalid():
    with pytest.raises(ValueError):
        cli._parse_duration("5x")
    with pytest.raises(ValueError):
        cli._parse_duration("abc")
    with pytest.raises(ValueError):
        cli._parse_duration("5")  # нет единицы


def test_cmd_timer(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    rc = cli.cmd_timer(Namespace(duration="5m", label="чай"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "чай" in out
    items = time_agent.list_pending()
    assert len(items) == 1
    assert items[0]["label"] == "чай"


def test_cmd_timer_invalid(capsys):
    rc = cli.cmd_timer(Namespace(duration="bad", label=""))
    assert rc == 1
    assert "❌" in capsys.readouterr().out


def test_cmd_reminder(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(health, "HEALTH_PATH", tmp_path / "h.json")
    rc = cli.cmd_reminder(Namespace(text="вода", every_minutes=60))
    assert rc == 0
    out = capsys.readouterr().out
    assert "вода" in out


def test_cmd_timers_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    rc = cli.cmd_timers(Namespace())
    assert rc == 0
    assert "нет" in capsys.readouterr().out.lower()


def test_cmd_timers_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    time_agent.add_timer(300, "чай")
    rc = cli.cmd_timers(Namespace())
    assert rc == 0
    assert "чай" in capsys.readouterr().out


def test_cmd_reminders_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(health, "HEALTH_PATH", tmp_path / "h.json")
    rc = cli.cmd_reminders(Namespace())
    assert rc == 0
    assert "нет" in capsys.readouterr().out.lower()
