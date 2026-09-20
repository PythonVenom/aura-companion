"""
Машинка 05: Установка (AgentUpgrader)
"""

import os
import subprocess
from agents.base import MicroAgent


class AgentUpgrader(MicroAgent):
    def __init__(self):
        super().__init__("upgrader", "Устанавливает обновления")
        self.waiting_for_confirmation = False
        self.confirmation_attempts = 0

    def execute(self, _):
        try:
            lock = '/var/lib/pacman/db.lck'
            if os.path.exists(lock):
                try: os.remove(lock)
                except: pass

            result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            if not count or int(count) == 0:
                return "✅ Обновлений нет"

            speaker = self._get_speaker()
            if speaker:
                speaker.say(f"Доступно {count} обновлений. Для подтверждения скажи: да аура обнови")

            self.waiting_for_confirmation = True
            self.confirmation_attempts = 0
            return "⚠️ Ожидание подтверждения..."

        except Exception as e:
            return f"❌ Ошибка: {e}"

    def confirm(self):
        try:
            lock = '/var/lib/pacman/db.lck'
            if os.path.exists(lock):
                try: os.remove(lock)
                except: pass

            speaker = self._get_speaker()
            if speaker:
                speaker.say("✅ Подтверждено. Начинаю обновление...")

            result = subprocess.run("sudo pacman -Syu --noconfirm", shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return "✅ Система обновлена!"
            else:
                return f"❌ Ошибка: {result.stderr}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def increment_attempts(self):
        self.confirmation_attempts += 1
        if self.confirmation_attempts > 3:
            self.waiting_for_confirmation = False
            return True
        return False

    def _get_speaker(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('speaker')
        return None
