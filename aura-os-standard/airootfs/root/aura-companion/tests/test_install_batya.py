"""Tests для install_batya.sh."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "install_batya.sh"


def test_exists():
    assert SCRIPT.exists()


def test_executable():
    assert SCRIPT.stat().st_mode & 0o111


def test_syntax():
    r = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode()


def test_shebang():
    first = SCRIPT.read_text().splitlines()[0]
    assert first.startswith("#!/")


def test_has_set_euo():
    assert "set -euo pipefail" in SCRIPT.read_text()


def test_has_elder_profile():
    src = SCRIPT.read_text()
    assert '"profile": "elder"' in src or "AURA_PROFILE=elder" in src


def test_has_brain_off():
    """LLM отключён для elder."""
    assert "AURA_BRAIN=0" in SCRIPT.read_text()


def test_has_systemd():
    src = SCRIPT.read_text()
    assert "aura.service" in src
    assert "systemctl --user" in src


def test_has_sos_instructions():
    """Инструкция для бати: если не отвечает — звони сыну."""
    src = SCRIPT.read_text()
    assert "позвони сыну" in src.lower() or "сыну" in src.lower()


def test_covers_3_pkg_managers():
    src = SCRIPT.read_text()
    assert "pacman" in src
    assert "apt" in src
    assert "dnf" in src


def test_downloads_piper_voice():
    assert "ru_RU-irina-medium" in SCRIPT.read_text()


def test_has_elder_settings():
    """Голос медленнее для elder-care."""
    src = SCRIPT.read_text()
    assert '"tts_speed": 0.9' in src
    assert "voice_volume_boost" in src
