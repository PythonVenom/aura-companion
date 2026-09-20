"""
Машинка 64: Следящий за обновлениями (AgentUpdateWatcher)
"""

import subprocess
from agents.base import MicroAgent


class AgentUpdateWatcher(MicroAgent):
    def __init__(self):
        super().__init__("update_watcher", "Следящий за обновлениями")
        self.timer = 0

    def check_updates(self):
        result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
        count = result.stdout.strip()
        if count and int(count) > 0:
            return f"⚠️ Доступно {count} обновлений. Обновить?"
        return "✅ Обновлений нет"

    def execute(self, command):
        if 'следи за обновлениями' in command or 'проверь обновления' in command:
            return self.check_updates()
        return "🔔 Следящий за обновлениями готов"
