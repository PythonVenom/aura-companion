"""
Базовый класс для всех микро-агентов Ауры.

Копия agents/base.py для модульной архитектуры (Strangler Fig, Фаза 1).
Каждый агент-«машинка» наследуется от MicroAgent.

ВАЖНО: это отдельная копия, не связанная с agents/base.py.
Монолит использует свою версию, модуль — свою.
Разрыв сделан осознанно (docs/migration-roadmap.md, Фаза 1).
"""


class MicroAgent:
    def __init__(self, name=None, description=None):
        self.name = name or getattr(self.__class__, "name", self.__class__.__name__)
        self.description = description or getattr(self.__class__, "description", "")
        self.active = False

    def activate(self):
        self.active = True
        print(f"🔧 {self.name} активирован")

    def deactivate(self):
        self.active = False
        print(f"🔧 {self.name} деактивирован")

    def execute(self, input_data):
        raise NotImplementedError
