"""PAL Ubuntu: реальная реализация."""
from unittest.mock import patch
from aura.platform.ubuntu import UbuntuAudio, UbuntuService, UbuntuMedia
from aura.platform.linux import LinuxAudio, LinuxService, LinuxMedia


def test_ubuntu_audio_has_methods():
    a = UbuntuAudio()
    assert hasattr(a, "list_sinks")
    assert hasattr(a, "duck")
    assert hasattr(a, "unduck")


def test_ubuntu_service_inherits():
    assert issubclass(UbuntuService, LinuxService)


def test_ubuntu_media_inherits():
    assert issubclass(UbuntuMedia, LinuxMedia)


def test_ubuntu_audio_lists():
    a = UbuntuAudio()
    with patch("subprocess.run") as mock:
        mock.return_value.stdout = ""
        assert isinstance(a.list_sinks(), list)


def test_ubuntu_duck_calls_pactl():
    a = UbuntuAudio()
    with patch("subprocess.run") as mock:
        a.duck(0.3)
        assert mock.called
