"""
Машинка 07: Интернет (AgentInternet)
"""

from agents.base import MicroAgent


class AgentInternet(MicroAgent):
    def __init__(self):
        super().__init__("internet", "Поиск в интернете")
        try:
            from ddgs import DDGS
            self.ddgs = DDGS()
            self.ready = True
        except:
            self.ready = False

    def search(self, query):
        if not self.ready:
            return "❌ Модуль поиска не установлен"
        try:
            results = []
            for r in self.ddgs.text(query, max_results=3):
                results.append(r)
            if not results:
                return f"❌ Ничего не найдено по '{query}'"
            answer = f"🔍 Результаты по '{query}':\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r.get('title', '')}\n   {r.get('body', '')[:150]}...\n"
            return answer
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    def execute(self, command):
        query = command.replace('найди', '').replace('поиск', '').replace('сколько времени в', '').replace('погода в', '').strip()
        if not query:
            return "Что искать?"
        return self.search(query)
