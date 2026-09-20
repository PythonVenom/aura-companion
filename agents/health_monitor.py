"""
Машинка 25: Здоровье (AgentHealthMonitor)
"""

from agents.base import MicroAgent


class AgentHealthMonitor(MicroAgent):
    def __init__(self):
        super().__init__("health", "Монитор здоровья")
        self.heart_rate = 72

    def execute(self, command):
        if "пульс" in command:
            return f"❤️ Пульс: {self.heart_rate} уд/мин"
        elif "статус" in command:
            return "🩺 Всё в норме!"
        return "🩺 Монитор здоровья готов"
