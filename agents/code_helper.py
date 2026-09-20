"""
Машинка 17: Код-помощник (AgentCodeHelper)
"""

from agents.base import MicroAgent


class AgentCodeHelper(MicroAgent):
    def __init__(self):
        super().__init__("code_helper", "Код-помощник")
        self.context = []
        self.last_suggestion = None

    def execute(self, command):
        if 'помоги' in command or 'подскажи' in command:
            return "🦜 Я здесь, капитан! Что пишем?"
        elif 'код' in command:
            return self.suggest(command)
        elif 'ошибка' in command or 'баг' in command:
            return "🔍 Ищу ошибки в твоём коде..."
        elif 'покажи' in command:
            return f"📝 Последний код:\n{self.context[-1]['text'][:200] if self.context else 'Ничего нет'}"
        return "👀 Смотрю, что ты пишешь..."

    def suggest(self, context):
        suggestions = {
            'def': "def function_name():\n    # TODO: реализовать\n    pass",
            'class': "class ClassName:\n    def __init__(self):\n        pass",
            'try': "try:\n    # код\n except Exception as e:\n    print(f'Ошибка: {e}')",
            'main': "if __name__ == '__main__':\n    main()"
        }
        for key, value in suggestions.items():
            if key in context:
                return f"💡 Может так:\n{value}"
        return None
