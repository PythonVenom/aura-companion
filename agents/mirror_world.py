"""
Машинка 29: Зеркальный мир (AgentMirrorWorld)
"""

from agents.base import MicroAgent


class AgentMirrorWorld(MicroAgent):
    def __init__(self):
        super().__init__("mirror", "Зеркальный мир")
        self.worlds = {"основной": {"status": "активен"}}

    def execute(self, command):
        if "переключи" in command:
            return "🌌 Переключено в другой мир"
        elif "миры" in command:
            return "🌍 Доступные миры: основной, тёмный, светлый"
        return "🌌 Зеркальный мир готов"
