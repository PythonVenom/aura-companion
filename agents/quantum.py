"""
Машинка 26: Квантовый вычислитель (AgentQuantumComputer)
"""

from agents.base import MicroAgent


class AgentQuantumComputer(MicroAgent):
    def __init__(self):
        super().__init__("quantum", "Квантовый вычислитель")
        self.qubits = 8

    def execute(self, command):
        if "кубиты" in command:
            if "+" in command:
                self.qubits = min(64, self.qubits + 4)
            elif "-" in command:
                self.qubits = max(2, self.qubits - 4)
            return f"⚛️ Кубиты: {self.qubits}"
        elif "оптимизируй" in command:
            return "⚛️ Оптимальное решение найдено!"
        return "⚛️ Квантовый вычислитель готов"
