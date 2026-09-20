"""
Машинка 58: Мультивселенная (AgentParallelUniverse)
"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from agents.base import MicroAgent


IS_WAYLAND = False  # будет переопределено из aura_core


class AgentParallelUniverse(MicroAgent):
    """Запускает фоновые потоки анализа, пока вы работаете"""

    def __init__(self):
        super().__init__("parallel_universe", "Мультивселенная")
        self.threads = []
        self.running = False
        self.last_analysis = None

    def _analyze_browser_tabs(self):
        if IS_WAYLAND:
            return "⚠️ Недоступно в Wayland"
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            tabs = [line.split(None, 4)[4] for line in result.stdout.split('\n') if line.strip()]
            for tab in tabs:
                if 'youtube' in tab.lower() or 'spotify' in tab.lower():
                    self.last_analysis = f"🎵 В фоне работает: {tab[:40]}"
                    return self.last_analysis
            self.last_analysis = "📊 Все вкладки анализированы, медиа не найдено"
            return self.last_analysis
        except:
            return "⚠️ Не смогла проанализировать вкладки"

    def _monitor_background(self):
        while self.running:
            self._analyze_browser_tabs()
            time.sleep(5)

    def start(self):
        if self.running:
            return "⚡ Мультивселенная уже работает"
        self.running = True
        thread = ThreadPoolExecutor(max_workers=1)
        self.threads.append(thread.submit(self._monitor_background))
        return "⚡ Мультивселенная запущена! Аура анализирует всё в фоне."

    def stop(self):
        self.running = False
        return "⏹️ Мультивселенная остановлена"

    def get_insight(self):
        if self.last_analysis:
            return self.last_analysis
        return "🧠 Мультивселенная думает..."

    def execute(self, command):
        if 'запусти мультивселенную' in command or 'параллельный' in command:
            return self.start()
        elif 'останови мультивселенную' in command:
            return self.stop()
        elif 'что в фоне' in command or 'анализ' in command:
            return self.get_insight()
        return "🌌 Мультивселенная готова. Команды:\n- запусти мультивселенную\n- что в фоне"
