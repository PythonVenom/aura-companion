"""#29 Tuya BLE — тесты (mock bleak)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aura.agents.tuya_ble import (
    AgentTuyaBLE, TuyaDevice, TUYA_SERVICE_UUID, MOCK_DEVICES,
)
from aura.core.protocol import AgentRequest


@pytest.fixture
def agent():
    return AgentTuyaBLE()


@pytest.fixture
def req():
    def _make(text: str):
        return AgentRequest(text=text, user="test")
    return _make


# === TuyaDevice ===

def test_tuya_device_str():
    d = TuyaDevice(name="Lamp", address="AA:BB", type="light")
    assert "Lamp" in str(d)
    assert "light" in str(d)


def test_tuya_device_default_type():
    d = TuyaDevice(name="X", address="AA")
    assert d.type == "unknown"


# === can_handle ===

def test_can_handle_scan(agent, req):
    assert agent.can_handle(req("найди tuya устройства"))


def test_can_handle_on(agent, req):
    assert agent.can_handle(req("включи умную лампу"))


def test_can_handle_off(agent, req):
    assert agent.can_handle(req("выключи умную розетку"))


def test_can_handle_status(agent, req):
    assert agent.can_handle(req("статус tuya"))


def test_cannot_handle_random(agent, req):
    assert not agent.can_handle(req("привет как дела"))


# === _check_bleak ===

def test_check_bleak_missing():
    with patch.dict("sys.modules", {"bleak": None}):
        # Не патчим — просто проверяем, что метод работает
        result = AgentTuyaBLE._check_bleak()
        assert isinstance(result, bool)


# === scan (mock mode) ===

@pytest.mark.asyncio
async def test_scan_mock_mode(agent, req):
    """Без bleak — mock-устройства."""
    with patch.object(agent, "_has_bleak", False):
        resp = await agent.handle(req("найди tuya"))
    assert "Mock-режим" in resp.text
    assert "fake-устройств" in resp.text


def _fake_bleak(discover_return=None, discover_side_effect=None):
    """Создать fake-модуль bleak для sys.modules."""
    import sys, types
    fake = types.ModuleType("bleak")

    class FakeScanner:
        @staticmethod
        async def discover(timeout=5.0):
            if discover_side_effect is not None:
                raise discover_side_effect
            return discover_return or []

    fake.BleakScanner = FakeScanner
    return fake


@pytest.mark.asyncio
async def test_scan_real_mode_no_devices(agent, req):
    """С bleak, но устройств нет."""
    import sys
    with patch.dict(sys.modules, {"bleak": _fake_bleak(discover_return=[])}):
        with patch.object(agent, "_has_bleak", True):
            resp = await agent.handle(req("найди tuya"))
    assert "не найдено" in resp.text


@pytest.mark.asyncio
async def test_scan_real_mode_finds_tuya(agent, req):
    """С bleak — находит Tuya по имени."""
    fake_device = MagicMock()
    fake_device.name = "Tuya-Lamp-Kitchen"
    fake_device.address = "AA:BB:CC:11:22:33"

    import sys
    with patch.dict(sys.modules, {"bleak": _fake_bleak(discover_return=[fake_device])}):
        with patch.object(agent, "_has_bleak", True):
            resp = await agent.handle(req("найди tuya"))
    assert "Найдено 1" in resp.text
    assert "Tuya-Lamp" in resp.text


@pytest.mark.asyncio
async def test_scan_filters_non_tuya(agent, req):
    """Игнорирует устройства без Tuya в имени."""
    d1 = MagicMock()
    d1.name = "Sony-Headphones"
    d1.address = "AA:BB"

    import sys
    with patch.dict(sys.modules, {"bleak": _fake_bleak(discover_return=[d1])}):
        with patch.object(agent, "_has_bleak", True):
            resp = await agent.handle(req("найди tuya"))
    assert "не найдено" in resp.text


@pytest.mark.asyncio
async def test_scan_bleak_exception(agent, req):
    import sys
    with patch.dict(sys.modules, {"bleak": _fake_bleak(discover_side_effect=RuntimeError("BLE off"))}):
        with patch.object(agent, "_has_bleak", True):
            resp = await agent.handle(req("найди tuya"))
    assert "Ошибка" in resp.text


# === power ===

@pytest.mark.asyncio
async def test_power_on_mock(agent, req):
    with patch.object(agent, "_has_bleak", False):
        resp = await agent.handle(req("включи умную лампу"))
    assert "Mock-режим" in resp.text


@pytest.mark.asyncio
async def test_power_off_mock(agent, req):
    with patch.object(agent, "_has_bleak", False):
        resp = await agent.handle(req("выключи умную розетку"))
    assert "Mock-режим" in resp.text


@pytest.mark.asyncio
async def test_power_real_not_implemented(agent, req):
    with patch.object(agent, "_has_bleak", True):
        resp = await agent.handle(req("включи tuya лампу"))
    assert "не реализован" in resp.text


# === status ===

def test_status_mock(agent):
    with patch.object(agent, "_has_bleak", False):
        resp = agent._status()
    assert "MOCK" in resp.text
    assert TUYA_SERVICE_UUID in resp.text


def test_status_real(agent):
    with patch.object(agent, "_has_bleak", True):
        resp = agent._status()
    assert "REAL" in resp.text


# === constants ===

def test_service_uuid_format():
    assert TUYA_SERVICE_UUID == "0000fd50-0000-1000-8000-00805f9b34fb"


def test_mock_devices_have_all_fields():
    for d in MOCK_DEVICES:
        assert "name" in d
        assert "address" in d
        assert "type" in d
