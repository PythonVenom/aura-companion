"""
Машинка 43: Хранилище (AgentVault)
"""

import os
import json
from agents.base import MicroAgent


class AgentVault(MicroAgent):
    def __init__(self):
        super().__init__("vault", "Хранилище")
        self.facts = {}
        self.facts_file = os.path.expanduser("~/aura_project/vault.json")
        self._load()

    def _load(self):
        if os.path.exists(self.facts_file):
            try:
                with open(self.facts_file, 'r', encoding='utf-8') as f:
                    self.facts = json.load(f)
            except:
                self.facts = {}

    def _save(self):
        try:
            with open(self.facts_file, 'w', encoding='utf-8') as f:
                json.dump(self.facts, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_fact(self, key, value):
        self.facts[key] = value
        self._save()
        return f"📌 Запомнила: {key} = {value}"

    def get_fact(self, key):
        return self.facts.get(key, None)

    def get_all_facts(self):
        return self.facts

    def execute(self, command):
        if 'запомни' in command or 'запиши' in command:
            parts = command.replace('запомни', '').replace('запиши', '').strip().split(' ', 1)
            if len(parts) == 2:
                return self.add_fact(parts[0], parts[1])
            else:
                return "Например: запомни мой любимый цвет синий"
        elif 'что ты помнишь' in command or 'память' in command:
            return json.dumps(self.get_all_facts(), ensure_ascii=False, indent=2)
        return "📌 Хранилище готово. Скажи: запомни [факт]"
