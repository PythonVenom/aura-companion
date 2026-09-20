"""
Машинка 14: Окна (AgentWindowManager)
"""

import subprocess
import re
from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentWindowManager(MicroAgent):
    def __init__(self):
        super().__init__("window_manager", "Менеджер окон")
        self.ready = True

    def execute(self, command):
        cmd = command.lower()

        if IS_WAYLAND:
            return "❌ Управление окнами недоступно в Wayland"

        if 'рабочий стол' in cmd or 'раб стол' in cmd or 'стол' in cmd:
            if 'следующий' in cmd or 'след' in cmd:
                subprocess.run(['wmctrl', '-s', '+1'], check=False)
                return "Переместила на следующий рабочий стол."
            elif 'предыдущий' in cmd or 'назад' in cmd:
                subprocess.run(['wmctrl', '-s', '-1'], check=False)
                return "Переместила на предыдущий рабочий стол."
            elif 'номер' in cmd or 'по счету' in cmd:
                nums = re.findall(r'\d+', cmd)
                if nums:
                    desk_num = int(nums[0]) - 1
                    subprocess.run(['wmctrl', '-s', str(desk_num)], check=False)
                    return f"Переместила на рабочий стол {nums[0]}."
                else:
                    return "Какой номер стола?"

        if 'выдели' in cmd or 'среда разработки' in cmd or 'код' in cmd:
            return self._focus_window("code-oss", "среда разработки")
        elif 'браузер' in cmd:
            return self._focus_window("firefox", "браузер")

        if 'половина экрана' in cmd or 'раздели экран' in cmd:
            return self._split_screen()

        if 'закрой' in cmd:
            return self._close_window(cmd)

        return "Не поняла команду управления окнами."

    def _focus_window(self, app_name, friendly_name):
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            lines = result.stdout.split('\n')

            for line in lines:
                if app_name in line:
                    window_id = line.split()[0]
                    subprocess.run(['wmctrl', '-i', '-a', window_id], check=False)
                    return f"Сфокусировалась на {friendly_name}."

            subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Окно {friendly_name} не найдено, открываю."
        except:
            return f"Не удалось сфокусироваться на {friendly_name}."

    def _split_screen(self):
        try:
            result = subprocess.run(['xdotool', 'getdisplaygeometry'], capture_output=True, text=True)
            w, h = map(int, result.stdout.split())
            half_w = w // 2

            self._focus_window("code-oss", "среда разработки")
            subprocess.run(['xdotool', 'windowsize', '--sync', 'active', str(half_w), str(h)], check=False)
            subprocess.run(['xdotool', 'windowmove', '--sync', 'active', '0', '0'], check=False)

            self._focus_window("firefox", "браузер")
            subprocess.run(['xdotool', 'windowsize', '--sync', 'active', str(half_w), str(h)], check=False)
            subprocess.run(['xdotool', 'windowmove', '--sync', 'active', str(half_w), '0'], check=False)

            return "Разделила экран: слева среда разработки, справа браузер."
        except:
            return "Не удалось разделить экран."

    def _close_window(self, cmd):
        try:
            app_name = None
            if 'браузер' in cmd:
                app_name = 'firefox'
            elif 'среда' in cmd or 'код' in cmd:
                app_name = 'code-oss'
            elif 'терминал' in cmd:
                app_name = 'gnome-terminal'

            if app_name:
                subprocess.run(['pkill', '-f', app_name], check=False)
                return f"Закрыла: {app_name}"
            return "Не знаю, что закрыть."
        except:
            return "Не удалось закрыть окно."
