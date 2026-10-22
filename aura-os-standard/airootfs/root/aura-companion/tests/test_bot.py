"""Telegram bot skeleton (ADR-041)."""
from pathlib import Path

from aura.bot import telegram_bot as tb


def test_load_token_empty(monkeypatch, tmp_path):
    monkeypatch.delenv(tb.TOKEN_ENV, raising=False)
    monkeypatch.setattr(tb, "TOKEN_FILE", tmp_path / "nope")
    assert tb.load_token() == ""


def test_load_token_env(monkeypatch):
    monkeypatch.setenv(tb.TOKEN_ENV, "123:ABC")
    assert tb.load_token() == "123:ABC"


def test_load_token_file(monkeypatch, tmp_path):
    monkeypatch.delenv(tb.TOKEN_ENV, raising=False)
    f = tmp_path / "tok"
    f.write_text("999:XYZ")
    monkeypatch.setattr(tb, "TOKEN_FILE", f)
    assert tb.load_token() == "999:XYZ"


def test_admin_ids(monkeypatch):
    monkeypatch.setenv(tb.ADMIN_IDS_ENV, "1, 2 ,bad,3")
    assert tb.load_admin_ids() == {1, 2, 3}


def test_not_ready_without_token(monkeypatch):
    monkeypatch.delenv(tb.TOKEN_ENV, raising=False)
    monkeypatch.setattr(tb, "TOKEN_FILE", Path("/nope"))
    b = tb.AuraBot()
    assert b.is_ready() is False
