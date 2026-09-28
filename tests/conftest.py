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
            if first in DANGEROUS_CMDS:
                raise RuntimeError(
                    f"Bug 18: тест вызвал {cmd!r} без мока. "
                    f"Патчить через monkeypatch.setattr(a, '_lock', ...) "
                    f"или patch('subprocess.Popen')."
                )
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", guarded)


