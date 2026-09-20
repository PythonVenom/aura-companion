"""
Машинка Screen: Чтение экрана (AgentScreenReader)
"""

import os
import subprocess
from agents.base import MicroAgent


IS_WAYLAND = False


class AgentScreenReader(MicroAgent):
    def __init__(self):
        super().__init__("screen_reader", "Чтение экрана")
        self.ready = False
        self.screenshot_path = os.path.expanduser("~/aura_project/screen_tmp.png")

        if IS_WAYLAND:
            print("⚠️ ScreenReader: Wayland не поддерживается")
            return

        try:
            import pytesseract
            from PIL import Image
            import pyautogui
            self.pytesseract = pytesseract
            self.Image = Image
            self.pyautogui = pyautogui
            self.ready = True
            print("✅ ScreenReader загружен (OCR через tesseract)")
        except Exception as e:
            print(f"⚠️ ScreenReader ошибка: {e}")
            self.ready = False

    def _make_screenshot(self):
        try:
            self.pyautogui.screenshot().save(self.screenshot_path)
            return True
        except Exception as e:
            print(f"⚠️ Скриншот не удался: {e}")
            return False

    def _get_window_list(self):
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=3)
            windows = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        windows.append({
                            "id": parts[0],
                            "desktop": parts[1],
                            "title": parts[4]
                        })
            return windows
        except:
            return []

    def read_screen(self):
        if not self.ready:
            return "❌ ScreenReader не готов"
        if not self._make_screenshot():
            return "❌ Не удалось сделать скриншот"
        try:
            img = self.Image.open(self.screenshot_path)
            text = self.pytesseract.image_to_string(img, lang='rus+eng')
            os.unlink(self.screenshot_path)
            text = text.strip()
            if not text:
                return "👁️ На экране нет текста"
            return text
        except Exception as e:
            return f"❌ Ошибка OCR: {e}"

    def find_on_screen(self, query):
        if not self.ready:
            return "❌ ScreenReader не готов"
        if not self._make_screenshot():
            return "❌ Не удалось сделать скриншот"
        try:
            img = self.Image.open(self.screenshot_path)
            text = self.pytesseract.image_to_string(img, lang='rus+eng')
            os.unlink(self.screenshot_path)
            if not text:
                return "👁️ На экране нет текста"
            query_lower = query.lower()
            text_lower = text.lower()
            if query_lower in text_lower:
                idx = text_lower.find(query_lower)
                context = text[max(0, idx-50):idx+len(query)+50].strip()
                return f"✅ Нашла '{query}' на экране:\n...{context}..."
            else:
                return f"❌ Не нашла '{query}' на экране"
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def get_windows(self):
        windows = self._get_window_list()
        if not windows:
            return "🪟 Нет открытых окон"
        result = f"🪟 Открыто окон: {len(windows)}\n\n"
        for i, w in enumerate(windows, 1):
            result += f"{i}. {w['title'][:60]}\n"
        return result

    def execute(self, command):
        cmd = command.lower().strip()

        if 'какие окна' in cmd or 'что открыто' in cmd or 'список окон' in cmd:
            return self.get_windows()

        if 'прочитай экран' in cmd or 'что на экране' in cmd or 'прочитай' in cmd:
            text = self.read_screen()
            return f"👁️ На экране:\n\n{text[:800]}"

        if 'найди на экране' in cmd or 'найди текст' in cmd:
            query = cmd
            for word in ['найди на экране', 'найди текст', 'найди']:
                query = query.replace(word, '')
            query = query.strip()
            if not query:
                return "Что искать?"
            return self.find_on_screen(query)

        return "👁️ ScreenReader готов. Команды: какие окна, прочитай экран, найди на экране X"
