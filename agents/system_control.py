"""
Машинка 09: Приложения (AgentSystemControl)
"""

import subprocess
from agents.base import MicroAgent


class AgentSystemControl(MicroAgent):
    def __init__(self):
        super().__init__("system", "Управляет ПК")

    def execute(self, command):
        apps = {'браузер': 'firefox', 'терминал': 'gnome-terminal', 'код': 'code-oss'}
        for name, cmd in apps.items():
            if name in command and 'закрой' not in command:
                subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Открыл: {name}"
            elif name in command and 'закрой' in command:
                subprocess.Popen(['pkill', '-f', cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Закрыл: {name}"
        return "❌ Не поняла"
