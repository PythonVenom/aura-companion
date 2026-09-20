"""
Машинка 59: Переключение фокуса (AgentFocusSwitch)
"""

import subprocess
import time
from agents.base import MicroAgent


IS_WAYLAND = False  # переопределяется из aura_core


class AgentFocusSwitch(MicroAgent):
    def __init__(self):
        super().__init__("focus_switch", "Переключение фокуса")
        self.ready = True
        self.known_windows = {
            "вк": "VK",
            "вконтакте": "VK",
            "ютуб": "YouTube",
            "браузер": "Firefox",
            "vlc": "VLC",
            "код": "Code OSS",
            "среда разработки": "Code OSS",
            "терминал": "GNOME Terminal",
            "работа": "Work",
            "проект": "Project"
        }

    def find_and_focus(self, app_name):
        if IS_WAYLAND:
            paths = {
                "VK": "firefox", "Firefox": "firefox", "YouTube": "firefox",
                "VLC": "vlc", "Code OSS": "code-oss", "GNOME Terminal": "gnome-terminal",
                "Work": "code-oss", "Project": "code-oss"
            }
            app = paths.get(app_name, "firefox")
            subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Открываю: {app_name}"

        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if app_name.lower() in line.lower():
                    window_id = line.split()[0]
                    subprocess.run(['wmctrl', '-i', '-a', window_id], check=False)
                    return f"Фокус перенесен на: {app_name}"

            subprocess.Popen([self._get_app_path(app_name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Окно {app_name} не найдено, открываю."
        except:
            return f"❌ Не удалось перенести фокус на {app_name}"

    def _get_app_path(self, app_name):
        paths = {
            "VK": "firefox",
            "Firefox": "firefox",
            "YouTube": "firefox",
            "VLC": "vlc",
            "Code OSS": "code-oss",
            "GNOME Terminal": "gnome-terminal",
            "Work": "code-oss",
            "Project": "code-oss"
        }
        return paths.get(app_name, "firefox")

    def execute(self, command):
        cmd = command.lower()

        if 'работа' in cmd or 'проект' in cmd:
            self._focus_work()
            return "Открыла рабочее пространство: код + браузер"

        for key, app_name in self.known_windows.items():
            if key in cmd:
                return self.find_and_focus(app_name)

        return "❌ Не знаю, на что переключить фокус. Скажи: фокус на ВК, фокус на браузер, фокус на работу"

    def _focus_work(self):
        try:
            subprocess.Popen(['code-oss'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(['firefox'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            if IS_WAYLAND:
                return True
            try:
                result = subprocess.run(['xdotool', 'getdisplaygeometry'], capture_output=True, text=True)
                w, h = map(int, result.stdout.split())
                half_w = w // 2
                subprocess.run(['xdotool', 'search', '--name', 'Code', 'windowmove', str(0), '0'], check=False)
                subprocess.run(['xdotool', 'search', '--name', 'Code', 'windowsize', str(half_w), str(h)], check=False)
                subprocess.run(['xdotool', 'search', '--name', 'Firefox', 'windowmove', str(half_w), '0'], check=False)
                subprocess.run(['xdotool', 'search', '--name', 'Firefox', 'windowsize', str(half_w), str(h)], check=False)
            except:
                pass
            return True
        except:
            return False
