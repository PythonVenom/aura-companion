"""
Машинка Power: Системные команды (AgentPower)
Выключение, перезагрузка, sleep, lock, logout, hibernate.
"""

import subprocess
import os
from agents.base import MicroAgent


class AgentPower(MicroAgent):
    def __init__(self):
        super().__init__("power", "Системные команды")
        self.ready = True
        print("✅ Power загружен")

    def shutdown(self):
        try:
            subprocess.Popen(['systemctl', 'poweroff'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "💤 Выключаю ПК. До встречи!"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def reboot(self):
        try:
            subprocess.Popen(['systemctl', 'reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🔄 Перезагружаю ПК. Скоро вернусь!"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def suspend(self):
        try:
            subprocess.Popen(['systemctl', 'suspend'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "😴 Ухожу в сон. Разбуди, когда нужно."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def lock(self):
        try:
            subprocess.Popen(['loginctl', 'lock-session'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🔒 Экран заблокирован."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def logout(self):
        try:
            user = os.environ.get('USER', 'pythonvenom')
            subprocess.Popen(['loginctl', 'terminate-user', user], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "🚪 Выхожу из системы."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def hibernate(self):
        try:
            subprocess.Popen(['systemctl', 'hibernate'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "💤 Ухожу в гибернацию."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def execute(self, command):
        cmd = command.lower().strip()

        if 'выключи' in cmd or 'poweroff' in cmd or 'shutdown' in cmd:
            return self.shutdown()
        if 'перезагрузи' in cmd or 'reboot' in cmd or 'restart' in cmd:
            return self.reboot()
        if 'спящий' in cmd or 'сон' in cmd or 'suspend' in cmd or 'sleep' in cmd:
            return self.suspend()
        if 'заблокируй' in cmd or 'блок' in cmd or 'lock' in cmd:
            return self.lock()
        if 'выйди из системы' in cmd or 'logout' in cmd or 'log out' in cmd:
            return self.logout()
        if 'гибернация' in cmd or 'hibernate' in cmd:
            return self.hibernate()

        return "💻 Power готов. Команды: выключи ПК, перезагрузи, спящий режим, заблокируй"
