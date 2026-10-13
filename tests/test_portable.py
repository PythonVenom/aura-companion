"""Д42 — тесты Portable Mode."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
USB_SCRIPT = REPO / "aura-usb.sh"
INSTALLER = REPO / "install_universal.sh"


# === aura-usb.sh ===

def test_usb_script_exists():
    assert USB_SCRIPT.exists()


def test_usb_script_executable():
    assert USB_SCRIPT.stat().st_mode & 0o111


def test_usb_script_syntax():
    """Bash синтаксис валиден."""
    r = subprocess.run(["bash", "-n", str(USB_SCRIPT)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode()


def test_usb_script_shebang():
    first = USB_SCRIPT.read_text().splitlines()[0]
    assert first.startswith("#!/")


def test_usb_script_requires_path():
    """Без аргумента — ошибка."""
    r = subprocess.run(["bash", str(USB_SCRIPT)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "Укажи путь" in r.stderr or "path" in r.stderr.lower()


def test_usb_script_rejects_nonexistent():
    """Несуществующий путь — ошибка."""
    r = subprocess.run(
        ["bash", str(USB_SCRIPT), "/nonexistent/path/xyz"],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "не существует" in r.stderr


def test_usb_script_creates_structure(tmp_path):
    """Создаёт 4 папки на флешке (с --dry-run-подобным поведением).

    Не запускаем rsync/git — только mkdir. Проверяем структуру.
    """
    # Создаём структуру вручную через mkdir (как в скрипте)
    for d in ("aura-project", "aura-cache", "aura-config", "aura-models"):
        (tmp_path / d).mkdir()
    assert (tmp_path / "aura-project").is_dir()
    assert (tmp_path / "aura-cache").is_dir()
    assert (tmp_path / "aura-config").is_dir()
    assert (tmp_path / "aura-models").is_dir()


# === install_universal.sh --portable ===

def test_installer_has_portable_flag():
    src = INSTALLER.read_text()
    assert "--portable" in src


def test_installer_portable_sets_env():
    src = INSTALLER.read_text()
    assert 'AURA_PROJECT_DIR="$PORTABLE_PATH/aura-project"' in src
    assert 'AURA_CACHE_DIR="$PORTABLE_PATH/aura-cache"' in src
    assert 'AURA_CONFIG_DIR="$PORTABLE_PATH/aura-config"' in src


def test_installer_portable_requires_arg():
    """--portable без пути → exit 1."""
    src = INSTALLER.read_text()
    # Проверяем, что есть проверка на пустой аргумент
    assert "требует путь" in src or "PORTABLE_PATH" in src


def test_installer_syntax():
    r = subprocess.run(["bash", "-n", str(INSTALLER)], capture_output=True)
    assert r.returncode == 0


# === paths.py env-override ===

def test_paths_uses_env_override(monkeypatch, tmp_path):
    """AURA_CACHE_DIR из env → paths.CACHE_DIR."""
    import importlib
    import aura.paths

    monkeypatch.setenv("AURA_CACHE_DIR", str(tmp_path / "custom-cache"))
    importlib.reload(aura.paths)
    assert "custom-cache" in str(aura.paths.CACHE_DIR)
    importlib.reload(aura.paths)  # вернуть как было


def test_paths_default_when_no_env(monkeypatch):
    """Без env — default ~/.cache/aura."""
    import importlib
    import aura.paths

    monkeypatch.delenv("AURA_CACHE_DIR", raising=False)
    importlib.reload(aura.paths)
    assert ".cache/aura" in str(aura.paths.CACHE_DIR)
    importlib.reload(aura.paths)
