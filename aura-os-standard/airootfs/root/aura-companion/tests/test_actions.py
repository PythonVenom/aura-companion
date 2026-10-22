"""#147 AgentActions — тесты."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aura.agents.actions import AgentActions
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentActions()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


@pytest.mark.parametrize("text", [
    "найди файл", "отправь файл", "отправь по почте",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


@pytest.mark.parametrize("text,expected", [
    ("найди файл отчёт.pdf", "отчёт.pdf"),
    ("найди документ паспорт", "паспорт"),
    ("отправь файл test.txt по почте", "test.txt"),
])
def test_extract_name(agent, text, expected):
    assert agent._extract_file_name(text) == expected


def test_extract_name_empty(agent):
    assert agent._extract_file_name("привет") == ""


@pytest.mark.asyncio
async def test_handle_help(agent, req):
    resp = await agent.handle(req("отправь по почте"))
    assert "Команды" in resp.text or "отправь" in resp.text.lower()


def test_find_file_not_found(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    resp = agent._find_file("найди файл nonexistent_xyz123")
    assert "не найдено" in resp.text.lower()


def test_find_file_found(agent, tmp_path, monkeypatch):
    # Создаём файл в Загрузки
    dl = tmp_path / "Загрузки"
    dl.mkdir()
    (dl / "отчёт.pdf").write_bytes(b"x" * 100)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    resp = agent._find_file("найди файл отчёт")
    assert "отчёт.pdf" in resp.text


@pytest.mark.asyncio
async def test_send_file_not_found(agent, tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    resp = await agent._send_file("отправь файл nonexistent_xyz по почте")
    assert "не найден" in resp.text.lower()


@pytest.mark.asyncio
async def test_send_file_with_email(agent, tmp_path, monkeypatch):
    dl = tmp_path / "Загрузки"
    dl.mkdir()
    (dl / "test.txt").write_bytes(b"x" * 50)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))

    fake = type("R", (), {"text": "✅ Отправлено"})()
    with patch("aura.agents.email_agent.AgentEmail") as MockEmail:
        MockEmail.return_value._send.return_value = fake
        resp = await agent._send_file("отправь файл test.txt по почте")
    assert "test.txt" in resp.text
