"""
Машинка 22: Временная петля (AgentTimeLoop)
"""

import time
from agents.base import MicroAgent


class AgentTimeLoop(MicroAgent):
    def __init__(self):
        super().__init__("time_loop", "Временная петля")
        self.reminders = []

    def execute(self, command):
        if 'напомни' in command:
            text = command.replace('напомни', '').strip()
            self.reminders.append({"text": text, "time": time.time() + 300})
            return f"⏰ Напомню через 5 минут: {text}"
        elif 'проверь' in command:
            return "⏰ Активных напоминаний нет"
        return "🔄 Временная петля готова"
