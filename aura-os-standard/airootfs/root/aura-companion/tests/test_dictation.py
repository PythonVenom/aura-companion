"""DictationAgent (ADR-044 шаг 5)."""
import pytest
from datetime import datetime
from pathlib import Path

from aura.agents import dictation as dmod
from aura.agents.dictation import AgentDictation
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent(tmp_path, monkeypatch):
    monkeypatch.setattr(dmod, "DICTATION_DIR", tmp_path / "dict")
    return AgentDictation()


def _req(text):
    return AgentRequest(text=text)


def _today_file(tmp_path):
    return tmp_path / "dict" / (datetime.now().strftime("%Y-%m-%d") + ".md")


# --- can_handle ---

def test_can_handle_diktovka(agent):
    assert agent.can_handle(_req("диктовка спина")) is True


def test_can_handle_stop(agent):
    assert agent.can_handle(_req("стоп диктовка")) is True


def test_can_handle_negative(agent):
    assert agent.can_handle(_req("погода")) is False


# --- start ---

@pytest.mark.asyncio
async def test_start_creates_file(agent, tmp_path):
    r = await agent.handle(_req("диктовка"))
    assert r.status == AgentStatus.OK
    assert "открыта" in r.text
    assert _today_file(tmp_path).exists()


# --- append ---

@pytest.mark.asyncio
async def test_append_line(agent, tmp_path):
    r = await agent.handle(_req("диктовка спина L4-L5 напряжение"))
    assert r.status == AgentStatus.OK
    assert "спина" in r.text
    f = _today_file(tmp_path)
    content = f.read_text(encoding="utf-8")
    assert "спина L4-L5" in content


@pytest.mark.asyncio
async def test_append_multiple(agent, tmp_path):
    await agent.handle(_req("диктовка первая"))
    await agent.handle(_req("диктовка вторая"))
    content = _today_file(tmp_path).read_text(encoding="utf-8")
    assert "первая" in content
    assert "вторая" in content
    assert agent._count == 2


# --- stop ---

@pytest.mark.asyncio
async def test_stop_returns_count(agent, tmp_path):
    await agent.handle(_req("диктовка раз"))
    await agent.handle(_req("диктовка два"))
    r = await agent.handle(_req("стоп диктовка"))
    assert "Строк: 2" in r.text
    assert agent._count == 0


@pytest.mark.asyncio
async def test_stop_without_start(agent):
    r = await agent.handle(_req("стоп диктовка"))
    assert "не была открыта" in r.text


# --- file path ---

@pytest.mark.asyncio
async def test_show_file_path(agent):
    r = await agent.handle(_req("диктовка файл"))
    assert r.status == AgentStatus.OK
    assert ".md" in r.text
