"""Тесты для aura/core/egress_broker.py (ADR-091)."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from aura.core.egress_broker import EgressBroker, BrokerPolicy


@pytest.fixture
def broker():
    return EgressBroker(policy=BrokerPolicy(allowed_endpoints=["api.deepseek.com"]))


def test_policy_default_deny():
    p = BrokerPolicy()
    assert p.allowed_endpoints == []
    assert p.allow("any.endpoint.com") is False


def test_policy_allow():
    p = BrokerPolicy(allowed_endpoints=["api.deepseek.com"])
    assert p.allow("api.deepseek.com") is True
    assert p.allow("evil.com") is False


def test_broker_filter_strips_private_fields(broker):
    payload = {
        "prompt": "async в Python",
        "user_name": "Вася",
        "user_email": "v@x.com",
        "device_state": {"cpu": 50},
    }
    clean = broker.filter_payload(payload)
    assert "prompt" in clean
    assert "user_name" not in clean
    assert "user_email" not in clean
    assert "device_state" not in clean


def test_broker_blocks_denied_endpoint(broker):
    with pytest.raises(PermissionError):
        broker.validate_endpoint("https://evil.com/api")


def test_broker_allows_endpoint(broker):
    broker.validate_endpoint("https://api.deepseek.com/v1/chat")


def test_broker_budget_zero():
    b = EgressBroker(policy=BrokerPolicy(daily_budget=0))
    assert b.check_budget(cost=0.01) is False


def test_broker_budget_ok():
    b = EgressBroker(policy=BrokerPolicy(daily_budget=10.0))
    assert b.check_budget(cost=0.05) is True


def test_broker_budget_accumulates():
    b = EgressBroker(policy=BrokerPolicy(daily_budget=1.0))
    b.record_spend(0.6)
    assert b.check_budget(cost=0.5) is False
    assert b.check_budget(cost=0.3) is True
