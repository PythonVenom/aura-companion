"""#125 Smoke test — критичный минимум для CI.

Наука: Fowler 2012 — smoke тесты проверяют что система жива.
Если smoke падает — деплой отменяется.
"""
from __future__ import annotations

import pytest

from aura.agents.scenes import AgentScenes
from aura.core import fdir as F
from aura.core import ledger as L
from aura.core import notifications as N
from aura.core import rate_limit as RL
from aura.core.api_version import CURRENT_API
from aura.core.protocol import AgentRequest

pytestmark = pytest.mark.smoke


def test_version_set():
    assert CURRENT_API.major >= 1


def test_ledger_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(L, "KEY_DIR", tmp_path / "keys")
    monkeypatch.setattr(L, "PRIV_PATH", tmp_path / "keys/ed25519.key")
    monkeypatch.setattr(L, "PUB_PATH", tmp_path / "keys/ed25519.pub")
    monkeypatch.setattr(L, "LEDGER_DB", tmp_path / "l.db")
    L.generate_keypair()
    sig = L.sign({"user": "test"})
    assert L.verify({"user": "test"}, sig) is True


def test_notifications_levels():
    assert N.NotifLevel.P0 < N.NotifLevel.P3


def test_fdir_default():
    F.reset()
    assert F.get_mode() == F.Mode.NORMAL
    assert F.is_agent_allowed("sos") is True


def test_rate_limit_singleton():
    RL.reset_llm_bucket()
    assert RL.check_llm() is True


@pytest.mark.asyncio
async def test_scenes_can_handle():
    a = AgentScenes()
    assert a.can_handle(AgentRequest(text="я спать", user="test"))


def test_agent_response_ok():
    from aura.core.protocol import AgentResponse
    r = AgentResponse.ok(text="test", agent_name="smoke")
    assert r.text == "test"


def test_paths_importable():
    from aura import paths
    assert paths.CACHE_DIR is not None
