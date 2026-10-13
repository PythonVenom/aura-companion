"""AgentCaptain — капитан корабля Aura (GAPS #9).

Роль: показать капитану его статус, дать совет от имени капитана,
вести ритуалы (утро/вечер).

Наука:
- Campbell 1949 (monomyth) — капитан как архетип героя
- Mass Effect (squadmates) — роль в команде
- Duhigg 2012 (habit loop) — ритуалы утро/вечер
- Seligman 2011 (flourish) — маленькие победы = мотивация

Тонкий агент: НЕ дублирует game/state.py, а использует его.
"""
from __future__ import annotations

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentCaptain(BaseAgent):
    """Капитан Aura — статус, советы, ритуалы."""

    name = "captain"
    description = "Капитан — статус, советы, ритуалы"

    KEYWORDS = (
        "капитан",
        "статус",
        "мой статус",
        "как дела у капитана",
        "что делать",
        "что дальше",
        "приоритеты",
        "xp",
        "опыт",
        "ранг",
        "уровень",
        "какой я капитан",
        "итоги дня",
        "что сделал за день",
    )

    # === API агента ===

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)

        text = request.text.lower()

        if "статус" in text or "ранг" in text or "уровень" in text or "xp" in text:
            return AgentResponse.ok(self._status(), self.name)

        if "что делать" in text or "что дальше" in text or "приоритет" in text:
            return AgentResponse.ok(self._advice(), self.name)

        if "итог" in text or "что сделал" in text:
            return AgentResponse.ok(self._daily_summary(), self.name)

        # Общий ответ
        return AgentResponse.ok(self._greeting(), self.name)

    # === Логика ===

    def _status(self) -> str:
        """Статус капитана: XP, ранг, сектор."""
        try:
            from aura.game.state import StateStore
            store = StateStore()
            state = store.load()
            days = state.days_on_planet() if hasattr(state, "days_on_planet") else 0
            hull = min(int(state.hull), 100)
            shields = min(int(state.shields), 100)
            return (
                f"🛸 Капитан Воронин Иван.\n"
                f"XP: {state.xp}  |  Ранг: {state.rank}  |  Уровень: {state.level}\n"
                f"Дней на планете: {days}\n"
                f"Корпус: {hull}%  |  Щиты: {shields}%"
            )
        except Exception as e:
            return f"🛸 Капитан на связи. Статус недоступен: {e}"

    def _advice(self) -> str:
        """Совет от капитана: топ-3 приоритета."""
        return (
            "🛸 Капитан, приоритеты по Д97 (дедлайн > долг > желание):\n"
            "\n"
            "1. 🔴 Флешка для бати (сегодня) — elder-care\n"
            "2. 🟡 Captain + Rituals (2-3ч) — для elder-care\n"
            "3. 🟡 Тесты на бате (1д) — после флешки\n"
            "\n"
            "❄️ РФРИТ заморожен (разморозка: «едем по РФРИТ»)"
        )

    def _daily_summary(self) -> str:
        """Итоги дня — из journal + commit log."""
        try:
            import subprocess
            from pathlib import Path

            # Последние 5 коммитов
            r = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=str(Path.home() / "aura-companion"),
                capture_output=True, text=True, timeout=5,
            )
            commits = r.stdout.strip() or "(нет коммитов)"

            # Journal
            journal = Path.home() / ".cache" / "aura" / "JOURNAL.md"
            journal_text = ""
            if journal.exists():
                lines = journal.read_text(encoding="utf-8").splitlines()[-5:]
                journal_text = "\n".join(lines)

            return (
                "🛸 Капитан, итоги дня:\n\n"
                f"**Коммиты:**\n{commits}\n\n"
                f"**Журнал (последние строки):**\n{journal_text or '(пусто)'}"
            )
        except Exception as e:
            return f"🛸 Итоги недоступны: {e}"

    def _greeting(self) -> str:
        """Капитан на связи."""
        return (
            "🛸 Капитан Воронин Иван на связи.\n"
            "Скажи «статус» для XP, «что делать» для приоритетов, "
            "«итоги дня» для отчёта."
        )


__all__ = ["AgentCaptain"]
