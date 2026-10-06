"""GRBL wrapper — управление ЧПУ через serial (ADR-037).

GRBL — open-source прошивка для Arduino-ЧПУ (3M+ установок мир).
Транспорт: serial (USB), 115200 бод.
"""
from __future__ import annotations

import re
from typing import Any

from aura.wrappers.base import AppWrapper, WrapperError


class GRBLWrapper(AppWrapper):
    """Обёртка над GRBL 1.1 (ЧПУ).

    Безопасные команды (whitelist):
      ? — статус
      $$ — параметры
      $G — G-code mode
      $H — homing (safe)
      $X — clear alarm

    Опасные (требуют confirm):
      G-code движения (G0/G1)
      $J — jog
      $C — check mode
    """

    name = "grbl"
    version = "1.1+"
    transport = "serial"

    SAFE = frozenset({"?", "$$", "$G", "$H", "$X", "$I"})

    def __init__(self, port: str | None = None, baud: int = 115200) -> None:
        super().__init__()
        self.port = port
        self.baud = baud
        self._serial = None
        self._safe_commands = self.SAFE

    def is_available(self) -> bool:
        """Проверяем наличие pyserial + порт."""
        try:
            import serial  # noqa: F401
        except ImportError:
            return False
        if self.port:
            from pathlib import Path
            return Path(self.port).exists()
        # Автопоиск USB-serial
        return any(
            p.exists() for p in [
                "/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1",
            ]
        )

    def connect(self) -> bool:
        try:
            import serial
        except ImportError as e:
            raise WrapperError("pyserial не установлен: pip install pyserial") from e

        if not self.port:
            for candidate in ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1"]:
                from pathlib import Path
                if Path(candidate).exists():
                    self.port = candidate
                    break

        if not self.port:
            raise WrapperError("GRBL порт не найден")

        try:
            self._serial = serial.Serial(self.port, self.baud, timeout=1)
            self._connected = True
            return True
        except Exception as e:
            raise WrapperError(f"GRBL connect: {e}") from e

    def disconnect(self) -> None:
        if self._serial:
            try:
                self._serial.close()
            except Exception as e:
                # F-006: не глотать (раздел 17 промта)
                import logging
                logging.getLogger('aura.grbl').debug(
                    'grbl error: %s', e)
        self._serial = None
        self._connected = False

    def execute(self, cmd: str, params: dict[str, Any] | None = None) -> dict:
        if not self._connected and not self.connect():
            return {"ok": False, "error": "not connected"}

        if not self.is_safe(cmd):
            raise WrapperError(
                f"Команда {cmd!r} не в whitelist. Требует confirm (ADR-037)."
            )

        try:
            self._serial.write((cmd + "\n").encode("ascii"))
            response = self._serial.readline().decode("ascii", errors="ignore").strip()
            return {"ok": True, "result": response}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @staticmethod
    def parse_status(line: str) -> dict:
        """<Idle|MPos:0.000,0.000,0.000|FS:0,0> → dict."""
        if not line.startswith("<"):
            return {}
        m = re.match(r"<([^|]+)\|MPos:([^|]+)\|FS:([^>]+)>", line)
        if not m:
            return {"raw": line}
        state, mpos, fs = m.group(1), m.group(2), m.group(3)
        xyz = [float(x) for x in mpos.split(",")]
        feed, speed = fs.split(",")
        return {
            "state": state,
            "mpos": {"x": xyz[0], "y": xyz[1], "z": xyz[2]},
            "feed": float(feed),
            "speed": float(speed),
        }


__all__ = ["GRBLWrapper"]
