"""
Машинка 60: Контроллер приложений (AgentAppController)
"""

from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentAppController(MicroAgent):
    def __init__(self):
        super().__init__("app_controller", "Контроллер приложений")
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
                return f"✅ Кликнул по: {text}"
            return f"❌ Не нашёл на экране: {text}"
        except:
            return "❌ Не удалось кликнуть"

    def press_key(self, key):
        if not self.ready:
            return "❌ pyautogui не установлен (X11 only)"
        try:
            self.pyautogui.press(key)
            return f"✅ Нажал: {key}"
        except:
            return "❌ Не удалось нажать клавишу"

    def type_text(self, text):
        if not self.ready:
            return "❌ pyautogui не установлен (X11 only)"
        try:
            self.pyautogui.typewrite(text, interval=0.1)
            return f"✅ Набрал: {text}"
        except:
            return "❌ Не удалось набрать текст"

    def execute(self, command):
        cmd = command.lower()
        if 'кликни' in cmd:
            text = cmd.replace('кликни', '').strip()
            return self.click_on_text(text)
        elif 'нажми' in cmd:
            key = cmd.replace('нажми', '').strip()
            return self.press_key(key)
        return "Контроллер приложений готов. Скажи: кликни [текст], нажми [клавиша]"
