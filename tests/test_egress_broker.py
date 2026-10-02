"""Тесты EgressBroker (ADR-091)."""
from __future__ import annotations
import pytest
from aura.core.egress_broker import EgressBroker, BrokerPolicy


@pytest.fixture
def broker():
    return EgressBroker(policy=BrokerPolicy(allowed_endpoints=["api.deepseek.com"]))


def test_policy_default_deny():
    p = BrokerPolicy()
    assert p.allow("any.endpoint.com") is False


def test_policy_allow():
    p = BrokerPolicy(allowed_endpoints=["api.deepseek.com"])
    assert p.allow("api.deepseek.com") is True
    assert p.allow("evil.com") is False


def test_filter_strips_private(broker):
    clean = broker.filter_payload({
        "prompt": "async", "user_name": "V", "user_email": "v@x",
        "device_state": {"cpu": 50},
    })
    assert "prompt" in clean
    assert "user_name" not in clean
    assert "device_state" not in clean


def test_blocks_denied_endpoint(broker):
    with pytest.raises(PermissionError):
        broker.validate_endpoint("https://evil.com/api")


def test_allows_endpoint(broker):
    broker.validate_endpoint("https://api.deepseek.com/v1")


def test_budget_zero():
    b = EgressBroker(BrokerPolicy(daily_budget=0))
    assert b.check_budget(0.01) is False


def test_budget_ok():
    b = EgressBroker(BrokerPolicy(daily_budget=10.0))
    assert b.check_budget(0.05) is True


def test_budget_accumulates():
    b = EgressBroker(BrokerPolicy(daily_budget=1.0))
    b.record_spend(0.6)
    assert b.check_budget(0.5) is False
    assert b.check_budget(0.3) is True
