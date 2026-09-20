"""
Машинка 56: Умный переключатель (AgentInterrupt)
"""

import subprocess
from agents.base import MicroAgent


class AgentInterrupt(MicroAgent):
    def __init__(self):
        super().__init__("interrupt", "Умный переключатель")
        self.ready = True

    def stop_all(self):
        try:
            subprocess.run(['playerctl', 'stop'], capture_output=True)
            return "⏹️ Все активные звуки остановлены."
        except:
            return "⏹️ Не удалось остановить звуки."

    def continue_all(self):
        try:
            subprocess.run(['playerctl', 'play'], capture_output=True)
            return "▶️ Все активные звуки продлены."
        except:
            return "▶️ Не удалось продлить звуки."

    def execute(self, command):
        if 'стоп' in command or 'тормози' in command:
            return self.stop_all()
        elif 'продолжи' in command:
            return self.continue_all()
        return "Умный переключатель готов."
