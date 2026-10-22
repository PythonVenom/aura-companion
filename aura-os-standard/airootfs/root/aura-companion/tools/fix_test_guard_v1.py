#!/usr/bin/env python3
"""Extend conftest guarded() to block desktop commands (Bug 49)."""
import sys
from pathlib import Path

p = Path("tests/conftest.py")
src = p.read_text(encoding="utf-8")
MARK = "# >>> AURA_TEST_DESKTOP_GUARD_V1"

if MARK in src:
    print("[skip] already patched")
    sys.exit(0)

old_dang = '''DANGEROUS_CMDS = frozenset({
    "systemctl", "loginctl",
    "poweroff", "reboot", "shutdown", "halt",
})'''

new_dang = old_dang + '''

''' + MARK + '''
# Bug 49: tests must not open windows/tabs/play sound via real subprocess.
DESKTOP_CMDS = frozenset({
    "xdg-open", "firefox", "chromium", "google-chrome",
    "paplay", "pw-play", "aplay", "ffplay", "mpv",
    "kdotool", "wmctrl", "xdotool", "kstart", "kstart5",
})


class _FakeDesktopProc:
    """Mock process for desktop commands."""

    def __init__(self, args=None, *a, **kw):
        self.args = args or []
        self.returncode = 0
        self.pid = 0
        self.stdout = None
        self.stderr = None

    def wait(self, timeout=None):
        return 0

    def poll(self):
        return 0

    def communicate(self, *a, **kw):
        return (b"", b"")

    def kill(self):
        pass

    def terminate(self):
        pass'''

if old_dang not in src:
    print("[FAIL] DANGEROUS_CMDS block not found")
    sys.exit(1)
src = src.replace(old_dang, new_dang, 1)

old_insert = '''            first = str(cmd[0]).split("/")[-1]
            if first in DANGEROUS_CMDS:'''

new_insert = '''            first = str(cmd[0]).split("/")[-1]
            ''' + MARK + '''
            if first in DESKTOP_CMDS:
                return _FakeDesktopProc(cmd)
            if first in DANGEROUS_CMDS:'''

if old_insert not in src:
    print("[FAIL] guarded() pattern not found")
    sys.exit(1)
src = src.replace(old_insert, new_insert, 1)

p.write_text(src, encoding="utf-8")
print("[ok] tests/conftest.py extended with desktop guard")
