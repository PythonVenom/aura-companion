"""#25-28 Порты: Astra, Эльбрус, ARM, Fedora — проверка установщиков."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
INSTALLERS = REPO / "install_fedora.sh", REPO / "install_arm.sh", REPO / "install_astra.sh", REPO / "install_elbrus.sh"


@pytest.mark.parametrize("installer", INSTALLERS, ids=lambda p: p.name)
def test_installer_exists(installer: Path):
    """Установщик существует и исполняемый."""
    assert installer.exists(), f"{installer.name} не найден"
    assert installer.stat().st_mode & 0o111, f"{installer.name} не исполняемый"


@pytest.mark.parametrize("installer", INSTALLERS, ids=lambda p: p.name)
def test_installer_syntax(installer: Path):
    """Bash-синтаксис валиден (bash -n)."""
    r = subprocess.run(["bash", "-n", str(installer)], capture_output=True, text=True)
    assert r.returncode == 0, f"{installer.name}: {r.stderr}"


@pytest.mark.parametrize("installer", INSTALLERS, ids=lambda p: p.name)
def test_installer_has_shebang(installer: Path):
    """Shebang #!/bin/bash на первой строке."""
    first = installer.read_text().splitlines()[0]
    assert first.startswith("#!/"), f"{installer.name}: bad shebang {first!r}"


@pytest.mark.parametrize("installer", INSTALLERS, ids=lambda p: p.name)
def test_installer_has_venv(installer: Path):
    """Создаёт venv ИЛИ делегирует в другой установщик (DRY)."""
    src = installer.read_text().lower()
    # ARM-установщик делегирует в install.sh/install_ubuntu.sh
    assert "venv" in src or "install_" in src, \
        f"{installer.name}: ни venv, ни делегирования"


@pytest.mark.parametrize("installer", INSTALLERS, ids=lambda p: p.name)
def test_installer_has_set_e(installer: Path):
    """set -e для остановки при ошибках."""
    src = installer.read_text()
    assert "set -e" in src, f"{installer.name}: нет set -e"


# === Специфика каждого дистрибутива ===

def test_fedora_uses_dnf():
    src = (REPO / "install_fedora.sh").read_text()
    assert "dnf" in src, "Fedora должна использовать dnf"


def test_astra_uses_apt():
    src = (REPO / "install_astra.sh").read_text()
    assert "apt" in src, "Astra = DEB-based → apt"


def test_astra_detects_version():
    src = (REPO / "install_astra.sh").read_text()
    assert "/etc/astra_version" in src, "Проверка /etc/astra_version"


def test_elbrus_detects_e2k():
    src = (REPO / "install_elbrus.sh").read_text()
    assert "e2k" in src, "Проверка e2k архитектуры"


def test_elbrus_handles_source_build():
    """E2K может требовать сборки из исходников."""
    src = (REPO / "install_elbrus.sh").read_text()
    assert "--no-binary" in src, "Нужна опция сборки из исходников"


def test_arm_detects_arm():
    src = (REPO / "install_arm.sh").read_text()
    assert "arm" in src.lower() or "aarch64" in src.lower()


def test_arm_mentioned_in_docs():
    """ARM должен быть задокументирован."""
    docs = (REPO / "docs/cross-platform.md").read_text()
    assert "ARM" in docs or "arm" in docs


def test_all_distros_mentioned_in_docs():
    """Все 4 порта упомянуты в cross-platform.md."""
    docs = (REPO / "docs/cross-platform.md").read_text()
    for distro in ("Astra", "Эльбрус", "ARM", "Fedora"):
        assert distro in docs, f"{distro} не задокументирован"
