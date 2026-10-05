"""T-os-4 — тесты Windows adapters (SAPI/WSR/Hello/Registry)."""
from unittest.mock import patch

from aura.os_features import windows


def test_not_windows():
    with patch.object(windows, "_is_windows", return_value=False):
        assert windows.SAPIAdapter().available() is False
        assert windows.WSRAdapter().available() is False
        assert windows.HelloAdapter().available() is False
        assert windows.RegistryAdapter().available() is False


def test_sapi_no_powershell():
    with patch.object(windows, "_is_windows", return_value=True), \
         patch.object(windows, "_has_powershell", return_value=False):
        assert windows.SAPIAdapter().available() is False


def test_sapi_available():
    with patch.object(windows, "_is_windows", return_value=True), \
         patch.object(windows, "_has_powershell", return_value=True):
        assert windows.SAPIAdapter().available() is True


def test_sapi_speak_when_unavailable():
    with patch.object(windows, "_is_windows", return_value=False):
        assert windows.SAPIAdapter().speak("test") is False


def test_sapi_list_voices_when_unavailable():
    with patch.object(windows, "_is_windows", return_value=False):
        assert windows.SAPIAdapter().list_voices() == []


def test_wsr_listen_placeholder():
    with patch.object(windows, "_is_windows", return_value=True):
        # placeholder — None
        assert windows.WSRAdapter().listen() is None


def test_hello_verify_placeholder():
    with patch.object(windows, "_is_windows", return_value=True):
        assert windows.HelloAdapter().verify() is False


def test_registry_set_autostart_unavailable():
    with patch.object(windows, "_is_windows", return_value=False):
        assert windows.RegistryAdapter().set_autostart("Aura", "C:\\x.exe") is False
        assert windows.RegistryAdapter().get_autostart("Aura") is None


def test_defender_available_structure():
    with patch.object(windows, "_is_windows", return_value=False):
        assert windows.DefenderAdapter().available() is False


def test_via_framework():
    """Через T-os-10 framework."""
    from aura.core import os_features
    with patch.object(os_features, "current_os", return_value="windows"):
        sapi = os_features.get("windows.sapi")
        assert sapi is not None
        assert hasattr(sapi, "speak")
        assert hasattr(sapi, "list_voices")


def test_safe_call_sapi_on_windows():
    from aura.core import os_features
    with patch.object(os_features, "current_os", return_value="windows"):
        # SAPI adapter есть → safe_call не должен падать
        # (но speak может быть False, т.к. мы не на Windows)
        r = os_features.safe_call("windows.sapi", "speak", "x", default=False)
        assert isinstance(r, bool)
