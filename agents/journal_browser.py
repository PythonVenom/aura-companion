"""
Машинка 68: Умный журнал браузера (AgentJournalBrowser)
"""

import subprocess
import time
from agents.base import MicroAgent


class AgentJournalBrowser(MicroAgent):
    def __init__(self):
        super().__init__("journal_browser", "Умный журнал браузера")
        self.ready = True

    def restore_session(self):
        """Открывает Firefox с восстановлением сессии"""
        try:
            subprocess.Popen(['firefox'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            return "✅ Восстановила Firefox"
        except:
            return "❌ Не удалось восстановить Firefox"

    def execute(self, command):
        cmd = command.lower()
        if 'восстанови' in cmd or 'журнал' in cmd:
            return self.restore_session()
        return "📋 Умный журнал готов. Скажи: 'восстанови браузер'"
