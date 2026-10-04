"""
Агент переключения фокуса (AgentFocusSwitch).

Фокус на окно по имени (X11, wmctrl).
Рабочее пространство: открыть Code + Firefox, разместить по половинам.

Мигрирован из agents/focus_switch.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- IS_WAYLAND — автоопределение (было False заглушкой)
- Логика find_and_focus / _focus_work НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.
"""

from __future__ import annotations

import os
import subprocess
import time

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentFocusSwitch(BaseAgent):
    """Переключение фокуса между окнами."""

    name = "focus_switch"

    KNOWN_WINDOWS = {
        "вк": "VK",
        "вконтакте": "VK",
        "ютуб": "YouTube",
        "браузер": "Firefox",
        "firefox": "Firefox",
        "vlc": "VLC",
        "код": "Code OSS",
        "code": "Code OSS",
        "среда разработки": "Code OSS",
        "терминал": "GNOME Terminal",
    }

    APP_PATHS = {
        "VK": "firefox",
        "Firefox": "firefox",
        "YouTube": "firefox",
        "VLC": "vlc",
        "Code OSS": "code-oss",
        "GNOME Terminal": "gnome-terminal",
    }

    KEYWORDS = (
        "фокус на",
        "переключись на",
        "переключи на",
        "рабочее пространство",
        "рабочий проект",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = True

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        if any(kw in text for kw in ("рабочее пространство", "рабочий проект")):
            return True
        if "фокус" in text or "переключ" in text:
            return any(k in text for k in self.KNOWN_WINDOWS)
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        cmd = request.text.lower()

        if "рабочее пространство" in cmd or "рабочий проект" in cmd:
            # Bug 41: отключено до стабильности (см. INBOX, v1.0.1)
            # self._focus_work()
            return AgentResponse.ok(
                text="Режим работы отключён (в доработке)",
                agent_name=self.name,
            )

        for key, app_name in self.KNOWN_WINDOWS.items():
            if key in cmd:
                return AgentResponse.ok(
                    text=self.find_and_focus(app_name),
                    agent_name=self.name,
                )

        return AgentResponse.not_handled(agent_name=self.name)

    def find_and_focus(self, app_name: str) -> str:
        if self.is_wayland:
            app = self.APP_PATHS.get(app_name, "firefox")
            subprocess.Popen(
                [app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return f"Открываю: {app_name}"

        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.split("\\n"):
                if app_name.lower() in line.lower():
                    window_id = line.split()[0]
                    subprocess.run(
                        ["wmctrl", "-i", "-a", window_id], check=False,
                    )
                    return f"Фокус перенесён на: {app_name}"

            app_path = self.APP_PATHS.get(app_name, "firefox")
            subprocess.Popen(
                [app_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return f"Окно {app_name} не найдено, открываю."
        except Exception:
            return f"❌ Не удалось перенести фокус на {app_name}"

    def _focus_work(self) -> None:
        try:
            subprocess.Popen(
                ["code-oss"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            subprocess.Popen(
                ["firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(2)
            if self.is_wayland:
                return
            try:
                result = subprocess.run(
                    ["xdotool", "getdisplaygeometry"],
                    capture_output=True, text=True, timeout=3,
                )
                w, h = map(int, result.stdout.split())
                half_w = w // 2
                subprocess.run(
                    ["xdotool", "search", "--name", "Code", "windowmove", "0", "0"],
                    check=False,
                )
                subprocess.run(
                    ["xdotool", "search", "--name", "Code", "windowsize", str(half_w), str(h)],
                    check=False,
                )
                subprocess.run(
                    ["xdotool", "search", "--name", "Firefox", "windowmove", str(half_w), "0"],
                    check=False,
                )
                subprocess.run(
                    ["xdotool", "search", "--name", "Firefox", "windowsize", str(half_w), str(h)],
                    check=False,
                )
            except Exception:
                pass
        except Exception:
            pass


__all__ = ["AgentFocusSwitch"]
