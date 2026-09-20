"""
Машинка 50: Автономность (AgentOfflineFirst)
"""

from agents.base import MicroAgent


class AgentOfflineFirst(MicroAgent):
    def __init__(self):
        super().__init__("offline_first", "Автономность")
        self.ready = True
        self.hybrid_core = None

    def _get_hybrid(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura:
            return aura.agents.get('hybrid_core')
        return None

    def execute(self, command):
        hybrid = self._get_hybrid()
        if hybrid:
            if not hybrid.check_network():
                return "⚡ Офлайн-режим: работаю на локальных моделях. Запрос обрабатываю сам."
            else:
                return "🌐 Гибридный режим: сеть доступна. Можно использовать облачные модели."
        return "⚡ Автономность + облако готовы."
