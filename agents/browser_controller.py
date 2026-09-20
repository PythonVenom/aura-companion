"""
Машинка 66: Контроллер браузера (AgentBrowserController)
"""

import subprocess
from agents.base import MicroAgent


class AgentBrowserController(MicroAgent):
    def __init__(self):
        super().__init__("browser_controller", "Контроллер браузера")
        self.ready = True
        self.urls = {
            'вк': 'https://vk.com/',
            'музыка вк': 'https://vk.com/audios',
            'подобрано': 'https://vk.com/audios?block=recommendations',
            'ютуб': 'https://www.youtube.com/',
            'рутуб': 'https://rutube.ru/',
            'новости': 'https://news.google.com/'
        }

    def open_url(self, url):
        """Открывает URL в Firefox"""
        try:
            subprocess.Popen(['firefox', '--new-tab', url],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Открыла URL: {url[:60]}"
        except:
            return "❌ Не удалось открыть URL"

    def execute(self, command):
        cmd = command.lower()

        if 'вк' in cmd or 'вконтакте' in cmd:
            if 'музыка' in cmd or 'аудио' in cmd:
                return self.open_url(self.urls['музыка вк'])
            if 'подобрано' in cmd:
                return self.open_url(self.urls['подобрано'])
            return self.open_url(self.urls['вк'])

        if 'ютуб' in cmd or 'youtube' in cmd:
            return self.open_url(self.urls['ютуб'])

        if 'рутуб' in cmd or 'rutube' in cmd:
            return self.open_url(self.urls['рутуб'])

        if 'новости' in cmd:
            return self.open_url(self.urls['новости'])

        return "🌐 Контроллер браузера готов"
