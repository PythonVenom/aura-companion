"""Android HAL — реализация BasePlatform для Termux.

Наука:
- Termux (termux.dev) — Linux env на Android
- Termux:API — доступ к железу через намерения Android
- BasePlatform (Tanenbaum HAL)

Отличия от Linux:
- Нет XDG (но похожие пути через $PREFIX)
- Уведомления через `termux-notification`
- TTS через `termux-tts-speak`
- Clipboard через `termux-clipboard-get/set`
- Открытие URL через `termux-open-url`
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path

from aura.platform_adapters.base import BasePlatform


class AndroidPlatform(BasePlatform):
    name = "android"

    def _prefix(self) -> Path:
        return Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))

    # --- Paths (Termux-стиль, не XDG) ---
    def config_dir(self) -> Path:
        return Path.home() / ".config" / "aura"

    def data_dir(self) -> Path:
        return Path.home() / ".local" / "share" / "aura"

    def cache_dir(self) -> Path:
        return Path.home() / ".cache" / "aura"

    # --- Termux:API команды ---

    def _has_termux_api(self, cmd: str) -> bool:
        return shutil.which(cmd) is not None

    # --- Audio ---
    def audio_play(self, path: Path) -> None:
        # В Termux:API нет play, но есть termux-media-player
        if self._has_termux_api("termux-media-player"):
            subprocess.run(
                ["termux-media-player", "play", str(path)],
                check=False, timeout=60,
            )
            return
        # Fallback — mpv/ffplay из pkg
        for cmd in (["mpv", "--no-video", "--really-quiet"],
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd + [str(path)], check=False, timeout=60)
                return

    def audio_record(self, seconds: int, out: Path) -> bool:
        # Только через Termux:API
        if not self._has_termux_api("termux-microphone-record"):
            return False
        try:
            subprocess.run(
                ["termux-microphone-record", "-f", str(out),
                 "-l", str(seconds)],
                timeout=seconds + 5, check=False,
            )
            return out.exists()
        except Exception:
            return False

    # --- Notifications ---
    def notify(self, title: str, body: str) -> bool:
        if not self._has_termux_api("termux-notification"):
            return False
        try:
            subprocess.run(
                ["termux-notification", "--title", title, "--content", body],
                timeout=5, check=False,
            )
            return True
        except Exception:
            return False

    # --- TTS ---
    def speak(self, text: str) -> bool:
        # Приоритет — нативный Android TTS (termux-tts-speak)
        if self._has_termux_api("termux-tts-speak"):
            try:
                subprocess.run(
                    ["termux-tts-speak", text],
                    timeout=30, check=False,
                )
                return True
            except Exception:
                pass
        # Fallback — espeak-ng
        if shutil.which("espeak-ng"):
            try:
                subprocess.run(
                    ["espeak-ng", "-v", "ru", text],
                    timeout=30, check=False,
                )
                return True
            except Exception:
                pass
        return False

    # --- Clipboard ---
    def clipboard_get(self) -> str:
        if not self._has_termux_api("termux-clipboard-get"):
            return ""
        try:
            r = subprocess.run(
                ["termux-clipboard-get"],
                capture_output=True, text=True, timeout=3,
            )
            return r.stdout if r.returncode == 0 else ""
        except Exception:
            return ""

    def clipboard_set(self, text: str) -> bool:
        if not self._has_termux_api("termux-clipboard-set"):
            return False
        try:
            subprocess.run(
                ["termux-clipboard-set", text],
                timeout=3, check=False,
            )
            return True
        except Exception:
            return False

    # --- Open ---
    def open_url(self, url: str) -> bool:
        if not self._has_termux_api("termux-open-url"):
            return False
        try:
            subprocess.Popen(
                ["termux-open-url", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def open_file(self, path: Path) -> bool:
        if not self._has_termux_api("termux-open"):
            return False
        try:
            subprocess.Popen(
                ["termux-open", str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False


__all__ = ["AndroidPlatform"]
