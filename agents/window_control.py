"""
Машинка Window: Управление окнами (AgentWindowControl)
Фокусировка, полный экран, свернуть, развернуть, перемещение.
"""

import subprocess
import re
from agents.base import MicroAgent


class AgentWindowControl(MicroAgent):
    def __init__(self):
        super().__init__("window_control", "Управление окнами")
        self.ready = True
        print("✅ WindowControl загружен")

    def _get_windows(self):
        """Список окон"""
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
                            "host": parts[2],
                            "title": parts[4]
                        })
            return windows
        except:
            return []

    def _find_window(self, query):
        """Найти окно по имени"""
        query_lower = query.lower().strip()
        if not query_lower:
            return None

        windows = self._get_windows()

        # Точное совпадение
        for w in windows:
            if query_lower == w['title'].lower():
                return w

        # Частичное
        for w in windows:
            if query_lower in w['title'].lower():
                return w

        return None

    def focus_window(self, query):
        """Переключиться на окно"""
        window = self._find_window(query)
        if not window:
            return f"❌ Окно '{query}' не найдено"

        try:
            subprocess.run(['wmctrl', '-i', '-a', window['id']], check=False)
            return f"✅ Переключилась на: {window['title'][:50]}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def close_window(self, query):
        """Закрыть окно"""
        window = self._find_window(query)
        if not window:
            return f"❌ Окно '{query}' не найдено"

        try:
            subprocess.run(['wmctrl', '-i', '-c', window['id']], check=False)
            return f"✅ Закрыла: {window['title'][:50]}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def fullscreen(self):
        """Полный экран для активного окна"""
        try:
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'toggle,fullscreen'], check=False)
            return "✅ Полный экран"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def minimize_all(self):
        """Свернуть все окна (KDE Plasma)"""
        try:
            # KDE Plasma — Show Desktop через qdbus
            result = subprocess.run(
                ['qdbus', 'org.kde.kglobalaccel', '/component/kwin',
                 'org.kde.kglobalaccel.Component.invokeShortcut', 'Show Desktop'],
                check=False, capture_output=True
            )
            if result.returncode == 0:
                return "✅ Свернула все окна"
            # Fallback — xdotool
            subprocess.run(['xdotool', 'key', 'super+d'], check=False)
            return "✅ Свернула все окна"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def maximize(self):
        """Развернуть активное окно"""
        try:
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'add,maximized_vert,maximized_horz'], check=False)
            return "✅ Развернула окно"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def unmaximize(self):
        """Восстановить активное окно"""
        try:
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b', 'remove,maximized_vert,maximized_horz'], check=False)
            return "✅ Восстановила окно"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def move_to_desktop(self, num):
        """Переместить активное окно на рабочий стол"""
        try:
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-t', str(num - 1)], check=False)
            return f"✅ Переместила на рабочий стол {num}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def list_windows(self):
        """Список окон"""
        windows = self._get_windows()
        if not windows:
            return "🪟 Нет окон"
        result = f"🪟 Окон: {len(windows)}\n\n"
        for i, w in enumerate(windows, 1):
            result += f"{i}. {w['title'][:60]}\n"
        return result

    def execute(self, command):
        cmd = command.lower().strip()

        # Переключиться на окно
        if 'переключись' in cmd or 'переключи' in cmd or 'фокус на' in cmd:
            query = cmd
            for word in ['переключись на', 'переключи на', 'переключись', 'переключи', 'фокус на']:
                query = query.replace(word, '')
            query = query.strip()
            if not query:
                return "На что переключиться?"
            return self.focus_window(query)

        # Закрыть окно
        if 'закрой окно' in cmd or 'закрой' in cmd and 'окно' in cmd:
            query = cmd.replace('закрой окно', '').replace('закрой', '').strip()
            if not query:
                return "Какое окно закрыть?"
            return self.close_window(query)

        # Полный экран
        if 'полный экран' in cmd or 'на весь экран' in cmd:
            return self.fullscreen()

        # Свернуть всё
        if 'сверни всё' in cmd or 'свернуть все' in cmd or 'покажи рабочий стол' in cmd:
            return self.minimize_all()

        # Развернуть
        if 'разверни' in cmd or 'максимизируй' in cmd:
            return self.maximize()

        # Восстановить
        if 'восстанови окно' in cmd or 'уменьши окно' in cmd:
            return self.unmaximize()

        # Переместить на рабочий стол
        if 'на рабочий стол' in cmd:
            nums = re.findall(r'\d+', cmd)
            if nums:
                return self.move_to_desktop(int(nums[0]))
            return "На какой рабочий стол?"

        # Список окон
        if 'список окон' in cmd or 'какие окна' in cmd:
            return self.list_windows()

        return "🪟 WindowControl готов. Команды: переключись на X, закрой X, полный экран, сверни всё"
