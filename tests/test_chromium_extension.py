"""#99 — тесты Chromium extension + host installer."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
CHROMIUM_DIR = REPO / "chromium_extension"
MANIFEST = CHROMIUM_DIR / "manifest.json"
BACKGROUND = CHROMIUM_DIR / "background.js"
INSTALLER = REPO / "install_chromium_host.sh"
NATIVE_HOST = REPO / "scripts/aura_bridge_host.py"


# === chromium_extension/manifest.json ===

def test_manifest_exists():
    assert MANIFEST.exists()


def test_manifest_valid_json():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_manifest_version_3():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["manifest_version"] == 3


def test_manifest_name():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "Aura Bridge"


def test_manifest_has_native_messaging():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "nativeMessaging" in data["permissions"]


def test_manifest_has_service_worker():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["background"]["service_worker"] == "background.js"


def test_manifest_host_permissions():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hosts = " ".join(data.get("host_permissions", []))
    assert "max.ru" in hosts


def test_manifest_no_gecko_specific():
    """Chromium manifest НЕ должен иметь browser_specific_settings (Firefox-only)."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "browser_specific_settings" not in data


# === background.js ===

def test_background_js_exists():
    assert BACKGROUND.exists()


def test_background_uses_chrome_api():
    """Использует chrome.* (совместимо с Chromium)."""
    src = BACKGROUND.read_text(encoding="utf-8")
    assert "chrome.runtime.connectNative" in src
    assert "chrome.tabs" in src


def test_background_native_host_name():
    src = BACKGROUND.read_text(encoding="utf-8")
    assert 'aura_bridge' in src


def test_background_handles_disconnect():
    src = BACKGROUND.read_text(encoding="utf-8")
    assert "onDisconnect" in src


# === content scripts ===

def test_content_max_exists():
    assert (CHROMIUM_DIR / "content_max.js").exists()


# === install_chromium_host.sh ===

def test_installer_exists():
    assert INSTALLER.exists()


def test_installer_executable():
    assert INSTALLER.stat().st_mode & 0o111


def test_installer_syntax():
    r = subprocess.run(["bash", "-n", str(INSTALLER)], capture_output=True)
    assert r.returncode == 0, r.stderr.decode()


def test_installer_shebang():
    first = INSTALLER.read_text().splitlines()[0]
    assert first.startswith("#!/")


def test_installer_has_host_name():
    src = INSTALLER.read_text()
    assert 'HOST_NAME="aura_bridge"' in src


def test_installer_covers_browsers():
    """Скрипт покрывает 5+ Chromium-браузеров."""
    src = INSTALLER.read_text()
    for browser in ("google-chrome", "chromium", "microsoft-edge",
                    "BraveSoftware", "vivaldi", "opera"):
        assert browser in src, f"{browser} не упомянут"


def test_installer_uses_native_messaging_dir():
    src = INSTALLER.read_text()
    assert "NativeMessagingHosts" in src


# === native host ===

def test_native_host_exists():
    assert NATIVE_HOST.exists()


def test_native_host_executable_or_python():
    """Host должен быть .py — запускается через python."""
    first = NATIVE_HOST.read_text().splitlines()[0]
    assert "python" in first.lower() or NATIVE_HOST.stat().st_mode & 0o111


# === firefox compatibility ===

def test_firefox_mv2_exists():
    """Firefox MV2 остаётся для старых версий."""
    assert (REPO / "firefox_extension/manifest.json").exists()


def test_firefox_mv3_exists():
    """Firefox MV3 — для 109+."""
    assert (REPO / "firefox_extension_mv3/manifest.json").exists()
