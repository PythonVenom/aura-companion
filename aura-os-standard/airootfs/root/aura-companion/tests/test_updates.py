"""
Тесты для AgentUpdates.

Все вызовы subprocess.run — замоканы.
Живой checkupdates НЕ запускается.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.updates import AgentUpdates
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def updates():
    return AgentUpdates()


def _mock_run(stdout_text):
    """Вернуть мок subprocess.run с заданным stdout."""
    mock = MagicMock()
    mock.return_value = MagicMock(stdout=stdout_text, returncode=0)
    return mock


# --- can_handle ---

def test_can_handle_check(updates):
    assert updates.can_handle(AgentRequest(text="проверь обновления"))


def test_can_handle_check_infinitive(updates):
    assert updates.can_handle(AgentRequest(text="проверить обновления"))


def test_can_handle_are_there(updates):
    assert updates.can_handle(AgentRequest(text="есть обновления"))


def test_can_handle_available(updates):
    assert updates.can_handle(AgentRequest(text="доступные обновления"))


def test_can_handle_system(updates):
    assert updates.can_handle(AgentRequest(text="обновления системы"))


def test_cannot_handle_time(updates):
    assert not updates.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(updates):
    assert not updates.can_handle(AgentRequest(text=""))


# --- handle: есть обновления ---

@pytest.mark.asyncio
async def test_handle_has_updates(updates):
    with patch("aura.agents.updates.subprocess.run", _mock_run("5\n")):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "updates"
    assert "5" in resp.text
    assert "Доступно" in resp.text


@pytest.mark.asyncio
async def test_handle_has_one_update(updates):
    with patch("aura.agents.updates.subprocess.run", _mock_run("1\n")):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert "1" in resp.text
    assert "Доступно" in resp.text


# --- handle: нет обновлений ---

@pytest.mark.asyncio
async def test_handle_no_updates(updates):
    with patch("aura.agents.updates.subprocess.run", _mock_run("0\n")):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert resp.status == AgentStatus.OK
    assert "обновлена" in resp.text.lower()


@pytest.mark.asyncio
async def test_handle_empty_stdout(updates):
    with patch("aura.agents.updates.subprocess.run", _mock_run("")):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert resp.status == AgentStatus.OK
    assert "обновлена" in resp.text.lower()


# --- handle: ошибка ---

@pytest.mark.asyncio
async def test_handle_error(updates):
    with patch(
        "aura.agents.updates.subprocess.run",
        side_effect=Exception("boom"),
    ):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert resp.status == AgentStatus.OK
    assert "Не удалось" in resp.text


@pytest.mark.asyncio
async def test_handle_bad_stdout(updates):
    """checkupdates может вернуть мусор — не должно падать."""
    with patch("aura.agents.updates.subprocess.run", _mock_run("abc\n")):
        resp = await updates.handle(AgentRequest(text="проверь обновления"))

    assert resp.status == AgentStatus.OK
    assert "Не удалось" in resp.text
