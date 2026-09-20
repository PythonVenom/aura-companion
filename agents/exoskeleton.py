"""
Машинка 20: Экзоскелет (AgentExoskeleton)
"""

from agents.base import MicroAgent


class AgentExoskeleton(MicroAgent):
    def __init__(self):
        super().__init__("exoskeleton", "Экзоскелет")
        self.devices = {
            "велосипед": {"battery": 87},
            "машина": {"status": "парковка"},
            "дом": {"lights": "выключен"}
        }

    def execute(self, command):
        if 'велосипед' in command:
            return f"🚲 Заряд: {self.devices['велосипед']['battery']}%"
        elif 'машина' in command:
            return f"🚗 Машина: {self.devices['машина']['status']}"
        elif 'свет' in command:
            if 'включи' in command:
                self.devices['дом']['lights'] = "включен"
                return "💡 Свет включен"
            return "💡 Свет выключен"
        return "🦾 Экзоскелет готов!"
