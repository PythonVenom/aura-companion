"""Blender wrapper — 3D через TCP + bpy (ADR-037).

Blender 4.2+ имеет встроенный Python. Aura подключается через
`blender --background --python-expr` или TCP-сервер (порт 9876).
"""
from __future__ import annotations

import json
import socket
import subprocess
import shutil
from typing import Any

from aura.wrappers.base import AppWrapper, WrapperError


class BlenderWrapper(AppWrapper):
    """Обёртка над Blender 4.x.

    Безопасные команды:
      - "scene_info" — состав сцены
      - "list_objects" — объекты
      - "export_fbx" — экспорт
      - "render" — рендер в файл

    Опасные (требуют confirm):
      - "delete_all", "save_as"
    """

    name = "blender"
    version = "4.2+"
    transport = "tcp"
    DEFAULT_PORT = 9876

    SAFE = frozenset({
        "scene_info", "list_objects", "export_fbx", "export_obj",
        "render", "list_materials",
    })

    def __init__(self, port: int = DEFAULT_PORT) -> None:
        super().__init__()
        self.port = port
        self._sock: socket.socket | None = None
        self._safe_commands = self.SAFE

    def is_available(self) -> bool:
        return shutil.which("blender") is not None

    def connect(self) -> bool:
        if not self.is_available():
            raise WrapperError("Blender не установлен (нет в PATH)")
        try:
            self._sock = socket.create_connection(("127.0.0.1", self.port), timeout=3)
            self._connected = True
            return True
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            raise WrapperError(
                f"Blender TCP сервер не отвечает на порт {self.port}. "
                f"Запусти: blender --python scripts/aura_server.py"
            ) from e

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None
        self._connected = False

    def execute(self, cmd: str, params: dict[str, Any] | None = None) -> dict:
        if not self.is_safe(cmd):
            raise WrapperError(f"Команда {cmd!r} требует confirm (ADR-037)")
        if not self._connected:
            self.connect()
        try:
            payload = json.dumps({"cmd": cmd, "params": params or {}})
            self._sock.sendall(payload.encode("utf-8"))
            response = self._sock.recv(65536).decode("utf-8")
            return {"ok": True, "result": json.loads(response)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def run_headless(self, script: str) -> dict:
        """Fallback: blender --background --python-expr."""
        if not self.is_available():
            return {"ok": False, "error": "blender не найден"}
        try:
            r = subprocess.run(
                ["blender", "--background", "--python-expr", script],
                capture_output=True, text=True, timeout=120,
            )
            return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except Exception as e:
            return {"ok": False, "error": str(e)}


__all__ = ["BlenderWrapper"]
