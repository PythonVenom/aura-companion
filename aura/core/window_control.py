"""#131 Window control — перемещение/размер/закрытие окон.

Наука:
- Fitts 1954 — моторные ограничения (батя не может мышью)
- WCAG 2.1 — accessibility
- X11 EWMH (Freedesktop 2005) — стандарт управления окнами

Инструменты:
- wmctrl — перемещение, размер, close (X11 + Wayland-KDE)
- xdotool — клики, клавиши (только X11)

Fallback: если wmctrl нет → все функции False.
"""
from __future__ import annotations

import shutil
import subprocess

TIMEOUT = 3


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _wmctrl(*args: str) -> bool:
    if not _has("wmctrl"):
        return False
    try:
        r = subprocess.run(
            ["wmctrl", *args],
            capture_output=True, timeout=TIMEOUT,
        )
        return r.returncode == 0
    except Exception:
        return False


def move_window(name: str, x: int, y: int) -> bool:
    """Переместить окно по имени в координаты (x, y)."""
    if not name:
        return False
    return _wmctrl("-r", name, "-e", f"0,{x},{y},-1,-1")


def resize_window(name: str, w: int, h: int) -> bool:
    """Изменить размер окна (ширина, высота)."""
    if not name or w <= 0 or h <= 0:
        return False
    return _wmctrl("-r", name, "-e", f"0,-1,-1,{w},{h}")


def move_resize(name: str, x: int, y: int, w: int, h: int) -> bool:
    """Переместить + изменить размер одной командой."""
    if not name:
        return False
    return _wmctrl("-r", name, "-e", f"0,{x},{y},{w},{h}")


def minimize_window(name: str) -> bool:
    """Свернуть окно."""
    return _wmctrl("-r", name, "-b", "add,hidden") if name else False


def maximize_window(name: str) -> bool:
    """Развернуть окно."""
    return _wmctrl("-r", name, "-b", "add,maximized_vert,maximized_horz") if name else False


def close_window(name: str) -> bool:
    """Закрыть окно."""
    return _wmctrl("-c", name) if name else False


def center_window(name: str, screen_w: int = 1920, screen_h: int = 1080,
                  win_w: int = 800, win_h: int = 600) -> bool:
    """Центрировать окно на экране."""
    x = max(0, (screen_w - win_w) // 2)
    y = max(0, (screen_h - win_h) // 2)
    return move_resize(name, x, y, win_w, win_h)


def move_to_corner(name: str, corner: str,
                   screen_w: int = 1920, screen_h: int = 1080,
                   win_w: int = 960, win_h: int = 540) -> bool:
    """Переместить окно в угол: tl/tr/bl/br."""
    corners = {
        "tl": (0, 0),
        "tr": (screen_w - win_w, 0),
        "bl": (0, screen_h - win_h),
        "br": (screen_w - win_w, screen_h - win_h),
    }
    if corner not in corners:
        return False
    x, y = corners[corner]
    return move_resize(name, max(0, x), max(0, y), win_w, win_h)


def list_windows() -> list[str]:
    """Список имён всех окон."""
    if not _has("wmctrl"):
        return []
    try:
        r = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        names = []
        for line in r.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                names.append(parts[3])
        return names
    except Exception:
        return []


def is_available() -> bool:
    """wmctrl доступен?"""
    return _has("wmctrl")


__all__ = [
    "center_window",
    "close_window",
    "is_available",
    "list_windows",
    "maximize_window",
    "minimize_window",
    "move_resize",
    "move_to_corner",
    "move_window",
    "resize_window",
]


# === #139 Wayland-native (ydotool) ===

def _has_ydotool() -> bool:
    return shutil.which("ydotool") is not None


def _ydotool(*args: str) -> bool:
    if not _has_ydotool():
        return False
    try:
        r = subprocess.run(
            ["ydotool", *args],
            capture_output=True, timeout=TIMEOUT,
        )
        return r.returncode == 0
    except Exception:
        return False



def _has_ydotool() -> bool:
    return shutil.which("ydotool") is not None


def _ydotool(*args: str) -> bool:
    if not _has_ydotool():
        return False
    try:
        r = subprocess.run(
            ["ydotool", *args],
            capture_output=True, timeout=TIMEOUT,
        )
        return r.returncode == 0
    except Exception:
        return False


def mouse_click(x: int, y: int, button: str = "left") -> bool:
    """#139: клик мышью на координаты (Wayland-friendly)."""
    btn_map = {"left": "0xC0", "right": "0xC1", "middle": "0xC2"}
    code = btn_map.get(button, "0xC0")
    # Сначала движение, потом клик
    _ydotool("mousemove", "--absolute", "-x", str(x), "-y", str(y))
    return _ydotool("click", code)


def type_text_wayland(text: str) -> bool:
    """#139: ввод текста через ydotool (Wayland-friendly)."""
    if not text:
        return False
    return _ydotool("type", "--", text)


def is_wayland() -> bool:
    """Wayland ли сессия?"""
    import os
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


__all__ += ["is_wayland", "mouse_click", "type_text_wayland"]
