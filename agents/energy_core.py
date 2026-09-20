"""
Машинка 33: Энергетическое ядро (AgentEnergyCore)
"""

from agents.base import MicroAgent


class AgentEnergyCore(MicroAgent):
    def __init__(self):
        super().__init__("energy", "Энергетическое ядро")
        self.energy = 85

    def execute(self, command):
        if "энергия" in command:
            return f"⚡ Энергия: {self.energy}%"
        elif "заряди" in command:
            self.energy = 100
            return "🔋 Полностью заряжена!"
        return "⚡ Энергетическое ядро готово"
