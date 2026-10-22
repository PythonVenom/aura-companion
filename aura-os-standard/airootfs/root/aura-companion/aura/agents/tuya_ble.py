"""#29 Tuya BLE — управление Tuya-устройствами через Bluetooth Low Energy.

Наука:
- Bluetooth Low Energy (SIG 2010) — GATT-профиль, Service UUID
- Tuya Local Protocol — шифрование (AES-128-ECB), handshake
- bleak (Python BLE) — асинхронный API

Tuya BLE использует Service UUID: 0000fd50-0000-1000-8000-00805f9b34fb
Каждое устройство имеет UUID и auth_key (получается из Tuya Cloud).

Graceful degradation:
- Если bleak нет → mock-режим с fake-устройствами (для тестов)
- Если реальных Tuya нет → сообщение пользователю
"""
from __future__ import annotations

from dataclasses import dataclass

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

TUYA_SERVICE_UUID = "0000fd50-0000-1000-8000-00805f9b34fb"

# Mock-устройства для fallback (если bleak нет)
MOCK_DEVICES = [
    {"name": "Tuya-Lamp-Living", "address": "AA:BB:CC:11:22:33", "type": "light"},
    {"name": "Tuya-Plug-Kitchen", "address": "AA:BB:CC:44:55:66", "type": "plug"},
    {"name": "Tuya-Strip-Office", "address": "AA:BB:CC:77:88:99", "type": "strip"},
]


@dataclass
class TuyaDevice:
    name: str
    address: str
    type: str = "unknown"   # light | plug | strip | unknown

    def __str__(self) -> str:
        return f"{self.name} [{self.type}] @ {self.address}"


class AgentTuyaBLE(BaseAgent):
    """Агент управления Tuya BLE устройствами."""

    name = "tuya_ble"

    SCAN_KEYWORDS = ("найди tuya", "найди туя", "скан tuya", "туя устройства",
                     "tuya устройства", "умные устройства")
    ON_KEYWORDS = ("включи tuya", "включи туя", "включи умную лампу",
                   "включи умную розетку")
    OFF_KEYWORDS = ("выключи tuya", "выключи туя", "выключи умную лампу",
                    "выключи умную розетку")
    STATUS_KEYWORDS = ("статус tuya", "статус туя", "tuya статус")

    def __init__(self) -> None:
        super().__init__()
        self._has_bleak = self._check_bleak()

    @staticmethod
    def _check_bleak() -> bool:
        try:
            import bleak  # noqa: F401
            return True
        except ImportError:
            return False

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(
            kw in t
            for kw in (self.SCAN_KEYWORDS + self.ON_KEYWORDS
                       + self.OFF_KEYWORDS + self.STATUS_KEYWORDS)
        )

    async def handle(self, request: AgentRequest) -> AgentResponse:
        t = request.text.lower()
        if any(kw in t for kw in self.SCAN_KEYWORDS):
            return await self._scan()
        if any(kw in t for kw in self.ON_KEYWORDS):
            return await self._power(t, on=True)
        if any(kw in t for kw in self.OFF_KEYWORDS):
            return await self._power(t, on=False)
        return self._status()

    # ─── Сканирование ───
    async def _scan(self) -> AgentResponse:
        if not self._has_bleak:
            devices = [TuyaDevice(**d) for d in MOCK_DEVICES]
            return AgentResponse.ok(
                text=f"📡 Mock-режим (bleak не установлен). "
                     f"Найдено {len(devices)} fake-устройств:\n"
                     + "\n".join(f"  • {d}" for d in devices),
                agent_name=self.name,
            )

        try:
            from bleak import BleakScanner
            raw = await BleakScanner.discover(timeout=5.0)
            devices = []
            for d in raw:
                # В реальности — фильтр по Service UUID Tuya
                # Здесь упрощённо: ищем "Tuya" в имени
                name = d.name or ""
                if "tuya" in name.lower():
                    devices.append(TuyaDevice(
                        name=name,
                        address=d.address,
                        type="unknown",
                    ))
            if not devices:
                return AgentResponse.ok(
                    text="📡 Tuya-устройств не найдено (проверь питание и pairing).",
                    agent_name=self.name,
                )
            return AgentResponse.ok(
                text=f"📡 Найдено {len(devices)} Tuya-устройств:\n"
                     + "\n".join(f"  • {d}" for d in devices),
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"❌ Ошибка BLE сканирования: {e}",
                agent_name=self.name,
            )

    # ─── Управление ───
    async def _power(self, text: str, on: bool) -> AgentResponse:
        action = "включения" if on else "выключения"
        if not self._has_bleak:
            return AgentResponse.ok(
                text=f"📡 Mock-режим: команда {action} отправлена (fake).",
                agent_name=self.name,
            )
        return AgentResponse.ok(
            text=f"⚠️ Real BLE {action} не реализован в skeleton. "
                 f"Нужен handshake + auth_key.",
            agent_name=self.name,
        )

    # ─── Статус ───
    def _status(self) -> AgentResponse:
        mode = "REAL (bleak)" if self._has_bleak else "MOCK"
        devices = len(MOCK_DEVICES)
        return AgentResponse.ok(
            text=f"📡 Tuya BLE: режим={mode}, "
                 f"mock-устройств={devices}, "
                 f"Service UUID={TUYA_SERVICE_UUID}",
            agent_name=self.name,
        )


__all__ = ["MOCK_DEVICES", "TUYA_SERVICE_UUID", "AgentTuyaBLE", "TuyaDevice"]
