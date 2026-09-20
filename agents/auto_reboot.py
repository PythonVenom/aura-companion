"""
Машинка 47: Авто-перезагрузка (AgentAutoReboot)
"""

import os
import subprocess
from agents.base import MicroAgent


class AgentAutoReboot(MicroAgent):
    def __init__(self):
        super().__init__("auto_reboot", "Авто-перезагрузка")
        self.ready = True
        self.reboot_script = os.path.expanduser("~/aura_project/reboot_aura.sh")

    def reboot(self):
        try:
            with open(self.reboot_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("sleep 10\n")
                f.write("cd /home/pythonvenom/aura_project\n")
                f.write("source venv/bin/activate\n")
                f.write("python3 aura_core.py\n")
            os.chmod(self.reboot_script, 0o755)
            subprocess.run(["sudo", "systemctl", "reboot"], capture_output=True)
            return "💤 Перезагружаюсь. Встретимся через 10 секунд!"
        except:
            return "❌ Не удалось перезагрузить"

    def execute(self, command):
        if 'перезагруз' in command or 'перезагрузка' in command:
            return self.reboot()
        return "Авто-перезагрузка готов. Скажи: перезагрузи систему"
