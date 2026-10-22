"""Тесты DBus сервиса Aura (GAPS #38)."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import patch, MagicMock

import pytest


# ============================================================
# 1. Импорт и создание
# ============================================================
def test_dbus_service_imports():
    from aura.core.dbus_service import AuraDBusService, BUS_NAME, INTERFACE
    assert BUS_NAME == "org.aura.Companion"
    assert INTERFACE == "org.aura.Companion"


def test_dbus_service_creation():
    from aura.core.dbus_service import AuraDBusService
    s = AuraDBusService()
    assert s.orchestrator is None
    assert not s._running


def test_jeepney_available():
    """jeepney установлен."""
    from aura.core.dbus_service import JEEPNEY_OK
    assert JEEPNEY_OK


# ============================================================
# 2. Бизнес-логика (без DBus)
# ============================================================
def test_status():
    from aura.core.dbus_service import AuraDBusService
    s = AuraDBusService()
    st = s._status()
    assert "status" in st
    assert "ts" in st


def test_agents_no_orch():
    """Без orchestrator — ошибка, не краш."""
    from aura.core.dbus_service import AuraDBusService
    s = AuraDBusService()
    result = s._agents()
    assert "agents" in result
    assert isinstance(result["agents"], list)


def test_command_ping():
    """Command('health') → ответ."""
    from aura.core.dbus_service import AuraDBusService
    s = AuraDBusService()
    r = asyncio.run(s._command("health"))
    assert "ok" in r


# ============================================================
# 3. Chat через ChatBridge (mocked)
# ============================================================
def test_chat_empty():
    from aura.core.dbus_service import AuraDBusService
    s = AuraDBusService()
    r = asyncio.run(s._chat(""))
    assert "Пустое" in r or "пуст" in r.lower()


# ============================================================
# 4. systemd unit
# ============================================================
def test_systemd_unit_exists():
    from pathlib import Path
    unit = Path.home() / ".config" / "systemd" / "user" / "aura-dbus.service"
    assert unit.exists()
    text = unit.read_text()
    assert "aura.core.dbus_service" in text
    assert "DBUS_SESSION_BUS_ADDRESS" in text
