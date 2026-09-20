"""
Машинка 19: Призрак (AgentGhost)
"""

import time
import hashlib
from agents.base import MicroAgent


class AgentGhost(MicroAgent):
    def __init__(self):
        super().__init__("ghost", "Цифровой призрак")
        self.vms = {}
        self.active_rooms = []
        self.honeypots = {22: "SSH", 80: "HTTP", 443: "HTTPS"}

    def create_ghost_room(self):
        room_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
        self.vms[room_id] = {"id": room_id, "status": "active"}
        self.active_rooms.append(room_id)
        return f"👻 Комната {room_id} создана (анонимность: Tor + VPN)"

    def destroy_room(self, room_id):
        if room_id in self.vms:
            del self.vms[room_id]
            self.active_rooms.remove(room_id)
            return f"🗑️ Комната {room_id} уничтожена"
        return "❌ Комната не найдена"

    def execute(self, command):
        if 'создай призрак' in command:
            return self.create_ghost_room()
        elif 'уничтожь' in command:
            room_id = command.replace('уничтожь', '').strip()
            return self.destroy_room(room_id)
        return "👻 Я твой цифровой призрак!"
