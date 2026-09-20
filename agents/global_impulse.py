"""
Машинка 41: Глобальный импульс (AgentGlobalImpulse)
"""

from agents.base import MicroAgent


class AgentGlobalImpulse(MicroAgent):
    def __init__(self):
        super().__init__("global", "Глобальный импульс")
        self.network = {"nodes": ["ядро", "спутник", "облако"]}

    def execute(self, command):
        if "импульс" in command:
            return "⚡ Импульс отправлен!"
        elif "синхронизируй" in command:
            return "🔄 Все узлы синхронизированы!"
        return "⚡ Глобальный импульс готов"
