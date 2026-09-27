"""Ubuntu/Debian: PipeWire или PulseAudio + systemd + MPRIS.

Fallback: если PipeWire нет — используем PulseAudio.
"""
from __future__ import annotations

import shutil
import subprocess


class UbuntuAudio:
    """PipeWire ИЛИ PulseAudio."""

    def _has_pipewire(self) -> bool:
        return shutil.which("pactl") is not None

    def list_sinks(self) -> list[str]:
        try:
            r = subprocess.run(["pactl", "list", "short", "sinks"],
                               capture_output=True, text=True, timeout=2)
            return [line.split("\t")[1] for line in r.stdout.splitlines()
                    if "\t" in line]
        except Exception:
            return []

    def list_sources(self) -> list[str]:
        try:
            r = subprocess.run(["pactl", "list", "short", "sources"],
                               capture_output=True, text=True, timeout=2)
            return [line.split("\t")[1] for line in r.stdout.splitlines()
                    if "\t" in line]
        except Exception:
            return []

    def get_default_sink(self) -> str:
        try:
            r = subprocess.run(["pactl", "info"],
                               capture_output=True, text=True, timeout=2)
            for line in r.stdout.splitlines():
                if line.startswith("Default Sink:"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return ""

    def set_default_sink(self, name: str) -> bool:
        try:
            r = subprocess.run(["pactl", "set-default-sink", name],
                               capture_output=True, timeout=2)
            return r.returncode == 0
        except Exception:
            return False

    def duck(self, level: float = 0.2) -> None:
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@",
                            f"{int(level*100)}%"],
                           capture_output=True, timeout=2)
        except Exception:
            pass

    def unduck(self) -> None:
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"],
                           capture_output=True, timeout=2)
        except Exception:
            pass


# Linux реализация совместима — наследуем
from aura.platform.linux import LinuxService, LinuxMedia  # noqa: E402


class UbuntuService(LinuxService):
    pass


class UbuntuMedia(LinuxMedia):
    pass


__all__ = ["UbuntuAudio", "UbuntuService", "UbuntuMedia"]
