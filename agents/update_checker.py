"""
Машинка 04: Обновления (AgentUpdateChecker)
"""

import subprocess
from agents.base import MicroAgent


class AgentUpdateChecker(MicroAgent):
    def __init__(self):
        super().__init__("updates", "Проверяет обновления")

    def execute(self, _):
        try:
            result = subprocess.run(
                "checkupdates 2>/dev/null | wc -l",
                shell=True, capture_output=True, text=True
            )
            count = result.stdout.strip()
            if count and int(count) > 0:
                return f"⚠️ Доступно {count} обновлений"
            return "✅ Система обновлена"
        except:
            return "❌ Не удалось проверить обновления"
