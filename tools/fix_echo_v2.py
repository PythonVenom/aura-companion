#!/usr/bin/env python3
"""Idempotent fix for double-voice echo (AURA_ECHO_FIX_V2)."""
import sys
from pathlib import Path

MAIN = Path.home() / "aura_project" / "aura_main.py"
MARK = "# >>> AURA_ECHO_FIX_V2"
src = MAIN.read_text(encoding="utf-8")

if MARK in src:
    print("[skip] already patched")
    sys.exit(0)

old1 = (
    "                self._duck_on()\n"
    "                self._set_barge_speaking(True)\n"
    "                # ADR-048: silent=True — не озвучивать\n"
    "                if not self.orch.last_silent():\n"
    "                    self.speaker.say(response)\n"
)
new1 = (
    "                self._duck_on()\n"
    "                self._set_barge_speaking(True)\n"
    "                " + MARK + "\n"
    "                # Mic mute + TTS в память эхо-фильтра\n"
    "                try:\n"
    "                    self.listener.set_last_response(response)\n"
    "                    self.listener.pause()\n"
    "                except Exception as _e:\n"
    "                    print(f'⚠️ echo-prep: {_e}')\n"
    "                # ADR-048: silent=True — не озвучивать\n"
    "                if not self.orch.last_silent():\n"
    "                    self.speaker.say(response)\n"
)

old2 = (
    "                self._set_barge_speaking(False)\n"
    "                self._duck_off()\n"
)
new2 = (
    "                self._set_barge_speaking(False)\n"
    "                self._duck_off()\n"
    "                " + MARK + "\n"
    "                # Cooldown + снять mic mute\n"
    "                time.sleep(1.5)\n"
    "                try:\n"
    "                    self.listener.resume()\n"
    "                except Exception as _e:\n"
    "                    print(f'⚠️ echo-resume: {_e}')\n"
)

if old1 not in src:
    print("[FAIL] patch1 pattern not found — пришли строки 660-670 aura_main.py")
    sys.exit(1)
if old2 not in src:
    print("[FAIL] patch2 pattern not found — пришли строки 695-702 aura_main.py")
    sys.exit(1)

src = src.replace(old1, new1, 1).replace(old2, new2, 1)
MAIN.write_text(src, encoding="utf-8")
print("[ok] aura_main.py patched with AURA_ECHO_FIX_V2")
