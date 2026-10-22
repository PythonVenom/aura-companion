"""
Агент редактора текста (AgentTextEditor).

Управление текстом через pyautogui: выделить, копировать, вставить,
сохранить, отменить (Ctrl+A/C/V/S/Z).

Мигрирован из agents/text_editor.py (монолит, мёртвый по ADR-004).
Изменения:
- Контракт BaseAgent: can_handle / handle
- Автоопределение Wayland (_detect_wayland)
- Guard can_handle в начале handle
- Логика execute → handle НЕ менялась

Портирован как заготовка (Фаза 6). НЕ подключён к bootstrap.
См. ADR-004.

X11-only (pyautogui). В Wayland — ready=False.
"""

from __future__ import annotations

import os

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


def _detect_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


class AgentTextEditor(BaseAgent):
    """Ctrl+A/C/V/S/Z через pyautogui."""

    name = "text_editor"

    KEYWORDS = (
        "выдели всё",
        "выделить всё",
        "копируй",
        "копировать",
        "вставь",
        "вставить",
        "сохрани файл",
        "сохранить файл",
        "отмени",
        "отменить",
    )

    def __init__(self) -> None:
        self.is_wayland = _detect_wayland()
        self.ready = False
        self.pyautogui = None
        self.pyperclip = None
        if not self.is_wayland:
            try:
                import pyautogui
                import pyperclip
                self.pyautogui = pyautogui
                self.pyperclip = pyperclip
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
                text="❌ Установи pyautogui и pyperclip (X11)",
                agent_name=self.name,
            )

        cmd = request.text.lower()

        if "выдели" in cmd or "выделить" in cmd:
            self.pyautogui.hotkey("ctrl", "a")
            return AgentResponse.ok(text="Выделила всё.", agent_name=self.name)

        if "копируй" in cmd or "копировать" in cmd:
            self.pyautogui.hotkey("ctrl", "c")
            return AgentResponse.ok(text="Скопировала.", agent_name=self.name)

        if "вставь" in cmd or "вставить" in cmd:
            self.pyautogui.hotkey("ctrl", "v")
            return AgentResponse.ok(text="Вставила.", agent_name=self.name)

        if "сохрани" in cmd or "сохранить" in cmd:
            self.pyautogui.hotkey("ctrl", "s")
            return AgentResponse.ok(text="Сохранила.", agent_name=self.name)

        if "отмени" in cmd or "отменить" in cmd:
            self.pyautogui.hotkey("ctrl", "z")
            return AgentResponse.ok(text="Отменила.", agent_name=self.name)

        return AgentResponse.not_handled(agent_name=self.name)


__all__ = ["AgentTextEditor"]
