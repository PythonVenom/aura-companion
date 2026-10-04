"""Общие фикстуры для тестов Aura."""
import pytest

from aura.agents import media_state


@pytest.fixture(autouse=True)
def _clean_media_state():
    """Bug 14: тесты не должны зависеть от live /tmp/aura_media_state.json."""
    media_state.clear()
    yield
    media_state.clear()


"""Глобальные фикстуры. Защита от опасных subprocess в тестах."""
import subprocess

import pytest


DANGEROUS_CMDS = frozenset({
    "systemctl", "loginctl",
    "poweroff", "reboot", "shutdown", "halt",
})

# >>> AURA_TEST_DESKTOP_GUARD_V1
# Bug 49: tests must not open windows/tabs/play sound via real subprocess.
DESKTOP_CMDS = frozenset({
    "xdg-open", "firefox", "chromium", "google-chrome",
    "paplay", "pw-play", "aplay", "ffplay", "mpv",
    "kdotool", "wmctrl", "xdotool", "kstart", "kstart5",
    # >>> AURA_TEST_DESKTOP_GUARD_V2
    # Bug 50: D-Bus / a11y — не пускать в реальную сессию
    "qdbus", "qdbus6", "dbus-send", "gdbus", "busctl",
    "gsettings", "onboard", "tecla", "maliit-keyboard",
    "gnome-screenshot", "spectacle", "flameshot", "grim", "scrot",
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
        pass


@pytest.fixture(autouse=True)
def _no_dangerous_subprocess(monkeypatch):
    """Любой тест, дёрнувший systemctl/loginctl/poweroff/reboot,
    получит RuntimeError. Патчить через monkeypatch/patch.
    Bug 18: тесты не должны выключать/блокировать реальный ПК."""
    real_popen = subprocess.Popen

    def guarded(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, (list, tuple)) and cmd:
            first = str(cmd[0]).split("/")[-1]
            # >>> AURA_TEST_DESKTOP_GUARD_V1
            if first in DESKTOP_CMDS:
                return _FakeDesktopProc(cmd)
            if first in DANGEROUS_CMDS:
                raise RuntimeError(
                    f"Bug 18: тест вызвал {cmd!r} без мока. "
                    f"Патчить через monkeypatch.setattr(a, '_lock', ...) "
                    f"или patch('subprocess.Popen')."
                )
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", guarded)


