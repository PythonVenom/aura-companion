"""
Агент менеджера окон (AgentWindowManager).

Рабочие столы (wmctrl или qdbus для KDE), split screen.

Мигрирован из agents/window_manager.py (монолит, мёртвый по ADR-004).
Фазы:
- 6: порт как заготовка
- 7.2: подключён в bootstrap
- 7.3: KDE Plasma 6 через qdbus6
- 7.3.1: словесные числительные («два» → 2)
- 7.3.2: проверка результата (не врать про несуществующий стол)
         + «новый рабочий стол» → createDesktop

См. ADR-004.
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
    MODULE_ALWAYS = True

    KEYWORDS = (
        "рабочий стол",
        "раб стол",
        "следующий стол",
        "предыдущий стол",
        "новый стол",
        "новый рабочий стол",
        "создай стол",
        "создай рабочий стол",
        "раздели экран",
        "половина экрана",
        # Bug 26: обзор / окна
        "обзор",
        "покажи окна",
        "покажи все окна",
        "закрой обзор",
        "выйди из обзора",
    )

    QDBUS_BIN = "qdbus6"  # Plasma 6

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.is_kde = _detect_kde() and shutil.which(self.QDBUS_BIN) is not None
        self.ready = True

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        if any(kw in text for kw in self.KEYWORDS):
            return True
        # Bug 23: "стол 2", "стол два"
        import re as _re
        if _re.search(
            r"\bстол\s+(\d|один|два|три|четыре|пять|шесть|семь|восемь|девять|десять)",
            text,
        ):
            return True
        return False

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(agent_name=self.name)

        cmd = request.text.lower()

        # Bug 26: обзор (toggle)
        if "обзор" in cmd or "покажи окна" in cmd or "покажи все окна" in cmd:
            return AgentResponse.ok(text=self._overview(), agent_name=self.name)

        if "рабочий стол" in cmd or "раб стол" in cmd or "стол" in cmd:
            return AgentResponse.ok(text=self._desktop(cmd), agent_name=self.name)

        if "раздели экран" in cmd or "половина экрана" in cmd:
            return AgentResponse.ok(text=self._split_screen(), agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)

    def _overview(self) -> str:
        """Показать/скрыть обзор Plasma 6 (toggle через kglobalaccel)."""
        if not self.is_kde:
            return "Обзор поддерживается в KDE."
        for name in ("Overview", "Expose", "Toggle Overview", "ToggleOverview"):
            try:
                r = subprocess.run(
                    [self.QDBUS_BIN, "org.kde.kglobalaccel", "/component/kwin",
                     "org.kde.kglobalaccel.Component.invokeShortcut", name],
                    capture_output=True, text=True, timeout=3,
                )
                if r.returncode == 0 and "error" not in r.stderr.lower():
                    return "Обзор переключён."
            except Exception:
                continue
        return "Не удалось вызвать обзор."

    def _kde_call(self, method: str, *args: str) -> str:
        """Вызвать qdbus6. Вернуть stdout (строку). Пусто — ошибка."""
        cmd = [self.QDBUS_BIN, "org.kde.KWin", "/KWin", method, *args]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _kde_desktop_count(self) -> int:
        try:
            result = subprocess.run(
                [
                    self.QDBUS_BIN,
                    "org.kde.KWin",
                    "/VirtualDesktopManager",
                    "org.kde.KWin.VirtualDesktopManager.count",
                ],
                capture_output=True, text=True, timeout=3,
            )
            return int(result.stdout.strip())
        except Exception:
            return 0

    def _kde_create_desktop(self, name: str = "Новый") -> bool:
        """Создать новый стол в конце. qdbus возвращает void, проверяем по count."""
        before = self._kde_desktop_count()
        try:
            subprocess.run(
                [
                    self.QDBUS_BIN, "org.kde.KWin",
                    "/VirtualDesktopManager",
                    "org.kde.KWin.VirtualDesktopManager.createDesktop",
                    str(before), name,
                ],
                capture_output=True, text=True, timeout=3,
            )
        except Exception:
            return False
        after = self._kde_desktop_count()
        return after > before

    def _parse_number(self, cmd: str) -> int | None:
        """Извлечь номер стола: цифрой или словом."""
        nums = re.findall(r"\d+", cmd)
        if nums:
            return int(nums[0])
        for word, num in NUMBERS.items():
            if word in cmd:
                return num
        return None

    def _desktop(self, cmd: str) -> str:
        # Новый стол
        if "новый" in cmd or "создай" in cmd:
            if self.is_kde:
                if self._kde_create_desktop():
                    # Переключиться на только что созданный (последний)
                    self._kde_call("nextDesktop")
                    return "Создала новый рабочий стол."
                return "Не удалось создать рабочий стол."
            return "Создание столов поддерживается только в KDE."

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

        # «номер 2», «по счету 2», «второй», «стол два», «стол 2»
        target_maybe = self._parse_number(cmd)
        if "номер" in cmd or "по счету" in cmd or target_maybe is not None:
            target = target_maybe
            if target is None:
                return "Какой номер стола?"
            if self.is_kde:
                # Bug 23: setCurrentDesktop возвращает void (пусто) при успехе,
                # "false" — при несуществующем столе. target — 1-based.
                result = self._kde_call("setCurrentDesktop", str(target))
                if result.lower() == "false":
                    return f"Стол {target} не существует."
                return f"Переместила на рабочий стол {target}."
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
