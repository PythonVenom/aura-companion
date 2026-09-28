"""
Агент управления окнами.

Работает через wmctrl (X11).
Умеет: фокус, fullscreen, minimize, close, список окон.

По науке:
- Изолирован (только subprocess)
- Тестируем (mock для wmctrl)
- Не знает про AuraCore
"""

from __future__ import annotations

import subprocess

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentWindowControl(BaseAgent):
    """
    Агент управления окнами X11.

    Обрабатывает:
    - "фокус на <окно>" / "переключись на <окно>" → focus
    - "разверни окно" / "на весь экран" → fullscreen
    - "сверни окно" / "минимизируй" → minimize
    - "закрой окно" → close active
    - "список окон" → list windows
    """

    name = "window_control"
    MODULE_ALWAYS = True

    FOCUS_KEYWORDS = ("фокус", "переключись", "активируй", "на передний план")
    FULLSCREEN_KEYWORDS = ("разверни", "на весь экран", "fullscreen", "во весь экран")
    MINIMIZE_KEYWORDS = ("сверни", "минимизируй", "minimize")
    CLOSE_KEYWORDS = ("закрой окно", "закрыть окно")
    LIST_KEYWORDS = ("список окон", "какие окна", "открытые окна")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        keywords = (
            self.FOCUS_KEYWORDS
            + self.FULLSCREEN_KEYWORDS
            + self.MINIMIZE_KEYWORDS
            + self.CLOSE_KEYWORDS
            + self.LIST_KEYWORDS
        )
        return any(kw in text for kw in keywords)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.LIST_KEYWORDS):
            return AgentResponse.ok(self.list_windows(), self.name)

        if any(kw in text for kw in self.CLOSE_KEYWORDS):
            return AgentResponse.ok(self.close_active(), self.name, silent=True)

        if any(kw in text for kw in self.FULLSCREEN_KEYWORDS):
            return AgentResponse.ok(self.fullscreen_active(), self.name, silent=True)

        if any(kw in text for kw in self.MINIMIZE_KEYWORDS):
            return AgentResponse.ok(self.minimize_active(), self.name, silent=True)

        if any(kw in text for kw in self.FOCUS_KEYWORDS):
            target = self._extract_target(text)
            if not target:
                return AgentResponse.ok("На какое окно переключиться?", self.name)
            return AgentResponse.ok(self.focus_window(target), self.name, silent=True)

        return AgentResponse.not_handled(self.name)

    # --- Внутренние методы ---

    def _extract_target(self, text: str) -> str:
        for kw in self.FOCUS_KEYWORDS:
            if kw in text:
                target = text.split(kw, 1)[1].strip()
                target = target.replace("на ", "").strip()
                return target
        return ""

    def list_windows(self) -> str:
        try:
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                check=False,
            )
            lines = [l for l in result.stdout.split("\n") if l.strip()]
            if not lines:
                return "🪟 Открытых окон нет"
            out = [f"🪟 Открыто окон: {len(lines)}"]
            for i, line in enumerate(lines[:15], 1):
                parts = line.split(None, 3)
                title = parts[3] if len(parts) >= 4 else "?"
                out.append(f"{i}. {title}")
            return "\n".join(out)
        except Exception as e:
            return f"❌ Ошибка wmctrl: {e}"

    def focus_window(self, target: str) -> str:
        try:
            result = subprocess.run(
                ["wmctrl", "-a", target],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return f"🪟 Фокус на: {target}"
            return f"❌ Окно '{target}' не найдено"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def fullscreen_active(self) -> str:
        try:
            subprocess.run(
                ["wmctrl", "-r", ":ACTIVE:", "-b", "toggle,fullscreen"],
                check=False,
            )
            return "🪟 Полноэкранный режим переключён"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def minimize_active(self) -> str:
        try:
            subprocess.run(
                ["xdotool", "getactivewindow", "windowminimize"],
                check=False,
            )
            return "🪟 Окно свёрнуто"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def close_active(self) -> str:
        try:
            subprocess.run(
                ["wmctrl", "-c", ":ACTIVE:"],
                check=False,
            )
            return "🪟 Окно закрыто"
        except Exception as e:
            return f"❌ Ошибка: {e}"


__all__ = ["AgentWindowControl"]
