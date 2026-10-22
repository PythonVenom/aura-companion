"""PAL Fedora/Alpine/ARM/WSL2 — smoke-тесты."""
import sys
from unittest.mock import patch


def test_platform_init_detects_distro():
    from aura.platform import _distro, _is_ubuntu_like
    d = _distro()
    assert isinstance(d, str)
    # На Arch — должен определить arch
    if d:
        assert len(d) > 1


def test_ubuntu_like_for_fedora_false():
    from aura.platform import _is_ubuntu_like
    with patch("aura.platform._distro", return_value="fedora"):
        assert _is_ubuntu_like() is False


def test_ubuntu_like_for_ubuntu_true():
    from aura.platform import _is_ubuntu_like
    with patch("aura.platform._distro", return_value="ubuntu"):
        assert _is_ubuntu_like() is True


def test_ubuntu_like_for_alpine_false():
    from aura.platform import _is_ubuntu_like
    with patch("aura.platform._distro", return_value="alpine"):
        assert _is_ubuntu_like() is False
