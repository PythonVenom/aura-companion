"""
Машинка 54: Умный дом (AgentSmartHome)
"""

import subprocess
from agents.base import MicroAgent


class AgentSmartHome(MicroAgent):
    def __init__(self):
        super().__init__("smart_home", "Умный дом")
        self.ready = True
        self.home = {
            "kitchen": False,
            "bathroom": False,
            "living_room": False,
            "bedroom": False,
            "office": False
        }
        self.monitor_status = "asleep"

    def enable_light(self, room):
        if room in self.home:
            self.home[room] = True
            subprocess.run(['notify-send', 'Свет включен', f'В комнате: {room}'], check=False)
            return f"💡 Свет включен в комнате: {room}"
        return "❌ Не удалось включить свет"

    def disable_light(self, room):
        if room in self.home:
            self.home[room] = False
            subprocess.run(['notify-send', 'Свет выключен', f'В комнате: {room}'], check=False)
            return f"💡 Свет выключен в комнате: {room}"
        return "❌ Не удалось выключить свет"

    def wake_monitor(self):
        try:
            subprocess.run(['xset', 'dpms', 'force', 'on'], check=False)
            self.monitor_status = "active"
            return "🖥️ Монитор выведен из спячки."
        except:
            return "🖥️ Не удалось вывести монитор из спячки."

    def enable_second_monitor(self):
        try:
            subprocess.run(['xrandr', '--output', 'HDMI-1', '--auto'], check=False)
            subprocess.run(['xset', 'dpms', 'force', 'on'], check=False)
            return "🖥️ Второй монитор выведен из спячки."
        except:
            return "🖥️ Не удалось вывести второй монитор."

    def execute(self, command):
        cmd = command.lower()
        if 'свет' in cmd:
            if 'включи' in cmd:
                room = cmd.replace('включи свет', '').strip()
                return self.enable_light(room or "living_room")
            elif 'выключи' in cmd:
                room = cmd.replace('выключи свет', '').strip()
                return self.disable_light(room or "living_room")
        elif 'монитор' in cmd:
            if 'включи' in cmd:
                return self.wake_monitor()
            elif 'второй' in cmd:
                return self.enable_second_monitor()
        return "Умный дом готов. Скажи: включи свет, выключи свет, монитор"
