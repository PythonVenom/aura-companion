"""
Машинка 11: Память (AgentMemoryRegistry)
"""

import os
import json
from datetime import datetime
from agents.base import MicroAgent


class AgentMemoryRegistry(MicroAgent):
    def __init__(self):
        super().__init__("registry", "Реестр памяти")
        self.memory_file = os.path.expanduser("~/aura_project/memory_registry.json")
        self.session_data = self._load_or_create()
        self.last_event = None
        self.is_initialized = True

    def _load_or_create(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._new_session()
        return self._new_session()

    def _new_session(self):
        return {
            "session_id": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "start_time": datetime.now().isoformat(),
            "events": [],
            "summary": {
                "total_commands": 0,
                "most_used": {},
                "patterns": []
            }
        }

    def log(self, event_type, data):
        event = {
            "time": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.session_data["events"].append(event)
        self._save()

        if event_type == "command":
            self.session_data["summary"]["total_commands"] += 1
            cmd = data.get("command", "")
            if cmd:
                self.session_data["summary"]["most_used"][cmd] = self.session_data["summary"]["most_used"].get(cmd, 0) + 1

    def get_last(self, count=10):
        return self.session_data["events"][-count:]

    def get_context(self):
        last_events = self.get_last(20)
        context = {
            "last_command": None,
            "last_dialog": None,
            "last_action": None,
            "recent_commands": []
        }
        for e in last_events:
            if e["type"] == "command":
                context["last_command"] = e["data"].get("command")
                context["recent_commands"].append(e["data"].get("command"))
            elif e["type"] == "dialog":
                context["last_dialog"] = e["data"]
            elif e["type"] == "action":
                context["last_action"] = e["data"].get("action")
        return context

    def _save(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def execute(self, command):
        if "покажи память" in command:
            return json.dumps(self.get_context(), ensure_ascii=False, indent=2)[:500]
        return "📝 Реестр памяти работает"
