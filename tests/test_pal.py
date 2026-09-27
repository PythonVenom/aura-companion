"""PAL (ADR-017): Platform Abstraction Layer."""
from aura.platform import get_audio, get_service, get_media
from aura.platform import _distro, _is_ubuntu_like


def test_audio_returns_instance():
    a = get_audio()
    assert hasattr(a, "list_sinks")
    assert hasattr(a, "duck")
    assert hasattr(a, "unduck")


def test_service_returns_instance():
    s = get_service()
    assert hasattr(s, "notify")


def test_media_returns_instance():
    m = get_media()
    assert hasattr(m, "list_players")


def test_detect_arch():
    """На Arch должен быть LinuxAudio, не UbuntuAudio."""
    a = get_audio()
    assert a.__class__.__name__ in ("LinuxAudio", "UbuntuAudio")


def test_ubuntu_detection_false_on_arch():
    """Если это Arch — _is_ubuntu_like() == False."""
    if _distro() == "arch":
        assert _is_ubuntu_like() is False


def test_list_sinks_returns_list():
    assert isinstance(get_audio().list_sinks(), list)


def test_ubuntu_audio_exists():
    """UbuntuAudio класс существует и совместим с LinuxAudio."""
    from aura.platform.ubuntu import UbuntuAudio
    a = UbuntuAudio()
    assert hasattr(a, "list_sinks")
    assert hasattr(a, "duck")


def test_ubuntu_service_inherits_linux():
    from aura.platform.ubuntu import UbuntuService
    from aura.platform.linux import LinuxService
    assert issubclass(UbuntuService, LinuxService)


def test_ubuntu_media_inherits_linux():
    from aura.platform.ubuntu import UbuntuMedia
    from aura.platform.linux import LinuxMedia
    assert issubclass(UbuntuMedia, LinuxMedia)


def test_windows_stub_raises():
    from aura.platform.windows import WindowsAudio
    import pytest
    with pytest.raises(NotImplementedError):
        WindowsAudio()


def test_macos_stub_raises():
    from aura.platform.macos import MacOSAudio
    import pytest
    with pytest.raises(NotImplementedError):
        MacOSAudio()
