"""
Машинка 65: Умный браузер (AgentSmartBrowser)
"""

import subprocess
import time
from agents.base import MicroAgent


class AgentSmartBrowser(MicroAgent):
    def __init__(self):
        super().__init__("smart_browser", "Умный браузер")
        self.ready = True
        self.urls = {
            'вк': 'https://vk.com/',
            'рутуб': 'https://rutube.ru/',
            'ютуб': 'https://www.youtube.com/',
            'музыка вк': 'https://vk.com/audios',
            'новости': 'https://news.google.com/'
        }

    def _open_new_tab(self, url):
        """Открывает URL в новой вкладке (работает и в Wayland)"""
        try:
            subprocess.Popen(['firefox', '--new-tab', url],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            return f"✅ Открыла: {url[:60]}"
        except:
            return "❌ Не удалось открыть вкладку"

    def _open_new_window(self, url):
        try:
            subprocess.Popen(['firefox', '--new-window', url],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Открыла окно: {url[:60]}"
        except:
            return "❌ Не удалось открыть окно"

    def execute(self, command):
        cmd = command.lower()
        if 'выведи вк' in cmd or 'открой вк' in cmd or ('вк' in cmd and 'музык' not in cmd):
            return self._open_new_tab(self.urls['вк'])
        if 'выведи рутуб' in cmd or 'рутуб' in cmd:
            return self._open_new_tab(self.urls['рутуб'])
        if 'выведи ютуб' in cmd or 'ютуб' in cmd:
            return self._open_new_tab(self.urls['ютуб'])
        if 'музыка вк' in cmd or 'вк музыка' in cmd:
            return self._open_new_tab(self.urls['музыка вк'])
        return "🔍 Умный браузер готов. Скажи: 'открой вк', 'открой рутуб', 'открой ютуб'"
