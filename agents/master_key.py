"""
Машинка 27: Мастер-ключ (AgentMasterKey)
"""

from agents.base import MicroAgent


class AgentMasterKey(MicroAgent):
    def __init__(self):
        super().__init__("master_key", "Мастер-ключ")
        self.systems = []

    def execute(self, command):
        if "разблокируй" in command:
            return "🔑 Все системы разблокированы!"
        elif "заблокируй" in command:
            return "🔒 Все системы заблокированы!"
        return "🔑 Мастер-ключ готов"
