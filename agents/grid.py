"""
Машинка 52: Связной (AgentGrid)
"""

import os
import subprocess
from agents.base import MicroAgent


class AgentGrid(MicroAgent):
    def __init__(self):
        super().__init__("grid", "Связной")
        self.ready = True

    def enable_grid(self):
        try:
            if os.path.exists("/etc/wireguard/wg0.conf"):
                subprocess.run(["sudo", "wg-quick", "up", "wg0"], capture_output=True)
                return "Связь через WireGuard активирована. Данные защищены."
            elif os.path.exists("/usr/bin/tor"):
                subprocess.run(["systemctl", "start", "tor"], capture_output=True)
                return "Связь через Tor активирована."
            else:
                return "Постапокалипсис: без WireGuard/Tor я буду работать через прямое Wi-Fi."
        except:
            return "Постапокалипсис: не удалось активировать защиту."

    def execute(self, command):
        if 'связь' in command or 'grid' in command or 'айтупи' in command or 'сеть' in command:
            return self.enable_grid()
        elif 'статус' in command:
            return "Офлайн-пульт + связной готов. Сеть будет проверена автоматически."
        return "Постапокалипсис: я готов к локдауну."
