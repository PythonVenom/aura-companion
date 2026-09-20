"""
Машинка 67: Управление мышкой (AgentMouse)
"""

from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentMouse(MicroAgent):
    def __init__(self):
        super().__init__("mouse", "Управление мышкой")
        self.ready = False
        if not IS_WAYLAND:
            try:
                import pyautogui
                self.pyautogui = pyautogui
                self.ready = True
            except:
                pass

    def click_on_text(self, text):
        if not self.ready:
            return "❌ pyautogui не установлен (X11 only)"
        try:
            location = self.pyautogui.locateOnScreen(text, confidence=0.8)
            if location:
                self.pyautogui.click(location)
                return f"✅ Кликнула по: {text}"
            return f"❌ Не нашла на экране: {text}"
        except:
            return "❌ Не удалось кликнуть"

    def click_at(self, x, y):
        if not self.ready:
            return "❌ pyautogui не установлен"
        try:
            self.pyautogui.click(x, y)
            return f"✅ Кликнула по координатам: ({x}, {y})"
        except:
            return "❌ Не удалось кликнуть"

    def type_text(self, text):
        if not self.ready:
            return "❌ pyautogui не установлен"
        try:
            self.pyautogui.typewrite(text, interval=0.1)
            return f"✅ Набрала: {text}"
        except:
            return "❌ Не удалось набрать текст"

    def press_key(self, key):
        if not self.ready:
            return "❌ pyautogui не установлен"
        try:
            self.pyautogui.press(key)
            return f"✅ Нажала: {key}"
        except:
            return "❌ Не удалось нажать клавишу"

    def execute(self, command):
        cmd = command.lower()
        if 'кликни' in cmd:
            text = cmd.replace('кликни', '').strip()
            return self.click_on_text(text)
        elif 'нажми' in cmd:
            key = cmd.replace('нажми', '').strip()
            return self.press_key(key)
        elif 'набери' in cmd or 'введи' in cmd:
            text = cmd.replace('набери', '').replace('введи', '').strip()
            return self.type_text(text)
        return "🖱️ Я умею: кликни [текст], нажми [клавиша], набери [текст]"
