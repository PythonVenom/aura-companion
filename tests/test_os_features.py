"""T-os-10 — тесты symbiotic layer framework."""
import sys
from pathlib import Path
from unittest.mock import patch

from aura.core import os_features


def test_current_os_detected():
    os_name = os_features.current_os()
    assert os_name in ("linux", "macos", "windows", "bsd", "android", "astra", "unknown")


def test_registry_not_empty():
    assert len(os_features.REGISTRY) >= 15
    assert "windows.sapi" in os_features.REGISTRY
    assert "macos.keychain" in os_features.REGISTRY
    assert "astra.mac_parsec" in os_features.REGISTRY


def test_detect_wrong_os():
    # На Linux "windows.sapi" не доступен
    with patch.object(os_features, "current_os", return_value="linux"):
        assert os_features.detect("windows.sapi") is False


def test_detect_same_os_missing():
    # Linux.systemd зарегистрирован, но модуля может не быть
    with patch.object(os_features, "current_os", return_value="linux"):
        # detect возвращает True (feature в реестре)
        assert os_features.detect("linux.systemd") is True


def test_detect_malformed():
    assert os_features.detect("no_dot_here") is False
    assert os_features.detect("") is False


def test_get_none_for_other_os():
    with patch.object(os_features, "current_os", return_value="linux"):
        assert os_features.get("windows.sapi") is None


def test_get_none_for_missing_module():
    # feature в реестре, но модуль без класса → None
    with patch.object(os_features, "current_os", return_value="windows"):
        # windows.py — заглушка без SAPIAdapter → None
        assert os_features.get("windows.sapi") is None


def test_list_available_returns_dict():
    result = os_features.list_available()
    assert isinstance(result, dict)
    # на linux → только linux.*
    for fid in result:
        assert fid.startswith(f"{os_features.current_os()}.")


def test_list_all_has_all_os():
    result = os_features.list_all()
    assert "windows" in result
    assert "macos" in result
    assert "astra" in result
    assert "linux" in result


def test_safe_call_default_when_no_feature():
    # На Linux windows.sapi недоступен → default
    with patch.object(os_features, "current_os", return_value="linux"):
        r = os_features.safe_call("windows.sapi", "speak", "test", default="fallback")
        assert r == "fallback"


def test_safe_call_no_raise():
    # Даже если adapter есть, но метод падает — safe_call не raise
    class Boom:
        def explode(self):
            raise RuntimeError("boom")

    with patch.object(os_features, "get", return_value=Boom()):
        r = os_features.safe_call("linux.systemd", "explode", default="ok")
        assert r == "ok"


def test_safe_call_missing_method():
    class Empty:
        pass

    with patch.object(os_features, "get", return_value=Empty()):
        r = os_features.safe_call("linux.systemd", "nonexistent", default=42)
        assert r == 42


def test_status_structure():
    s = os_features.status()
    assert "os" in s
    assert "features_registered" in s
    assert "features_available" in s
    assert "registry_total" in s
    assert s["registry_total"] >= 15


def test_status_on_linux():
    with patch.object(os_features, "current_os", return_value="linux"):
        s = os_features.status()
        assert s["os"] == "linux"
        assert "linux.systemd" in s["available"]
        assert "windows.sapi" not in s["available"]
