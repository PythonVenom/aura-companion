"""
Машинка 62: Маршрутизатор (AgentRouter)
"""

from agents.base import MicroAgent


class AgentRouter(MicroAgent):
    def __init__(self):
        super().__init__("router", "Маршрутизатор")
        self.ready = True
        self.last_commands = []

    def execute(self, command):
        cmd = command.lower()
        if 'открой браузер' in cmd or 'браузер' in cmd:
            response = self._get_agent('focus_switch').find_and_focus("Firefox")
            if 'не найдено' in response:
                self._get_agent('system').execute("браузер")
                return "Открыла браузер!"
            return response
        if 'открой код' in cmd or 'среда разработки' in cmd:
            response = self._get_agent('focus_switch').find_and_focus("Code OSS")
            if 'не найдено' in response:
                self._get_agent('system').execute("код")
                return "Открыла среду разработки!"
            return response
        return self._get_agent('brain').execute(command)

    def _get_agent(self, name):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get(name)
        return None
