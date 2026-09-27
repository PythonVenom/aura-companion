"""AgentChecklist: голосовое управление чек-листом."""
import pytest
from pathlib import Path

from aura.agents import checklist


@pytest.fixture
def tmp_paths(tmp_path, monkeypatch):
    p = tmp_path / "CHECKLIST.md"
    p.write_text("# Чек-лист\n\n## 🔴 Критично\n- [ ] fix bug 12\n- [ ] позвонить Ивану\n\n## ✅ Сделано\n- [x] релиз\n", encoding="utf-8")
    monkeypatch.setattr(checklist, "CHECKLIST_PATH", p)
    return p


def test_read_today(tmp_paths):
    """Возвращает незакрытые пункты."""
    items = checklist.read_today()
    assert "fix bug 12" in items
    assert "позвонить Ивану" in items


def test_add_item(tmp_paths):
    """Добавляет пункт в конец."""
    checklist.add_item("записать видео для YouTube")
    text = tmp_paths.read_text(encoding="utf-8")
    assert "записать видео для YouTube" in text


def test_complete_item(tmp_paths):
    """Отмечает выполненным (по подстроке)."""
    ok = checklist.complete_item("bug 12")
    assert ok is True
    text = tmp_paths.read_text(encoding="utf-8")
    assert "- [x] fix bug 12" in text


def test_complete_not_found(tmp_paths):
    ok = checklist.complete_item("несуществующее")
    assert ok is False


def test_summary_format(tmp_paths):
    s = checklist.summary()
    assert "fix bug 12" in s
    assert "позвонить Ивану" in s


def test_summary_empty(tmp_path, monkeypatch):
    p = tmp_path / "empty.md"
    p.write_text("# Чек-лист\n\n## 🔴 Критично\n", encoding="utf-8")
    monkeypatch.setattr(checklist, "CHECKLIST_PATH", p)
    assert checklist.summary() == "" or "нет" in checklist.summary().lower()
