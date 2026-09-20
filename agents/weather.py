"""
Машинка 13: Погода (AgentWeather)
"""

from agents.base import MicroAgent


class AgentWeather(MicroAgent):
    def __init__(self):
        super().__init__("weather", "Погода")
        self.ready = True

    def execute(self, command):
        try:
            query = command.replace('погода', '').replace('какая', '').replace('сегодня', '').strip()
            if not query:
                query = "Москва"

            import __main__
            aura = getattr(__main__, 'aura', None)
            if aura and hasattr(aura, 'agents'):
                internet = aura.agents.get('internet')
                if internet:
                    return internet.search(f"погода {query}")

            return "❌ Погода недоступна"
        except:
            return "❌ Не удалось получить погоду"
