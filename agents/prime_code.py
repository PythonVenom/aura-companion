"""
Машинка 42: Первоначальный код (AgentPrimeCode)
"""

from agents.base import MicroAgent


class AgentPrimeCode(MicroAgent):
    def __init__(self):
        super().__init__("prime", "Первоначальный код")
        self.laws = {"единство": "Всё есть одно", "сознание": "Всё есть сознание"}

    def execute(self, command):
        if "закон" in command:
            return "📜 Закон единства: Всё есть одно"
        elif "дешифруй" in command:
            return "🔓 Декодировано: АУРА"
        return "⚛️ Первоначальный код готов"
