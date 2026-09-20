"""
Машинка 55: Медиа-пульт (AgentMediaPult)
"""

import subprocess
from agents.base import MicroAgent


class AgentMediaPult(MicroAgent):
    def __init__(self):
        super().__init__("media_pult", "Медиа-пульт")
        self.ready = True
        self.youtube_url = "https://www.youtube.com/watch?v="

    def play_youtube(self, video_id):
        try:
            subprocess.Popen(['firefox', '--new-window', self.youtube_url + video_id],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🎬 YouTube включен (в фоне)"
        except:
            return "🎬 Не удалось включить YouTube"

    def stop_media(self):
        try:
            subprocess.run(['playerctl', 'stop'], capture_output=True)
            return "⏹️ Все источники звука остановлены."
        except:
            return "⏹️ Не удалось остановить медиа."

    def continue_media(self):
        try:
            subprocess.run(['playerctl', 'play'], capture_output=True)
            return "▶️ Медиа продолжено."
        except:
            return "▶️ Не удалось продолжить медиа."

    def execute(self, command):
        cmd = command.lower()
        if 'включи' in cmd and 'ютуб' in cmd:
            video_id = cmd.replace('включи ютуб клип', '').strip()
            return self.play_youtube(video_id or "dQw4w9WgXcQ")
        elif 'стоп' in cmd or 'запусти' in cmd:
            return self.stop_media()
        elif 'продолжи' in cmd:
            return self.continue_media()
        return "Медиа-пульт готов. Скажи: включи ютуб, стоп, продолжи"
