"""Linux: PipeWire + systemd + MPRIS."""
from __future__ import annotations

import contextlib
import subprocess


class LinuxAudio:
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
        with contextlib.suppress(Exception):
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@",
                            f"{int(level*100)}%"],
                           capture_output=True, timeout=2)

    def unduck(self) -> None:
        with contextlib.suppress(Exception):
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"],
                           capture_output=True, timeout=2)


class LinuxService:
    def enable_autostart(self) -> bool:
        try:
            subprocess.run(
                ["systemctl", "--user", "enable", "aura.service"],
                capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def disable_autostart(self) -> bool:
        try:
            subprocess.run(
                ["systemctl", "--user", "disable", "aura.service"],
                capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def notify(self, title: str, body: str) -> None:
        with contextlib.suppress(Exception):
            subprocess.run(["notify-send", title, body],
                           capture_output=True, timeout=2)


class LinuxMedia:
    def list_players(self) -> list[str]:
        try:
            r = subprocess.run(["playerctl", "-l"],
                               capture_output=True, text=True, timeout=2)
            return r.stdout.strip().splitlines()
        except Exception:
            return []

    def pause_all(self) -> bool:
        try:
            subprocess.run(["playerctl", "-a", "pause"],
                           capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def resume_all(self) -> bool:
        try:
            subprocess.run(["playerctl", "-a", "play"],
                           capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def get_last_active(self) -> str | None:
        from aura.agents import media_state
        return media_state.get_active()


__all__ = ["LinuxAudio", "LinuxMedia", "LinuxService"]
