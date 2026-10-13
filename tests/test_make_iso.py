"""Д42 Фаза 2 — тесты Live ISO builder."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
ISO_SCRIPT = REPO / "aura-make-iso.sh"
PROFILE_DIR = REPO / "aura-os"


# === Скрипт ===

def test_iso_script_exists():
    assert ISO_SCRIPT.exists()


def test_iso_script_executable():
    assert ISO_SCRIPT.stat().st_mode & 0o111


def test_iso_script_syntax():
    r = subprocess.run(["bash", "-n", str(ISO_SCRIPT)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode()


def test_iso_script_shebang():
    first = ISO_SCRIPT.read_text().splitlines()[0]
    assert first.startswith("#!/")


def test_iso_script_help():
    r = subprocess.run(
        ["bash", str(ISO_SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    assert "Фаза 2" in r.stdout or "ISO" in r.stdout


def test_iso_script_rejects_unknown_arg():
    r = subprocess.run(
        ["bash", str(ISO_SCRIPT), "--garbage"],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "Неизвестный" in r.stderr


def test_iso_script_no_auto_dd():
    """Безопасность: dd не должен ИСПОЛНЯТЬСЯ (только показан юзеру)."""
    src = ISO_SCRIPT.read_text()
    # Проверяем, что нет строк, начинающихся с "sudo dd" ВНЕ heredoc
    # (heredoc — от "cat <<" до "FINAL" или "TXT")
    in_heredoc = False
    bad_lines = []
    for line in src.splitlines():
        stripped = line.strip()
        if "<<" in line and ("FINAL" in line or "TXT" in line):
            in_heredoc = True
            continue
        if in_heredoc and stripped in ("FINAL", "TXT"):
            in_heredoc = False
            continue
        if not in_heredoc and stripped.startswith("sudo dd"):
            bad_lines.append(stripped)
    assert not bad_lines, f"❌ dd не должен исполняться: {bad_lines}"


def test_iso_script_warns_user():
    """Скрипт должен предупреждать о рисках."""
    src = ISO_SCRIPT.read_text()
    assert "защита от dd" in src or "НЕ будем" in src
    assert "ОСТОРОЖНО" in src or "дважды" in src.lower()


# === Профиль aura-os ===

def test_profile_dir_exists():
    assert PROFILE_DIR.exists()


def test_profile_build_sh():
    assert (PROFILE_DIR / "build.sh").exists()


def test_profile_profiledef():
    assert (PROFILE_DIR / "profiledef.sh").exists()


def test_profile_build_syntax():
    r = subprocess.run(
        ["bash", "-n", str(PROFILE_DIR / "build.sh")],
        capture_output=True,
    )
    assert r.returncode == 0
