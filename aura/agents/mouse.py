"""
Агент управления мышью (AgentMouse).

click по тексту/координатам, type, press через pyautogui.

Мигрирован из agents/mouse.py (монолит, мёртвый по ADR-004).
Изменения: контракт BaseAgent, автоопределение Wayland, guard.

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004. X11-only (pyautogui).
"""

from __future__ import annotations

import os

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentMouse(BaseAgent):
    """Управление мышью и клавиатурой."""

    name = "mouse"

    KEYWORDS = (
        "кликни по",
        "кликни на",
        "кликни",
        "нажми клавишу",
        "набери",
        "введи текст",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = False
        self.pyautogui = None
        if not self.is_wayland:
            try:
                import pyautogui
                self.pyautogui = pyautogui
                self.ready = True
            except Exception:
                self.ready = False

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(agent_name=self.name)

        if not self.ready:
            return AgentResponse.ok(
                text="❌ pyautogui не установлен (X11 only)",
                agent_name=self.name,
            )

        cmd = request.text.lower()

        if "кликни" in cmd:
            target = self._extract_after(cmd, ("кликни по", "кликни на", "кликни"))
            if target:
                return AgentResponse.ok(
                    text=self.click_on_text(target), agent_name=self.name,
                )
            return AgentResponse.ok(
                text="Что кликнуть?", agent_name=self.name,
            )

        if "нажми клавишу" in cmd:
            key = self._extract_after(cmd, ("нажми клавишу",))
            if key:
                return AgentResponse.ok(
                    text=self.press_key(key), agent_name=self.name,
                )
            return AgentResponse.ok(
                text="Какую клавишу?", agent_name=self.name,
            )

        if "набери" in cmd or "введи текст" in cmd:
            text = self._extract_after(cmd, ("набери", "введи текст"))
            if text:
                return AgentResponse.ok(
                    text=self.type_text(text), agent_name=self.name,
                )
            return AgentResponse.ok(
                text="Что набрать?", agent_name=self.name,
            )

        return AgentResponse.not_handled(agent_name=self.name)

    def click_on_text(self, text: str) -> str:
        try:
            location = self.pyautogui.locateOnScreen(text, confidence=0.8)
            if location:
                self.pyautogui.click(location)
                return f"✅ Кликнула по: {text}"
            return f"❌ Не нашла на экране: {text}"
        except Exception:
            return "❌ Не удалось кликнуть"

    def click_at(self, x: int, y: int) -> str:
        try:
            self.pyautogui.click(x, y)
            return f"✅ Кликнула по координатам: ({x}, {y})"
        except Exception:
            return "❌ Не удалось кликнуть"

    def type_text(self, text: str) -> str:
        try:
            self.pyautogui.typewrite(text, interval=0.1)
            return f"✅ Набрала: {text}"
        except Exception:
            return "❌ Не удалось набрать текст"

    def press_key(self, key: str) -> str:
        try:
            self.pyautogui.press(key)
            return f"✅ Нажала: {key}"
        except Exception:
            return "❌ Не удалось нажать клавишу"

    def _extract_after(self, cmd: str, prefixes: tuple) -> str:
        for p in prefixes:
            if p in cmd:
                rest = cmd.replace(p, "", 1).strip()
                return rest
        return ""


__all__ = ["AgentMouse"]
