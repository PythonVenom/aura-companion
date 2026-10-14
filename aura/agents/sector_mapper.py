"""AgentSectorMapper — определяет «сектор инфокосмоса» по запросу.

Сектор = раздел интернета/жизни: news, code, music, knowledge, home, health.

Наука: Topic Classification (Manning 2008), Intent Detection.
Лор: AURA летит по инфокосмосу, каждый сектор — область знаний.
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent

SECTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "news":     ("новост", "что происходит", "последние событ", "срочно в мире"),
    "code":     ("код", "программ", "python", "asyncio", "функци", "баг", "ошибк в коде"),
    "music":    ("музык", "песн", "трек", "альбом", "исполнител", "включи"),
    "knowledge":("что такое", "объясни", "расскажи про", "факт о", "знаешь о"),
    "home":     ("дом", "свет", "розетк", "температур", "кондицион", "mqtt", "умный дом"),
    "health":   ("болит", "здоров", "таблетк", "врач", "самочувств", "пульс"),
    "finance":  ("курс", "доллар", "евро", "банк", "оплат", "жкх", "пенси"),
}


class AgentSectorMapper(BaseAgent):
    """Определяет сектор по тексту запроса. Мета-агент (не действие)."""

    name = "sector_mapper"
    MODULE_ALWAYS = True

    def can_handle(self, request: AgentRequest) -> bool:
        t = request.text.lower()
        return any(k in t for k in ("сектор", "где я", "где мы", "какой сектор"))

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        t = request.text.lower()
        # Извлечь запрос после «сектор/где»
        for marker in ("сектор", "где я", "где мы", "какой сектор"):
            if marker in t:
                query = t.split(marker, 1)[-1].strip(" ?.,!")
                break
        else:
            query = t

        sector = self.detect(query)
        return AgentResponse.ok(
            text=f"🛸 Сектор: {sector}. Курс проложен.",
            agent_name=self.name,
        )

    @staticmethod
    def detect(text: str) -> str:
        """Определить сектор по ключевым словам."""
        t = text.lower()
        best, best_score = "unknown", 0
        for sector, kws in SECTOR_KEYWORDS.items():
            score = sum(1 for kw in kws if kw in t)
            if score > best_score:
                best, best_score = sector, score
        return best if best_score > 0 else "unknown"


__all__ = ["SECTOR_KEYWORDS", "AgentSectorMapper"]
