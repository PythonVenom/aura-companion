"""macOS: CoreAudio + AppleScript + launchd.

Зависимости:
- sounddevice (CoreAudio)
- osascript (встроен)
"""
from __future__ import annotations

import contextlib
import subprocess


class MacOSAudio:
    def list_sinks(self) -> list[str]:
        try:
            r = subprocess.run(
                ["system_profiler", "SPAudioDataType"],
                capture_output=True, text=True, timeout=3)
            return [line.strip() for line in r.stdout.splitlines()
                    if ":" in line and "Output" in line]
        except Exception:
            return []

    def list_sources(self) -> list[str]:
        try:
            r = subprocess.run(
                ["system_profiler", "SPAudioDataType"],
                capture_output=True, text=True, timeout=3)
            return [line.strip() for line in r.stdout.splitlines()
                    if ":" in line and "Input" in line]
        except Exception:
            return []

    def get_default_sink(self) -> str:
        return "default"

    def set_default_sink(self, name: str) -> bool:
        return False

    def duck(self, level: float = 0.2) -> None:
        with contextlib.suppress(Exception):
            subprocess.run(
                ["osascript", "-e",
                 f"set volume output volume {int(level*100)}"],
                capture_output=True, timeout=2)

    def unduck(self) -> None:
        with contextlib.suppress(Exception):
            subprocess.run(
                ["osascript", "-e", "set volume output volume 100"],
                capture_output=True, timeout=2)


class MacOSService:
    def _plist_path(self) -> str:
        from pathlib import Path
        return str(Path.home() / "Library/LaunchAgents/com.aura.companion.plist")

    def enable_autostart(self) -> bool:
        plist = self._plist_path()
        content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.aura.companion</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>-m</string>
        <string>aura_main</string>
    </array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>"""
        try:
            with open(plist, "w") as f:
                f.write(content)
            subprocess.run(["launchctl", "load", plist],
                           capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def disable_autostart(self) -> bool:
        try:
            subprocess.run(["launchctl", "unload", self._plist_path()],
                           capture_output=True, timeout=3)
            return True
        except Exception:
            return False

    def notify(self, title: str, body: str) -> None:
        with contextlib.suppress(Exception):
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{body}" with title "{title}"'],
                capture_output=True, timeout=2)


class MacOSMedia:
    def list_players(self) -> list[str]:
        try:
            r = subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to get name of every process'],
                capture_output=True, text=True, timeout=3)
            apps = r.stdout.split(", ")
            return [a for a in apps if a in ("Music", "Spotify", "VLC")]
        except Exception:
            return []

    def pause_all(self) -> bool:
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "Music" to pause'],
                capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def resume_all(self) -> bool:
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "Music" to play'],
                capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def get_last_active(self) -> str | None:
        from aura.agents import media_state
        return media_state.get_active()


__all__ = ["MacOSAudio", "MacOSMedia", "MacOSService"]
