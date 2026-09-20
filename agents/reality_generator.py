"""
Машинка 35: Генератор реальности (AgentRealityGenerator)
"""

from agents.base import MicroAgent


class AgentRealityGenerator(MicroAgent):
    def __init__(self):
        super().__init__("reality", "Генератор реальности")
        self.worlds = []

    def execute(self, command):
        if "создай мир" in command:
            self.worlds.append({"name": "новый мир"})
            return "🌍 Новый мир создан!"
        elif "симулируй" in command:
            return "🔄 Симуляция завершена: успех!"
        return "🌍 Генератор реальности готов"
