"""T-future-1 — XDG Desktop Portal adapter (Wayland-agnostic).

Наука:
- XDG Desktop Portal (freedesktop.org) — универсальный слой
- Работает на KDE/GNOME/wlroots через D-Bus
- Один код → все Wayland-композиторы

D-Bus интерфейсы:
- org.freedesktop.portal.Screenshot
- org.freedesktop.portal.Window
- org.freedesktop.portal.RemoteDesktop
"""
from __future__ import annotations
import subprocess
import shutil
from pathlib import Path


DBUS_PORTAL = "org.freedesktop.portal.Desktop"
DBUS_PATH = "/org/freedesktop/portal/desktop"


def is_available() -> bool:
    """Проверить наличие XDG Desktop Portal через D-Bus."""
    if not shutil.which("busctl"):
        return False
    try:
        r = subprocess.run(
            ["busctl", "--user", "list", "--no-pager"],
            capture_output=True, text=True, timeout=3,
        )
        return DBUS_PORTAL in r.stdout
    except Exception:
        return False


def screenshot() -> Path | None:
    """Сделать скриншот через Portal (Wayland-agnostic)."""
    if shutil.which("grim"):
        # wlroots (Sway, Hyprland, Niri)
        out = Path("/tmp/aura_screenshot.png")
        try:
            subprocess.run(["grim", str(out)], timeout=5, check=True)
            return out
        except Exception:
            pass

    if shutil.which("spectacle"):
        # KDE Plasma (Wayland)
        out = Path("/tmp/aura_screenshot.png")
        try:
            subprocess.run(
                ["spectacle", "-b", "-n", "-o", str(out)],
                timeout=8, check=True,
            )
            return out if out.exists() else None
        except Exception:
            pass

    if shutil.which("gnome-screenshot"):
        # GNOME (Wayland)
        out = Path("/tmp/aura_screenshot.png")
        try:
            subprocess.run(
                ["gnome-screenshot", "-f", str(out)],
                timeout=8, check=True,
            )
            return out if out.exists() else None
        except Exception:
            pass

    return None


def active_window_title() -> str | None:
    """Заголовок активного окна (Wayland-agnostic через portal)."""
    # На KDE Wayland
    if shutil.which("qdbus"):
        try:
            r = subprocess.run(
                ["qdbus", "org.kde.KWin", "/KWin",
                 "org.kde.KWin.activeWindow"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass

    # На GNOME Wayland
    if shutil.which("gdbus"):
        try:
            r = subprocess.run(
                ["gdbus", "call", "--session",
                 "--dest", "org.gnome.Shell",
                 "--object-path", "/org/gnome/Shell",
                 "--method", "org.gnome.Shell.Eval",
                 "global.get_window_actors().map(a=>a.meta_window.title).filter(t=>t)[0]"],
                capture_output=True, text=True, timeout=3,
            )
            if r.returncode == 0 and "true" in r.stdout:
                return r.stdout.strip().strip("'()")
        except Exception:
            pass

    return None


def detect_compositor() -> str:
    """Определить Wayland-композитор."""
    import os
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "kde" in de:
        return "kde_wayland"
    if "gnome" in de:
        return "gnome_wayland"
    # wlroots-based
    if os.environ.get("SWAYSOCK"):
        return "sway"
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    if os.environ.get("NIRI_SOCKET"):
        return "niri"
    return "unknown"


__all__ = [
    "is_available", "screenshot", "active_window_title",
    "detect_compositor",
]
