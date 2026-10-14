"""#150 FDIR — тесты."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from aura.core import fdir as F


@pytest.fixture(autouse=True)
def reset():
    F.reset()
    yield
    F.reset()


def test_default_mode():
    assert F.get_mode() == F.Mode.NORMAL


def test_set_mode():
    prev = F.set_mode(F.Mode.SAFE, "test")
    assert prev == F.Mode.NORMAL
    assert F.get_mode() == F.Mode.SAFE
    assert F.get_reason() == "test"


def test_critical_agents_always_allowed():
    F.set_mode(F.Mode.EMERGENCY)
    for agent in ("sos", "meds", "fall", "call"):
        assert F.is_agent_allowed(agent) is True


def test_non_critical_blocked_in_safe():
    F.set_mode(F.Mode.SAFE)
    assert F.is_agent_allowed("weather") is False
    assert F.is_agent_allowed("vk_music") is False


def test_all_allowed_in_normal():
    F.set_mode(F.Mode.NORMAL)
    for agent in ("sos", "weather", "vk_music"):
        assert F.is_agent_allowed(agent) is True


def test_degraded_allows_all():
    F.set_mode(F.Mode.DEGRADED)
    assert F.is_agent_allowed("weather") is True


def test_emergency_only_critical():
    F.set_mode(F.Mode.EMERGENCY)
    assert F.is_agent_allowed("weather") is False
    assert F.is_agent_allowed("sos") is True


def test_ram_percent_positive():
    pct = F._ram_percent()
    assert 0 <= pct <= 100


def test_check_health_normal():
    with patch("aura.core.fdir._ram_percent", return_value=50):
        m = F.check_health()
    assert m == F.Mode.NORMAL


def test_check_health_degraded():
    with patch("aura.core.fdir._ram_percent", return_value=90):
        m = F.check_health()
    assert m == F.Mode.DEGRADED


def test_check_health_safe():
    with patch("aura.core.fdir._ram_percent", return_value=97):
        m = F.check_health()
    assert m == F.Mode.SAFE


def test_format_status():
    out = F.format_status()
    assert "FDIR" in out
    assert "NORMAL" in out


def test_critical_agents_frozen():
    assert isinstance(F.CRITICAL_AGENTS, frozenset)
    assert "sos" in F.CRITICAL_AGENTS
