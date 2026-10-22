"""Recovery: state файлы сохраняются между рестартами."""
import json
import time
from pathlib import Path


def test_fsm_persisted(tmp_path, monkeypatch):
    from aura import dialog_fsm
    fsm_path = tmp_path / "fsm.json"
    monkeypatch.setattr(dialog_fsm, "FSM_PATH", fsm_path)

    dialog_fsm.set_state("awaiting_reply", chat="Аня", text="привет")
    assert fsm_path.exists()

    # Симуляция рестарта: читаем заново
    data = json.loads(fsm_path.read_text())
    assert data["state"] == "awaiting_reply"
    assert data["chat"] == "Аня"


def test_media_state_persisted(tmp_path, monkeypatch):
    from aura.agents import media_state as ms
    monkeypatch.setattr(ms, "STATE_PATH", tmp_path / "media.json")
    ms.set_active("vk", chat="Аня")
    # Читаем
    assert ms.get_active() == "vk"


def test_calendar_persisted(tmp_path, monkeypatch):
    from aura.agents import chat_sense
    monkeypatch.setattr(chat_sense, "CALENDAR_PATH", tmp_path / "cal.json")
    chat_sense.save_event({"when": "2026-09-28T14:00", "chat": "Аня",
                            "text": "массаж", "trigger": "массаж"})
    assert len(chat_sense.load_calendar()) == 1
