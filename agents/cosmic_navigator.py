"""
Машинка 36: Космический навигатор (AgentCosmicNavigator)
"""

from agents.base import MicroAgent


class AgentCosmicNavigator(MicroAgent):
    def __init__(self):
        super().__init__("cosmic", "Космический навигатор")
        self.stars = ["Сириус", "Полярная", "Вега"]

    def execute(self, command):
        if "найди" in command:
            return "⭐ Сириус: расстояние 8.6 св. лет"
        elif "звезды" in command:
            return f"⭐ Звёзды: {', '.join(self.stars)}"
        return "🚀 Космический навигатор готов"
