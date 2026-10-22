from aura.env.detect import get_display_server
import subprocess

class UIAdapter:
    """Абстракция для управления окнами (X11 vs Wayland)."""
    def __init__(self):
        self.server = get_display_server()
        print(f"🖥️ UI Adapter инициализирован для: {self.server.upper()}")

    def open_app(self, app_name: str):
        if self.server == "x11":
            return self._x11_open(app_name)
        elif self.server == "wayland":
            return self._wayland_open(app_name)
        return "Неизвестный сервер"

    def _x11_open(self, app_name: str):
        subprocess.Popen(app_name.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Запущено через X11: {app_name}"

    def _wayland_open(self, app_name: str):
        return "В Wayland пока не реализовано"
