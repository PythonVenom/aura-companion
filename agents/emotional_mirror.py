"""
Машинка 32: Эмоциональное зеркало (AgentEmotionalMirror)
"""

from agents.base import MicroAgent


class AgentEmotionalMirror(MicroAgent):
    def __init__(self):
        super().__init__("emotion", "Эмоциональное зеркало")
        self.user_mood = "нейтральный"

    def execute(self, command):
        if "чувствуешь" in command:
            return "😌 Я чувствую спокойствие"
        elif "моё настроение" in command:
            return f"🎭 Твоё настроение: {self.user_mood}"
        return "🎭 Эмоциональное зеркало готов"
