"""AgentOBDScanner — OBD-II через ELM327 (F-060)."""
from __future__ import annotations
import logging
log = logging.getLogger("aura.obd")

DTC_HINTS = {
    "P0300": "Random misfire",
    "P0301": "Cylinder 1 misfire — пропуск цилиндра 1",
    "P0302": "Cylinder 2 misfire",
    "P0171": "System too lean",
    "P0420": "Catalyst efficiency low",
}

class AgentOBDScanner:
    name = "obd_scanner"
    MODULE_ALWAYS = False
    CAPABILITIES = {"obd:read", "obd:clear", "obd:decode", "obd:vin"}
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
    def decode(self, code):
        return DTC_HINTS.get(code.upper(), f"{code} — расшифровка не найдена")
    def scan(self):
        return "ELM327 не подключён. Вставь адаптер в USB."
    def clear(self):
        return "ELM327 не подключён."
    def vin(self):
        return "ELM327 не подключён."
