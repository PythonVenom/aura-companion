"""CLI и health."""
import json
from unittest.mock import patch
from aura import cli


def test_health_returns_json(capsys):
    with patch("aura.cli.subprocess.run") as mock:
        mock.return_value.stdout = "active\n"
        try:
            cli.cmd_health(None)
        except SystemExit:
            pass
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "status" in data
    assert "components" in data


def test_cli_check_exists():
    from aura.system_check import format_report
    assert callable(format_report)


def test_cli_calendar_empty(capsys, tmp_path, monkeypatch):
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    cli.cmd_calendar(None)
    out = capsys.readouterr().out
    assert "пуст" in out.lower() or out.strip() == ""


def test_health_fsm_idle(capsys, tmp_path, monkeypatch):
    from aura import cli
    monkeypatch.setattr("aura.cli.Path", type(Path("/tmp")) if False else __import__("pathlib").Path)
    with patch("aura.cli.subprocess.run") as mock:
        mock.return_value.stdout = "active\n"
        try:
            cli.cmd_health(None)
        except SystemExit:
            pass
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "fsm" in data["components"]
