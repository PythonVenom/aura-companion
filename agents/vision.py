"""
Машинка 08: Зрение (AgentVision)
"""

import os
from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentVision(MicroAgent):
    def __init__(self):
        super().__init__("vision", "Зрение Ауры")
        self.ready = False
        if not IS_WAYLAND:
            try:
                import pyautogui
                self.pyautogui = pyautogui
                self.ready = True
            except:
                pass

    def screenshot(self):
        if not self.ready:
            return "❌ Зрение недоступно (Wayland)"
        try:
            path = os.path.expanduser("~/aura_project/screenshot.png")
            self.pyautogui.screenshot().save(path)
            return f"📸 Скриншот: {path}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def execute(self, command):
        if 'скриншот' in command:
            return self.screenshot()
        return "👁️ Я вижу экран"
