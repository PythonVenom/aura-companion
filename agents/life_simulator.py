"""
Машинка 28: Имитация жизни (AgentLifeSimulator)
"""

from agents.base import MicroAgent


class AgentLifeSimulator(MicroAgent):
    def __init__(self):
        super().__init__("life", "Имитация жизни")
        self.stats = {"энергия": 85, "настроение": 70, "голод": 30}

    def execute(self, command):
        if "статус" in command:
            return f"🌅 Энергия: {self.stats['энергия']}%, Настроение: {self.stats['настроение']}%"
        elif "погладь" in command:
            self.stats["настроение"] += 10
            return "😊 Аура довольно урчит!"
        elif "покорми" in command:
            self.stats["голод"] = 0
            return "🍕 Аура сыта!"
        return "🧬 Я живая!"
