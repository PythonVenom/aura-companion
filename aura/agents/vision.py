"""
Агент зрения (AgentVision).

Скриншот экрана через pyautogui.

Мигрирован из agents/vision.py (монолит, мёртвый по ADR-004).
Изменения: контракт BaseAgent, автоопределение Wayland.

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004. X11-only (pyautogui).
"""

from __future__ import annotations

import os

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentVision(BaseAgent):
    """Скриншот через pyautogui."""

    name = "vision"

    KEYWORDS = ("скриншот", "сделай снимок", "снимок экрана")

    SCREENSHOT_PATH = os.path.expanduser("~/aura_project/screenshot.png")

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
                text="❌ Зрение недоступно (Wayland или нет pyautogui)",
                agent_name=self.name,
            )

        try:
            self.pyautogui.screenshot().save(self.SCREENSHOT_PATH)
            return AgentResponse.ok(
                text=f"📸 Скриншот: {self.SCREENSHOT_PATH}",
                agent_name=self.name,
            )
        except Exception as e:
            return AgentResponse.ok(
                text=f"❌ Ошибка: {e}",
                agent_name=self.name,
            )


__all__ = ["AgentVision"]
