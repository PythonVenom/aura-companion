"""
Агент менеджера окон (AgentWindowManager).

Рабочие столы (wmctrl или qdbus для KDE), split screen.

Мигрирован из agents/window_manager.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Автоопределение Wayland (_detect_wayland) и KDE (_detect_kde)
- Поддержка KDE Plasma 6 через qdbus6 (Фаза 7.3)
- Парсер словесных числительных («два» → 2) — T-one распознаёт словами

Подключён в Фазе 7.2. См. ADR-004.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def _detect_kde() -> bool:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return "kde" in desktop or "plasma" in desktop


# Числительные словами: T-one часто распознаёт "два", "три" вместо цифр
NUMBERS = {
    "один": 1, "одна": 1, "первый": 1, "первом": 1, "первого": 1,
    "два": 2, "две": 2, "второй": 2, "втором": 2, "второго": 2,
    "три": 3, "третий": 3, "третьем": 3, "третьего": 3,
    "четыре": 4, "четвертый": 4, "четвёртый": 4, "четвертом": 4,
    "пять": 5, "пятый": 5, "пятом": 5,
    "шесть": 6, "шестой": 6,
    "семь": 7, "седьмой": 7,
    "восемь": 8, "восьмой": 8,
    "девять": 9, "девятый": 9,
    "десять": 10, "десятый": 10,
}


class AgentWindowManager(BaseAgent):
    """Менеджер окон: столы, split."""

    name = "window_manager"

    KEYWORDS = (
        "рабочий стол",
        "раб стол",
        "следующий стол",
        "предыдущий стол",
        "раздели экран",
        "половина экрана",
    )

    QDBUS_BIN = "qdbus6"  # Plasma 6

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.is_kde = _detect_kde() and shutil.which(self.QDBUS_BIN) is not None
        self.ready = True

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(agent_name=self.name)

        cmd = request.text.lower()

        if "рабочий стол" in cmd or "раб стол" in cmd or "стол" in cmd:
            return AgentResponse.ok(text=self._desktop(cmd), agent_name=self.name)

        if "раздели экран" in cmd or "половина экрана" in cmd:
            return AgentResponse.ok(text=self._split_screen(), agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)

    def _kde_call(self, method: str, arg: str | None = None) -> bool:
        cmd = [self.QDBUS_BIN, "org.kde.KWin", "/KWin", method]
        if arg is not None:
            cmd.append(arg)
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            return True
        except Exception:
            return False

    def _parse_number(self, cmd: str) -> int | None:
        """Извлечь номер стола: цифрой или словом."""
        # Сначала цифры
        nums = re.findall(r"\d+", cmd)
        if nums:
            return int(nums[0])
        # Потом слова
        for word, num in NUMBERS.items():
            if word in cmd:
                return num
        return None

    def _desktop(self, cmd: str) -> str:
        if "следующий" in cmd or "след" in cmd:
            if self.is_kde:
                self._kde_call("nextDesktop")
            elif not self.is_wayland:
                subprocess.run(["wmctrl", "-s", "+1"], check=False)
            return "Переместила на следующий рабочий стол."

        if "предыдущий" in cmd or "назад" in cmd:
            if self.is_kde:
                self._kde_call("previousDesktop")
            elif not self.is_wayland:
                subprocess.run(["wmctrl", "-s", "-1"], check=False)
            return "Переместила на предыдущий рабочий стол."

        if "номер" in cmd or "по счету" in cmd:
            target = self._parse_number(cmd)
            if target is None:
                return "Какой номер стола?"
            if self.is_kde:
                self._kde_call("setCurrentDesktop", str(target))
            elif not self.is_wayland:
                subprocess.run(["wmctrl", "-s", str(target - 1)], check=False)
            return f"Переместила на рабочий стол {target}."

        return "Не поняла команду стола."

    def _focus_window(self, app_name: str, friendly_name: str) -> str:
        if self.is_wayland:
            return "⚠️ Фокус на окно недоступен в Wayland"
        try:
            result = subprocess.run(
                ["wmctrl", "-l"], capture_output=True, text=True, timeout=3,
            )
            for line in result.stdout.split("\n"):
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
        if self.is_wayland:
            return "⚠️ Split screen недоступен в Wayland"
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
