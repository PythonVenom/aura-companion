"""Тесты для aura/web/ui — HTML UI (ADR-080)."""
from __future__ import annotations
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    from aura.web.api import create_app
    orch = MagicMock()
    orch.process = MagicMock(return_value="ok")
    return TestClient(create_app(orchestrator=orch))


def test_ui_root_returns_html(client):
    r = client.get("/ui")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_ui_contains_title(client):
    r = client.get("/ui")
    assert "Aura" in r.text


def test_ui_contains_chat_input(client):
    r = client.get("/ui")
    assert "<input" in r.text or "<textarea" in r.text


def test_ui_contains_fetch_chat(client):
    r = client.get("/ui")
    assert "/chat" in r.text


def test_ui_offline_no_cdn(client):
    r = client.get("/ui")
    assert "unpkg.com" not in r.text
    assert "cdn." not in r.text
