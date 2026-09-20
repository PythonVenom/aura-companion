"""
Машинка 49: Гибридное ядро (AgentHybridCore)
"""

import subprocess
from agents.base import MicroAgent


class AgentHybridCore(MicroAgent):
    def __init__(self):
        super().__init__("hybrid_core", "Гибридное ядро")
        self.ready = True
        self.current_mode = "offline"

    def check_network(self):
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                self.current_mode = "online"
                return True
            else:
                self.current_mode = "offline"
                return False
        except:
            self.current_mode = "offline"
            return False

    def execute(self, command):
        if 'интернет' in command or 'вайфай' in command or 'wifi' in command or 'подключись' in command:
            if self.check_network():
                return "🌐 Wi-Fi обнаружен. Подключилась к сети. Режим: гибридный."
            else:
                return "📴 Wi-Fi не обнаружен. Работаю офлайн на локальных моделях."
        elif 'статус' in command:
            return f"🖥️ Режим работы: {self.current_mode}"
        return "🔧 Гибридное ядро готово. Команды: подключись, статус"
