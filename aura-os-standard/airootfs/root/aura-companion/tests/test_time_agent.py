"""TimeAgent + Health + nlp."""
import time
from aura.agents import time_agent, health
from aura.nlp import fuzzy_match, _levenshtein


def test_add_timer(tmp_path, monkeypatch):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    t = time_agent.add_timer(60, "тест")
    assert t["type"] == "timer"


def test_add_alarm(tmp_path, monkeypatch):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    a = time_agent.add_alarm(7, 30, "утро")
    assert a["type"] == "alarm"


def test_list_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    time_agent.add_timer(60, "x")
    assert len(time_agent.list_pending()) == 1


def test_get_fired(tmp_path, monkeypatch):
    monkeypatch.setattr(time_agent, "TIMERS_PATH", tmp_path / "t.json")
    time_agent.add_timer(-1, "прошлое")
    assert len(time_agent.get_fired()) == 1


def test_add_reminder(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "HEALTH_PATH", tmp_path / "h.json")
    r = health.add_reminder("пить воду", 60)
    assert "text" in r


def test_check_due(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "HEALTH_PATH", tmp_path / "h.json")
    health.add_reminder("x", every_minutes=0)
    time.sleep(0.05)
    assert len(health.check_due()) >= 1


def test_lev_eq():
    assert _levenshtein("abc", "abc") == 0


def test_lev_one():
    assert _levenshtein("выключи", "выключит") == 1


def test_fuzzy_exact():
    assert fuzzy_match("выключи пк", ["выключи"]) is True


def test_fuzzy_near():
    assert fuzzy_match("выключит пк", ["выключи"], max_dist=2) is True


def test_fuzzy_far():
    assert fuzzy_match("привет мир", ["выключи"], max_dist=2) is False
