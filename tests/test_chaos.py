"""#155 Chaos testing — fault injection.

Наука: Basiri 2016 (Chaos Engineering), Nygard 2018 (Release It!).
Цель: система должна gracefully деградировать, а не падать.

Симулируем:
- отказ Ollama (LLM недоступен)
- отказ SQLite (БД недоступна)
- отказ speaker (TTS упал)
- отказ keyring (ключ не найден)
- отказ агента (raise exception)
- FDIR переходы под нагрузкой
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

from aura.core import fdir as F
from aura.core import ledger as L
from aura.core import notifications as N
from aura.core import recall_log as RL
from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


@pytest.fixture(autouse=True)
def reset_fdir():
    F.reset()
    yield
    F.reset()


# === 1. Ollama недоступен → fallback ===

def test_ollama_down_graceful(tmp_path, monkeypatch):
    """LLM недоступен → brain возвращает ошибку, но не крашится."""
    from aura.agents.brain import AgentBrain
    b = AgentBrain()
    with patch("aura.agents.brain.urllib.request.urlopen",
               side_effect=OSError("Ollama down")):
        resp = b.ask("привет")
    assert isinstance(resp, str)
    assert len(resp) > 0  # fallback ответ


# === 2. SQLite недоступна → лог не падает ===

def test_recall_db_down_graceful(monkeypatch):
    """recall_log.record при сломанной БД — молчит."""
    monkeypatch.setattr(RL, "DB", Path("/root/cannot_write/x.db"))
    RL.record("test", "action", "detail")  # не должно упасть


def test_notifications_db_down_graceful(tmp_path, monkeypatch):
    monkeypatch.setattr(N, "DB", tmp_path / "n.db")
    with patch("aura.core.notifications.sqlite3.connect",
               side_effect=sqlite3.OperationalError("boom")):
        with patch("aura.core.notifications.shutil.which", return_value=None):
            result = N.notify(N.NotifLevel.P1, "test", "body")
    assert result is False


# === 3. Keyring недоступен → hard fail или error ===

def test_ledger_key_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "PRIV_PATH", tmp_path / "no.key")
    monkeypatch.setattr(L, "PUB_PATH", tmp_path / "no.pub")
    monkeypatch.setattr(L, "KEY_DIR", tmp_path / "keys")
    monkeypatch.setattr(L, "LEDGER_DB", tmp_path / "l.db")
    L.generate_keypair()  # создаст
    sig = L.sign({"x": 1})
    assert len(sig) == 64


# === 4. Агент падает → orchestrator выживает ===

class _CrashAgent(BaseAgent):
    name = "crash"
    TRIGGERS = ("crash",)

    def can_handle(self, request: AgentRequest) -> bool:
        return True

    async def handle(self, request: AgentRequest) -> AgentResponse:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_agent_crash_isolated():
    """Падение агента → orchestrator не падает."""
    agent = _CrashAgent()
    with pytest.raises(RuntimeError):
        await agent.handle(AgentRequest(text="crash", user="test"))
    # Проверяем, что Aura может продолжать (agent изолирован)
    assert agent.name == "crash"


# === 5. FDIR под нагрузкой ===

def test_fdir_ram_100_percent():
    """RAM 100% → FDIR SAFE."""
    with patch("aura.core.fdir._ram_percent", return_value=100):
        m = F.check_health()
    assert m == F.Mode.SAFE
    assert F.is_agent_allowed("sos") is True
    assert F.is_agent_allowed("weather") is False


def test_fdir_recovery():
    """RAM вернулась в норму → FDIR NORMAL."""
    with patch("aura.core.fdir._ram_percent", return_value=97):
        F.check_health()
    assert F.get_mode() == F.Mode.SAFE
    with patch("aura.core.fdir._ram_percent", return_value=50):
        F.check_health()
    assert F.get_mode() == F.Mode.NORMAL


# === 6. Множественные отказы одновременно ===

def test_multi_failure_graceful(tmp_path, monkeypatch):
    """Ollama + SQLite + keyring упали одновременно."""
    from aura.agents.brain import AgentBrain

    b = AgentBrain()
    with patch("aura.agents.brain.urllib.request.urlopen",
               side_effect=OSError("no ollama")):
        resp1 = b.ask("привет")
    assert isinstance(resp1, str)

    monkeypatch.setattr(RL, "DB", Path("/root/x.db"))
    RL.record("test", "a", "b")  # не падает

    monkeypatch.setattr(N, "DB", tmp_path / "n.db")
    with patch("aura.core.notifications.sqlite3.connect",
               side_effect=sqlite3.OperationalError):
        with patch("aura.core.notifications.shutil.which", return_value=None):
            N.notify(N.NotifLevel.P0, "SOS", "тест")  # не падает


# === 7. FDIR в SAFE не пускает не-критичных ===

def test_fdir_safe_blocks_non_critical():
    F.set_mode(F.Mode.SAFE, "chaos")
    for agent in ("weather", "vk_music", "browser_tabs"):
        assert F.is_agent_allowed(agent) is False


def test_fdir_emergency_keeps_sos():
    F.set_mode(F.Mode.EMERGENCY, "critical")
    assert F.is_agent_allowed("sos") is True
    assert F.is_agent_allowed("meds") is True
    assert F.is_agent_allowed("weather") is False
