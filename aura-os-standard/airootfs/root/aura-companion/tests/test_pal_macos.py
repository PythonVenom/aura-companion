"""PAL macOS."""
from unittest.mock import patch, MagicMock
from aura.platform.macos import MacOSAudio, MacOSService, MacOSMedia


def test_macos_audio_lists_empty():
    a = MacOSAudio()
    with patch("subprocess.run") as mock:
        mock.return_value.stdout = ""
        assert a.list_sinks() == []


def test_macos_duck_calls_osascript():
    a = MacOSAudio()
    with patch("subprocess.run") as mock:
        a.duck(0.2)
        mock.assert_called()
        call_args = str(mock.call_args)
        assert "osascript" in call_args


def test_macos_service_notify():
    s = MacOSService()
    with patch("subprocess.run") as mock:
        s.notify("t", "b")
        mock.assert_called()


def test_macos_media_pause():
    m = MacOSMedia()
    with patch("subprocess.run") as mock:
        mock.return_value.stdout = ""
        assert m.pause_all() is True
