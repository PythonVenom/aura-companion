"""Persistence: state сохраняется между перезапусками."""
import json
from pathlib import Path


def test_fsm_survives_restart(tmp_path, monkeypatch):
    from aura import dialog_fsm
    monkeypatch.setattr(dialog_fsm, "FSM_PATH", tmp_path / "fsm.json")
    dialog_fsm.set_state("awaiting_reply", chat="Аня", text="привет")
    data = json.loads((tmp_path / "fsm.json").read_text())
    assert data["state"] == "awaiting_reply"
    assert data["chat"] == "Аня"


def test_media_state_survives(tmp_path, monkeypatch):
    from aura.agents import media_state as ms
    monkeypatch.setattr(ms, "STATE_PATH", tmp_path / "media.json")
    ms.set_active("vk")
    assert ms.get_active() == "vk"


def test_calendar_persists_across_restart(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({
        "when": "2026-09-28T14:00", "chat": "Аня",
        "text": "массаж", "trigger": "массаж",
    })
    items = chat_sense.load_calendar()
    assert len(items) == 1
    assert items[0]["chat"] == "Аня"


def test_chat_sense_ttl_survives(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "STATE_PATH", tmp_path / "cs.json")
    items = [{"chat": "Аня", "preview": "привет", "reason": "unanswered"}]
    chat_sense.mark_reminded(items)
    state = json.loads((tmp_path / "cs.json").read_text())
    assert "Аня" in state.get("reminded", {})
