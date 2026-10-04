"""Триггер morning_checklist в ProactiveEngine."""

from unittest.mock import MagicMock
from aura.agents import checklist as cl


def test_trigger_reads_checklist(tmp_path, monkeypatch):
    from aura.agents.proactive import morning_checklist_trigger
    from datetime import datetime as dt
    p = tmp_path / "CHECKLIST.md"
    p.write_text("# Чек-лист\n\n## 🔴 Критично\n- [ ] fix bug 12\n- [ ] написать пост\n",
                 encoding="utf-8")
    monkeypatch.setattr(cl, "CHECKLIST_PATH", p)

    t = morning_checklist_trigger(get_agent=None)
    state = {}
    # Время 9:00 — должно сработать
    import aura.agents.proactive as pr
    monkeypatch.setattr(pr, "_now_hour", lambda: 9)

    assert t.condition(state) is True
    result = t.action()
    assert "fix bug 12" in result


def test_trigger_before_8_no_fire(tmp_path, monkeypatch):
    from aura.agents.proactive import morning_checklist_trigger
    p = tmp_path / "CHECKLIST.md"
    p.write_text("- [ ] task\n", encoding="utf-8")
    monkeypatch.setattr(cl, "CHECKLIST_PATH", p)

    t = morning_checklist_trigger(get_agent=None)
    import aura.agents.proactive as pr
    monkeypatch.setattr(pr, "_now_hour", lambda: 6)

    assert t.condition({}) is False


def test_trigger_after_noon_no_fire(tmp_path, monkeypatch):
    from aura.agents.proactive import morning_checklist_trigger
    p = tmp_path / "CHECKLIST.md"
    p.write_text("- [ ] task\n", encoding="utf-8")
    monkeypatch.setattr(cl, "CHECKLIST_PATH", p)

    t = morning_checklist_trigger(get_agent=None)
    import aura.agents.proactive as pr
    monkeypatch.setattr(pr, "_now_hour", lambda: 14)

    assert t.condition({}) is False


def test_trigger_no_items(tmp_path, monkeypatch):
    from aura.agents.proactive import morning_checklist_trigger
    p = tmp_path / "CHECKLIST.md"
    p.write_text("", encoding="utf-8")
    monkeypatch.setattr(cl, "CHECKLIST_PATH", p)

    t = morning_checklist_trigger(get_agent=None)
    import aura.agents.proactive as pr
    monkeypatch.setattr(pr, "_now_hour", lambda: 9)

    assert t.condition({}) is False
