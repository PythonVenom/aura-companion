"""Linux HAL — реализация BasePlatform.

Наука:
- XDG Base Directory Specification (freedesktop.org 2021)
- POSIX (IEEE 1003.1)
- D-Bus (freedesktop) для уведомлений
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from aura.platform_adapters.base import BasePlatform


class LinuxPlatform(BasePlatform):
    name = "linux"

    # --- XDG paths ---
    def config_dir(self) -> Path:
        base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
        return Path(base) / "aura"

    def data_dir(self) -> Path:
        base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share"
        return Path(base) / "aura"

    def cache_dir(self) -> Path:
        base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
        return Path(base) / "aura"

    # --- Audio ---
    def _audio_players(self) -> list[list[str]]:
        # PipeWire → PulseAudio → ALSA
        return [
            ["pw-play"], ["paplay"], ["aplay"],
            ["mpv", "--no-video", "--really-quiet"],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
        ]

    def audio_play(self, path: Path) -> None:
        for cmd in self._audio_players():
            if shutil.which(cmd[0]):
                subprocess.run([*cmd, str(path)], check=False, timeout=60)
                return

    def audio_record(self, seconds: int, out: Path) -> bool:
        if shutil.which("arecord"):
            try:
                subprocess.run(
                    ["arecord", "-q", "-f", "S16_LE", "-r", "16000",
                     "-c", "1", "-d", str(seconds), str(out)],
                    timeout=seconds + 5, check=True,
                )
                return True
            except Exception:
                pass
        if shutil.which("pw-record"):
            try:
                subprocess.run(
                    ["pw-record", "--rate", "16000", "--channels", "1",
                     "--format", "s16", str(out)],
                    timeout=seconds + 5, check=False,
                )
                return out.exists()
            except Exception:
                pass
        return False

    # --- Notifications ---
    def notify(self, title: str, body: str) -> bool:
        if not shutil.which("notify-send"):
            return False
        try:
            subprocess.run(
                ["notify-send", "-a", "Aura", title, body],
                timeout=5, check=False,
            )
            return True
        except Exception:
            return False

    # --- TTS ---
    def speak(self, text: str) -> bool:
        for cmd in (["spd-say", "-w"], ["espeak-ng", "-v", "ru"],
                    ["espeak", "-v", "ru"]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run([*cmd, text], timeout=30, check=False)
                    return True
                except Exception:
                    continue
        return False

    # --- Clipboard ---
    def _clip_commands(self, mode: str) -> list[list[str]]:
        if mode == "get":
            return [
                ["wl-paste", "--no-newline"],
                ["xclip", "-selection", "clipboard", "-o"],
                ["xsel", "--clipboard", "--output"],
            ]
        return [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]

    def clipboard_get(self) -> str:
        for cmd in self._clip_commands("get"):
            if shutil.which(cmd[0]):
                try:
                    r = subprocess.run(cmd, capture_output=True,
                                       text=True, timeout=3)
                    if r.returncode == 0:
                        return r.stdout
                except Exception:
                    continue
        return ""

    def clipboard_set(self, text: str) -> bool:
        for cmd in self._clip_commands("set"):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, input=text, text=True,
                                   timeout=3, check=False)
                    return True
                except Exception:
                    continue
        return False

    # --- Open ---
    def open_url(self, url: str) -> bool:
        if not shutil.which("xdg-open"):
            return False
        try:
            subprocess.Popen(["xdg-open", url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    def open_file(self, path: Path) -> bool:
        return self.open_url(str(path))


__all__ = ["LinuxPlatform"]
