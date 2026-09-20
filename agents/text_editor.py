"""
Машинка 16: Редактор текста (AgentTextEditor)
"""

from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentTextEditor(MicroAgent):
    def __init__(self):
        super().__init__("text_editor", "Редактор текста")
        self.ready = False
        if not IS_WAYLAND:
            try:
                import pyautogui
                import pyperclip
                self.pyautogui = pyautogui
                self.pyperclip = pyperclip
                self.ready = True
            except:
                pass

    def execute(self, command):
        if not self.ready:
            return "❌ Установи pyautogui и pyperclip (X11)"

        cmd = command.lower()

        if 'выдели' in cmd or 'выделить' in cmd:
            self.pyautogui.hotkey('ctrl', 'a')
            return "Выделила всё."
        elif 'копируй' in cmd or 'копировать' in cmd:
            self.pyautogui.hotkey('ctrl', 'c')
            return "Скопировала."
        elif 'вставь' in cmd or 'вставить' in cmd:
            self.pyautogui.hotkey('ctrl', 'v')
            return "Вставила."
        elif 'сохрани' in cmd or 'сохранить' in cmd:
            self.pyautogui.hotkey('ctrl', 's')
            return "Сохранила."
        elif 'отмени' in cmd or 'отменить' in cmd:
            self.pyautogui.hotkey('ctrl', 'z')
            return "Отменила."
        return "Не поняла команду для текста."
