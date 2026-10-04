"""TrayIcon — SNI трей через pystray (ADR-081).

StatusNotifierItem (SNI) — стандарт D-Bus, работает в 90% Linux DE:
GNOME (с расширением), KDE Plasma, Cinnamon, XFCE, MATE, LXQt,
Budgie, i3/Sway/Hyprland (через waybar/polybar).

Почему pystray:
- Кроссплатформенный (Linux, Windows, macOS)
- Тонкая обёртка над SNI/AppIndicator
- Не требует GTK/Qt напрямую (использует backend)
"""
from __future__ import annotations
import subprocess
import urllib.request
import json
from pathlib import Path


MENU_ITEMS = [
    # AURA_SOS_TRAY_V1 — паническая кнопка (T018)
    ("sos", "🆘 SOS — вызвать помощь"),
    ("sep_sos", None),
    ("status", "Статус"),
    ("sep1", None),
    ("pause", "⏸ Пауза"),
    ("resume", "▶ Продолжить"),
    ("sep2", None),
    ("web", "🌐 Web UI"),
    ("kill", "✕ Kill Aura"),
    ("sep3", None),
    ("quit", "Выход"),
]


STATE_COLORS = {
    "idle": "#5a7a9a",
    "listening": "#f5c542",
    "thinking": "#f58742",
    "speaking": "#42c55a",
    "paused": "#666666",
    "error": "#c54242",
    "unknown": "#888888",
}


def state_to_color(state: str) -> str:
    return STATE_COLORS.get(state, STATE_COLORS["unknown"])


def make_icon_image(color: str = "#888888", size: int = 64):
    """Простая иконка — круг с цветом статуса."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 6
    d.ellipse([pad, pad, size - pad, size - pad], fill=color)
    return img


class TrayIcon:
    def __init__(self, api_url: str = "http://127.0.0.1:8765", _icon=None):
        self.api_url = api_url.rstrip("/")
        self._icon = _icon
        self.enabled = _icon is not None
        self._last_state = "unknown"

    def status_url(self) -> str:
        return f"{self.api_url}/status"

    def chat_url(self) -> str:
        return f"{self.api_url}/chat"

    def pause_command(self) -> str:
        return "python3 ~/aura_project/scripts/aura_ctl.py pause"

    def resume_command(self) -> str:
        return "python3 ~/aura_project/scripts/aura_ctl.py resume"

    def kill_command(self) -> str:
        return "python3 ~/aura_project/scripts/aura_ctl.py kill"

    def _get_state(self) -> str:
        try:
            with urllib.request.urlopen(self.status_url(), timeout=2) as r:
                data = json.loads(r.read())
                return data.get("state", "unknown")
        except Exception:
            return "unknown"

    def _run(self, cmd: str) -> None:
        try:
            subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    def _open_web(self) -> None:
        self._run(f"xdg-open {self.api_url}/ui")

    def build_menu(self) -> list:
        """Список (label, action) для pystray.Menu."""
        items = []
        for key, label in MENU_ITEMS:
            if label is None:
                items.append(("---", None))
                continue
            if key == "status":
                items.append((f"● {self._last_state}", None))
            elif key == "pause":
                items.append((label, lambda: self._run(self.pause_command())))
            elif key == "resume":
                items.append((label, lambda: self._run(self.resume_command())))
            elif key == "kill":
                items.append((label, lambda: self._run(self.kill_command())))
            elif key == "web":
                items.append((label, self._open_web))
            elif key == "quit":
                items.append((label, self._quit))
        return items

    def _quit(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass

    def refresh_state(self) -> str:
        s = self._get_state()
        self._last_state = s
        if self._icon is not None:
            try:
                from PIL import Image
                self._icon.icon = make_icon_image(state_to_color(s))
                self._icon.title = f"Aura: {s}"
                self._icon.update_menu()
            except Exception:
                pass
        return s

    def run(self) -> None:
        """Запустить трей (блокирующий)."""
        try:
            import pystray
        except ImportError:
            print("pystray не установлен: pip install pystray Pillow")
            return
        color = state_to_color(self._last_state)
        image = make_icon_image(color)
        menu_items = []
        for label, action in self.build_menu():
            if action is None:
                menu_items.append(pystray.Menu.SEPARATOR)
            else:
                menu_items.append(pystray.MenuItem(label, action))
        icon = pystray.Icon(
            "aura", image, f"Aura: {self._last_state}",
            menu=pystray.Menu(*menu_items),
        )
        self._icon = icon
        self.enabled = True
        icon.run()


__all__ = ["TrayIcon", "MENU_ITEMS", "STATE_COLORS", "state_to_color", "make_icon_image"]
