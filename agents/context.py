"""
Машинка 12: Контекст (AgentContext)
"""

from agents.base import MicroAgent


class AgentContext(MicroAgent):
    def __init__(self):
        super().__init__("context", "Контекст и анализ")
        self.registry = None

    def _get_registry(self):
        if not self.registry:
            import __main__
            aura = getattr(__main__, 'aura', None)
            if aura and hasattr(aura, 'agents'):
                self.registry = aura.agents.get('registry')
        return self.registry

    def analyze(self):
        registry = self._get_registry()
        if not registry:
            return "⚠️ Реестр не найден"

        context = registry.get_context()
        commands = context.get("recent_commands", [])

        if len(commands) < 3:
            return "👀 Недостаточно данных для анализа"

        patterns = []
        if "браузер" in str(commands[-3:]) and "музык" in str(commands[-3:]):
            patterns.append("🔍 Паттерн: после браузера → музыка")
        if "врем" in str(commands[-3:]) and "врем" in str(commands[-5:]):
            patterns.append("🔄 Паттерн: частый запрос времени")

        if patterns:
            return "\n".join(patterns)
        return "📊 Паттернов не обнаружено"

    def execute(self, command):
        if "анализ" in command or "паттерн" in command:
            return self.analyze()
        return "🧠 Контекст: анализирую поведение"
