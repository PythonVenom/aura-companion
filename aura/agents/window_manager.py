"""
Агент менеджера окон (AgentWindowManager).

Рабочие столы (wmctrl -s), фокус на окно, split screen, закрытие.

Мигрирован из agents/window_manager.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Автоопределение Wayland (_detect_wayland)
- Логика _focus_window / _split_screen / _close_window НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.

ВОЗМОЖНЫЙ ДУБЛЬ: focus_switch умеет фокус. window_control (мигрирован)
умеет close/focus/fullscreen. Этот агент добавляет рабочие столы и
split screen. Решить при подключении.
"""

from __future__ import annotations

import os
import re
import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentWindowManager(BaseAgent):
    """Менеджер окон: столы, split, закрытие."""

    name = "window_manager"

    KEYWORDS = (
        "рабочий стол",
        "раб стол",
        "следующий стол",
        "предыдущий стол",
        "раздели экран",
        "половина экрана",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = not self.is_wayland

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if self.is_wayland:
            return AgentResponse.ok(
                text="❌ Управление окнами недоступно в Wayland",
                agent_name=self.name,
            )

        cmd = request.text.lower()

        if "рабочий стол" in cmd or "раб стол" in cmd or "стол" in cmd:
            return AgentResponse.ok(text=self._desktop(cmd), agent_name=self.name)

        if "раздели экран" in cmd or "половина экрана" in cmd:
            return AgentResponse.ok(text=self._split_screen(), agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)

    def _desktop(self, cmd: str) -> str:
        if "следующий" in cmd or "след" in cmd:
            subprocess.run(["wmctrl", "-s", "+1"], check=False)
            return "Переместила на следующий рабочий стол."
        if "предыдущий" in cmd or "назад" in cmd:
            subprocess.run(["wmctrl", "-s", "-1"], check=False)
            return "Переместила на предыдущий рабочий стол."
        if "номер" in cmd or "по счету" in cmd:
            nums = re.findall(r"\d+", cmd)
            if nums:
                desk_num = int(nums[0]) - 1
                subprocess.run(["wmctrl", "-s", str(desk_num)], check=False)
                return f"Переместила на рабочий стол {nums[0]}."
            return "Какой номер стола?"
        return "Не поняла команду стола."

    def _focus_window(self, app_name: str, friendly_name: str) -> str:
        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.split("\\n"):
                if app_name in line:
                    window_id = line.split()[0]
                    subprocess.run(
                        ["wmctrl", "-i", "-a", window_id], check=False,
                    )
                    return f"Сфокусировалась на {friendly_name}."
            subprocess.Popen(
                [app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return f"Окно {friendly_name} не найдено, открываю."
        except Exception:
            return f"Не удалось сфокусироваться на {friendly_name}."

    def _split_screen(self) -> str:
        try:
            result = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True, text=True, timeout=3,
            )
            w, h = map(int, result.stdout.split())
            half_w = w // 2

            self._focus_window("code-oss", "среда разработки")
            subprocess.run(
                ["xdotool", "windowsize", "--sync", "active", str(half_w), str(h)],
                check=False,
            )
            subprocess.run(
                ["xdotool", "windowmove", "--sync", "active", "0", "0"],
                check=False,
            )

            self._focus_window("firefox", "браузер")
            subprocess.run(
                ["xdotool", "windowsize", "--sync", "active", str(half_w), str(h)],
                check=False,
            )
            subprocess.run(
                ["xdotool", "windowmove", "--sync", "active", str(half_w), "0"],
                check=False,
            )

            return "Разделила экран: слева среда разработки, справа браузер."
        except Exception:
            return "Не удалось разделить экран."


__all__ = ["AgentWindowManager"]
