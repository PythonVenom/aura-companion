"""
Базовый класс для всех микро-агентов Ауры.
Каждый агент наследуется от MicroAgent.
"""


class MicroAgent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.active = False

    def activate(self):
        self.active = True
        print(f"🔧 {self.name} активирован")

    def deactivate(self):
        self.active = False
        print(f"🔧 {self.name} деактивирован")

    def execute(self, input_data):
        raise NotImplementedError
