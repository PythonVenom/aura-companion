"""Тесты для aura/web/api.py — HTTP API Aura (ADR-079)."""
from __future__ import annotations
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from aura.web.api import create_app
    orch = MagicMock()
    orch.process = MagicMock(return_value="тестовый ответ")
    app = create_app(orchestrator=orch, bridge=None)
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_status_returns_json(client):
    r = client.get("/status")
    assert r.status_code == 200
    data = r.json()
    assert "state" in data
    assert "version" in data


def test_chat_post(client):
    r = client.post("/chat", json={"user": "который час"})
    assert r.status_code == 200
    data = r.json()
    assert "aura" in data
    assert data["user"] == "который час"


def test_chat_empty_rejected(client):
    r = client.post("/chat", json={"user": ""})
    assert r.status_code == 400


def test_chat_history_get(client):
    r = client.get("/chat/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_agents_list(client):
    r = client.get("/agents")
    assert r.status_code == 200
    data = r.json()
    assert "agents" in data


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert "version" in r.json()
