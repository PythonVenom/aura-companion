"""Music — фоновый саундтрек корабля.

Один mpv-процесс в idle-режиме, IPC-сокет для смены треков.
Crossfade при переключении. Тишина — если aura_quiet_mode.

Наука: Hunicke 2004 (MDA — музыка как эстетика),
       Csikszentmihalyi 1990 (flow — фон не отвлекает).
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

SOCKET_PATH = "/tmp/aura_mpv.sock"

# Домашние треки. Если файла нет — пропускаем.
DEFAULT_TRACKS: dict[str, str] = {
    "idle": "~/.local/share/aura/music/idle.ogg",
    "combat": "~/.local/share/aura/music/combat.ogg",
    "triumph": "~/.local/share/aura/music/triumph.ogg",
    "night": "~/.local/share/aura/music/night.ogg",
}


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p))


class Music:
    """Singleton-обёртка над mpv. Один процесс на весь Аура."""

    _instance: Music | None = None

    def __init__(self, tracks: dict[str, str] | None = None):
        self.tracks = {k: str(_expand(v)) for k, v in (tracks or DEFAULT_TRACKS).items()}
        self.volume = 0.3
        self._proc: subprocess.Popen | None = None
        self._current: str | None = None

    @classmethod
    def instance(cls) -> Music:
        if cls._instance is None:
            cls._instance = Music()
        return cls._instance

    # ── процесс mpv ─────────────────────────────────────
    def _ensure_proc(self) -> bool:
        # Singleton через PID-файл: если mpv с нашим сокетом уже есть — не стартуем
        try:
            existing = subprocess.run(
                ["pgrep", "-f", f"mpv.*{SOCKET_PATH}"],
                capture_output=True, text=True, timeout=2,
            )
            if existing.stdout.strip() and Path(SOCKET_PATH).exists():
                return True
        except Exception:
            pass
        if self._proc and self._proc.poll() is None:
            return True
        if not shutil.which("mpv"):
            return False
        try:
            if Path(SOCKET_PATH).exists():
                Path(SOCKET_PATH).unlink()
            self._proc = subprocess.Popen(
                [
                    "mpv", "--idle=yes", "--no-video",
                    "--ao=pulse",  # обход залипания буфера PipeWire при restart
                    f"--input-ipc-server={SOCKET_PATH}",
                    f"--volume={int(self.volume * 100)}",
                    "--loop-file=inf",
                    "--really-quiet",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # ждём сокет
            for _ in range(20):
                if Path(SOCKET_PATH).exists():
                    return True
                time.sleep(0.05)
            return Path(SOCKET_PATH).exists()
        except Exception:
            return False

    def _send(self, cmd: list) -> bool:
        if not self._ensure_proc():
            return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(SOCKET_PATH)
                s.sendall((json.dumps({"command": cmd}) + "\n").encode())
            return True
        except Exception:
            return False

    # ── публичное API ────────────────────────────────────
    def play(self, track: str) -> bool:
        """Запустить трек. True, если mpv принял команду."""
        path = self.tracks.get(track)
        if not path or not Path(path).exists():
            return False
        if not self._ensure_proc():
            return False
        ok = self._send(["loadfile", path, "replace"])
        if ok:
            self._current = track
        return ok

    def stop(self) -> None:
        """Остановить музыку, но не убивать mpv."""
        self._send(["stop"])
        self._current = None

    def set_volume(self, volume: float) -> None:
        """0.0 – 1.0."""
        self.volume = max(0.0, min(1.0, volume))
        self._send(["set_property", "volume", int(self.volume * 100)])

    def current(self) -> str | None:
        return self._current

    def shutdown(self) -> None:
        """Закрыть mpv (для тестов / выхода)."""
        if self._proc and self._proc.poll() is None:
            self._send(["quit"])
            try:
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()
        self._proc = None
        self._current = None
        if Path(SOCKET_PATH).exists():
            with contextlib.suppress(Exception):
                Path(SOCKET_PATH).unlink()


# Триггер: какая музыка соответствует событию Ауры
EVENT_TO_TRACK: dict[str, str] = {
    "morning": "idle",
    "day": "idle",
    "evening": "idle",
    "night": "night",
    "hyperjump": "triumph",
    "fix_success": "triumph",
    "bug_found": "combat",
    "enemy_spotted": "combat",
}


def track_for_event(event: str) -> str | None:
    """Событие → трек или None (если музыки для него нет)."""
    return EVENT_TO_TRACK.get(event)
