"""#133 AgentMQTT — тесты."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aura.agents import mqtt as M
from aura.agents.mqtt import AgentMQTT
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "CONFIG_PATH", tmp_path / "mqtt.json")
    return AgentMQTT()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


def test_config_defaults(agent):
    assert agent.config["broker"] == "localhost"
    assert agent.config["port"] == 1883


def test_config_from_file(tmp_path, monkeypatch):
    cfg = tmp_path / "mqtt.json"
    cfg.write_text(json.dumps({"broker": "10.0.0.1", "port": 8883}))
    monkeypatch.setattr(M, "CONFIG_PATH", cfg)
    a = AgentMQTT()
    assert a.config["broker"] == "10.0.0.1"
    assert a.config["port"] == 8883


@pytest.mark.parametrize("text", [
    "mqtt статус", "mqtt список", "включи mqtt", "умный дом mqtt",
])
def test_can_handle(agent, req, text):
    assert agent.can_handle(req(text))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет"))


def test_status_format(agent):
    out = agent._status()
    assert "localhost" in out
    assert "1883" in out


def test_publish_no_client(agent):
    """Без client → False, не краш."""
    assert agent.publish("test/topic", "payload") is False


def test_publish_with_client(agent):
    mock_client = MagicMock()
    agent.client = mock_client
    assert agent.publish("test/topic", "on") is True
    mock_client.publish.assert_called_once_with("test/topic", "on")


@pytest.mark.asyncio
async def test_handle_status(agent, req):
    resp = await agent.handle(req("mqtt статус"))
    assert "localhost" in resp.text


def test_paho_ok_flag():
    assert isinstance(M.PAHO_OK, bool)
