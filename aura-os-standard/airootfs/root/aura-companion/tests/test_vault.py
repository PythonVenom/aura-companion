"""
Тесты для AgentVault.

Работаем с временным файлом через monkeypatch.
"""

from __future__ import annotations

import pytest

from aura.agents.vault import AgentVault
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def vault(tmp_path, monkeypatch):
    test_file = tmp_path / "vault_test.json"
    monkeypatch.setattr(AgentVault, "FACTS_FILE", str(test_file))
    return AgentVault()


def test_init_empty(vault):
    assert vault.get_all_facts() == {}


def test_can_handle_remember(vault):
    assert vault.can_handle(AgentRequest(text="запомни мой цвет синий"))


def test_can_handle_facts(vault):
    assert vault.can_handle(AgentRequest(text="мои факты"))


def test_cannot_handle_time(vault):
    assert not vault.can_handle(AgentRequest(text="который час"))


@pytest.mark.asyncio
async def test_handle_remember(vault):
    resp = await vault.handle(AgentRequest(text="запомни цвет синий"))
    assert resp.status == AgentStatus.OK
    assert "Запомнила" in resp.text
    assert vault.get_fact("цвет") == "синий"


@pytest.mark.asyncio
async def test_handle_remember_no_value(vault):
    resp = await vault.handle(AgentRequest(text="запомни"))
    assert resp.status == AgentStatus.OK
    assert "Скажи" in resp.text


@pytest.mark.asyncio
async def test_handle_show_empty(vault):
    resp = await vault.handle(AgentRequest(text="мои факты"))
    assert resp.status == AgentStatus.OK
    assert "Фактов нет" in resp.text


@pytest.mark.asyncio
async def test_handle_show_facts(vault):
    vault.add_fact("цвет", "синий")
    vault.add_fact("город", "волгоград")
    resp = await vault.handle(AgentRequest(text="мои факты"))
    assert "цвет" in resp.text
    assert "синий" in resp.text
    assert "волгоград" in resp.text


@pytest.mark.asyncio
async def test_handle_not_handled(vault):
    resp = await vault.handle(AgentRequest(text="просто болтовня"))
    assert resp.status == AgentStatus.NOT_HANDLED


def test_persistence(tmp_path, monkeypatch):
    test_file = tmp_path / "vault2.json"
    monkeypatch.setattr(AgentVault, "FACTS_FILE", str(test_file))
    v1 = AgentVault()
    v1.add_fact("тест", "значение")
    v2 = AgentVault()
    assert v2.get_fact("тест") == "значение"
