"""
Машинка 06: Авто-оповещение (AgentUpdateNotifier)
"""

import subprocess
from agents.base import MicroAgent


class AgentUpdateNotifier(MicroAgent):
    def __init__(self):
        super().__init__("update_notifier", "Авто-оповещение об обновлениях")
        self.last_count = 0
        self.interval = 7200

    def check(self):
        try:
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            return int(count) if count else 0
        except:
            return 0

    def notify(self):
        count = self.check()
        if count == 0:
            return "✅ Обновлений нет"

        if count == self.last_count:
            return "ℹ️ Обновлений не прибавилось"

        self.last_count = count
        msg = f"Создатель, доступно {count} обновлений. Обновить?"

        speaker = self._get_speaker()
        if speaker:
            speaker.say(msg)

        return f"⚠️ Внимание: {count} обновлений"

    def _get_speaker(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('speaker')
        return None

    def execute(self, command=None):
        return self.notify()
