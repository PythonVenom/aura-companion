"""Определение окружения: DE, WM, дистрибутив, sound, session."""
import os
import shutil
from functools import lru_cache
from pathlib import Path


def _detect_de() -> str:
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()
    for key, name in [
        ("kde", "kde"), ("gnome", "gnome"), ("xfce", "xfce"),
        ("cinnamon", "cinnamon"), ("mate", "mate"), ("lxqt", "lxqt"),
        ("budgie", "budgie"), ("sway", "sway"), ("hyprland", "hyprland"),
        ("i3", "i3"), ("deepin", "deepin"),
    ]:
        if key in de or key in session:
            return name
    return "unknown"


def _detect_session() -> str:
    return os.environ.get("XDG_SESSION_TYPE", "x11").lower()


def _detect_distro() -> str:
    try:
        content = Path("/etc/os-release").read_text()
        for line in content.splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip(chr(34)).lower()
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.detect').debug(
            'detect error: %s', e)
    return "unknown"


def _detect_sound() -> str:
    if shutil.which("pw-cli") or shutil.which("wpctl"):
        return "pipewire"
    if shutil.which("pactl"):
        return "pulseaudio"
    if shutil.which("amixer"):
        return "alsa"
    return "unknown"


def _has_systemd() -> bool:
    return Path("/run/systemd/system").exists()


def _detect_wm() -> str:
    session = _detect_session()
    if session == "wayland":
        if os.environ.get("SWAYSOCK"):
            return "sway"
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "hyprland"
        if shutil.which("qdbus6"):
            return "kwin_wayland"
        return "wayland_generic"
    if shutil.which("qdbus6") or shutil.which("qdbus"):
        return "kwin"
    if shutil.which("wmctrl"):
        return "wmctrl"
    if shutil.which("xdotool"):
        return "xdotool"
    return "unknown"


def _detect_tray() -> str:
    if os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        return "sni"
    return "none"


@lru_cache(maxsize=1)
def detect() -> dict:
    return {
        "de": _detect_de(),
        "wm": _detect_wm(),
        "session": _detect_session(),
        "distro": _detect_distro(),
        "sound": _detect_sound(),
        "systemd": _has_systemd(),
        "tray": _detect_tray(),
    }


def get_env(key: str, default=None):
    return detect().get(key, default)


if __name__ == "__main__":
    import json
    print(json.dumps(detect(), ensure_ascii=False, indent=2))
