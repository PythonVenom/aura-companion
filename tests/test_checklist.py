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


# === AgentChecklist (BaseAgent) ===

def test_agent_can_handle_checklist(tmp_paths):
    from aura.agents.checklist import AgentChecklist
    from aura.core.protocol import AgentRequest
    a = AgentChecklist()
    assert a.can_handle(AgentRequest(text="аура чек-лист")) is True
    assert a.can_handle(AgentRequest(text="что осталось")) is True


def test_agent_cannot_handle_other():
    from aura.agents.checklist import AgentChecklist
    from aura.core.protocol import AgentRequest
    a = AgentChecklist()
    assert a.can_handle(AgentRequest(text="привет как дела")) is False


@pytest.mark.asyncio
async def test_agent_handle_summary(tmp_paths):
    from aura.agents.checklist import AgentChecklist
    from aura.core.protocol import AgentRequest, AgentStatus
    a = AgentChecklist()
    resp = await a.handle(AgentRequest(text="что в чек-листе"))
    assert resp.status == AgentStatus.OK
    assert "fix bug 12" in resp.text


@pytest.mark.asyncio
async def test_agent_handle_add(tmp_paths):
    from aura.agents.checklist import AgentChecklist
    from aura.core.protocol import AgentRequest, AgentStatus
    a = AgentChecklist()
    resp = await a.handle(AgentRequest(text="добавь в чек-лист: тест голосом"))
    assert resp.status == AgentStatus.OK
    assert "тест голосом" in tmp_paths.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_agent_handle_complete(tmp_paths):
    from aura.agents.checklist import AgentChecklist
    from aura.core.protocol import AgentRequest, AgentStatus
    a = AgentChecklist()
    resp = await a.handle(AgentRequest(text="выполнил fix bug 12"))
    assert resp.status == AgentStatus.OK
    assert "- [x] fix bug 12" in tmp_paths.read_text(encoding="utf-8")
