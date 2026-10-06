"""macOS HAL — реализация BasePlatform для Darwin.

Наука:
- BasePlatform (Tanenbaum HAL)
- NSSpeechSynthesizer (Apple) — нативный TTS
- pbcopy / pbpaste — clipboard
- osascript (AppleScript) — уведомления
- open — URL/файлы

Отличия от Linux:
- Нет XDG, но похожие пути (~/Library/Application Support)
- TTS через `say`
- Clipboard через `pbcopy` / `pbpaste`
- Уведомления через `osascript`
- Открытие через `open`
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

from aura.platform_adapters.base import BasePlatform


class MacOSPlatform(BasePlatform):
    name = "macos"

    # --- Paths (Apple-style) ---
    def config_dir(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "Aura"

    def data_dir(self) -> Path:
        return Path.home() / "Library" / "Application Support" / "Aura"

    def cache_dir(self) -> Path:
        return Path.home() / "Library" / "Caches" / "Aura"

    # --- Audio ---
    def audio_play(self, path: Path) -> None:
        if shutil.which("afplay"):
            subprocess.run(["afplay", str(path)], check=False, timeout=120)
            return
        for cmd in (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
                    ["mpv", "--no-video", "--really-quiet"]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd + [str(path)], check=False, timeout=120)
                return

    def audio_record(self, seconds: int, out: Path) -> bool:
        # На macOS — sox или ffmpeg
        if shutil.which("sox"):
            try:
                subprocess.run(
                    ["sox", "-d", "-r", "16000", "-c", "1",
                     str(out), "trim", "0", str(seconds)],
                    timeout=seconds + 5, check=False,
                )
                return out.exists()
            except Exception:
                pass
        if shutil.which("ffmpeg"):
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "avfoundation", "-i", ":0",
                     "-t", str(seconds), "-ar", "16000", "-ac", "1",
                     str(out)],
                    timeout=seconds + 5, check=False,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                return out.exists()
            except Exception:
                pass
        return False

    # --- Notifications (osascript) ---
    def notify(self, title: str, body: str) -> bool:
        if not shutil.which("osascript"):
            return False
        try:
            script = (
                f'display notification "{body}" '
                f'with title "{title}" sound name "default"'
            )
            subprocess.run(
                ["osascript", "-e", script],
                timeout=5, check=False,
            )
            return True
        except Exception:
            return False

    # --- TTS (say) ---
    def speak(self, text: str) -> bool:
        if not shutil.which("say"):
            return False
        try:
            subprocess.run(
                ["say", "-v", "Milena", text],  # Milena — русский
                timeout=60, check=False,
            )
            return True
        except Exception:
            return False

    # --- Clipboard ---
    def clipboard_get(self) -> str:
        if not shutil.which("pbpaste"):
            return ""
        try:
            r = subprocess.run(
                ["pbpaste"], capture_output=True, text=True, timeout=3,
            )
            return r.stdout if r.returncode == 0 else ""
        except Exception:
            return ""

    def clipboard_set(self, text: str) -> bool:
        if not shutil.which("pbcopy"):
            return False
        try:
            subprocess.run(
                ["pbcopy"], input=text, text=True, timeout=3, check=False,
            )
            return True
        except Exception:
            return False

    # --- Open ---
    def open_url(self, url: str) -> bool:
        if not shutil.which("open"):
            return False
        try:
            subprocess.Popen(
                ["open", url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def open_file(self, path: Path) -> bool:
        return self.open_url(str(path))


__all__ = ["MacOSPlatform"]
