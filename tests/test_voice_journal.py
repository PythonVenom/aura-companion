"""Тесты VoiceJournal — дневник настроения."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from aura.agents.journal_mood import VoiceJournal, parse_mood


@pytest.fixture
def journal(tmp_path, monkeypatch):
    j = VoiceJournal(root=tmp_path)
    return j


def test_parse_mood_number():
    assert parse_mood("сегодня настроение 7") == 7
    assert parse_mood("настроение 10 из 10") == 10


def test_parse_mood_words_good():
    assert parse_mood("сегодня отлично") >= 7
    assert parse_mood("всё хорошо") >= 7


def test_parse_mood_words_bad():
    assert parse_mood("паршиво") <= 3
    assert parse_mood("плохо сегодня") <= 3


def test_parse_mood_unknown():
    assert parse_mood("просто работал") is None


def test_journal_add_entry(journal):
    journal.add("сегодня настроение 5", mood=5)
    entries = journal.read_all()
    assert len(entries) == 1
    assert entries[0]["mood"] == 5


def test_journal_week_stats(journal):
    journal.add("день 1", mood=3)
    journal.add("день 2", mood=7)
    journal.add("день 3", mood=5)
    stats = journal.stats_last_days(7)
    assert stats["count"] == 3
    assert stats["avg"] == 5.0


def test_journal_can_handle():
    from aura.core.protocol import AgentRequest
    j = VoiceJournal()
    assert j.can_handle(AgentRequest(text="занеси в дневник: сегодня 7"))
    assert j.can_handle(AgentRequest(text="как я себя чувствовал на неделе"))
    assert not j.can_handle(AgentRequest(text="который час"))


def test_journal_stats_empty(journal):
    stats = journal.stats_last_days(7)
    assert stats["count"] == 0
    assert stats["avg"] is None
