"""
Машинка 57: История окон (AgentContextMemory)
"""

import subprocess
import time
from agents.base import MicroAgent


IS_WAYLAND = False  # будет переопределено из aura_core


class AgentContextMemory(MicroAgent):
    """Запоминает, какие окна открыты, когда, и что они делают"""

    def __init__(self):
        super().__init__("context_memory", "История окон")
        self.window_history = []
        self.last_played_source = None

    def scan_windows(self):
        if IS_WAYLAND:
            return False
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            current_time = time.time()
            self.window_history = []
            for line in lines:
                if line.strip():
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        window_id = parts[0]
                        title = parts[4]
                        self.window_history.append({
                            "id": window_id,
                            "title": title,
                            "opened_at": current_time,
                            "process": self._detect_process(title)
                        })
            return True
        except:
            return False

    def _detect_process(self, title):
        if 'youtube' in title.lower() or 'ютуб' in title.lower():
            return 'youtube'
        elif 'vlc' in title.lower() or 'media' in title.lower():
            return 'vlc'
        elif 'spotify' in title.lower():
            return 'spotify'
        elif 'firefox' in title.lower() or 'браузер' in title.lower():
            return 'browser'
        elif 'code' in title.lower() or 'код' in title.lower():
            return 'code'
        return 'unknown'

    def get_last_media_source(self):
        self.scan_windows()
        for window in reversed(self.window_history):
            if window['process'] in ['youtube', 'vlc', 'spotify', 'browser']:
                self.last_played_source = window['process']
                return window
        return None

    def sort_by_time(self):
        return sorted(self.window_history, key=lambda x: x['opened_at'])

    def execute(self, command):
        if IS_WAYLAND:
            return "❌ История окон недоступна в Wayland"
        self.scan_windows()
        if 'окна' in command or 'история' in command:
            windows = self.sort_by_time()
            result = "🪟 ОТКРЫТЫЕ ОКНА:\n"
            for w in windows:
                age = int(time.time() - w['opened_at'])
                result += f"  ├─ {w['title'][:40]} ({age} сек назад, {w['process']})\n"
            return result
        elif 'источник' in command or 'музыка' in command:
            source = self.get_last_media_source()
            if source:
                return f"🎵 Последний источник: {source['title'][:50]}"
            return "❌ Нет активного источника звука"
        return "📊 История окон работает"
