"""
Агент времени.

Показывает текущее время и дату.
Не имеет внешних зависимостей — только datetime.
Это эталонный агент для остальных.
"""

from __future__ import annotations

from datetime import datetime

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentTime(BaseAgent):
    """
    Агент времени.

    Обрабатывает запросы:
    - "который час" / "сколько времени" / "время"
    - "какой сегодня день" / "какая дата" / "дата"
    """

    name = "time"

    # Ключевые слова для can_handle
    TIME_KEYWORDS = ("время", "час", "сколько времени", "который час")
    DATE_KEYWORDS = ("дата", "день", "число", "какой сегодня")

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.TIME_KEYWORDS + self.DATE_KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if any(kw in text for kw in self.DATE_KEYWORDS):
            result = self._format_date()
        else:
            result = self._format_time()

        return AgentResponse.ok(text=result, agent_name=self.name)

    # --- Внутренние методы ---

    def _format_time(self) -> str:
        """Форматирует текущее время по-русски."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        if hour == 0:
            display_hour = 12
        elif hour > 12:
            display_hour = hour - 12
        else:
            display_hour = hour

        hours_str = f"{display_hour} {self._plural(display_hour, ['час', 'часа', 'часов'])}"

        if minute == 0:
            minutes_str = ""
        else:
            minutes_str = f"{minute} {self._plural(minute, ['минута', 'минуты', 'минут'])}"

        day_part = self._day_part(hour)

        if minutes_str:
            return f"{hours_str} {minutes_str} {day_part}, Создатель"
        return f"{hours_str} {day_part}, Создатель"

    def _format_date(self) -> str:
        """Форматирует текущую дату по-русски."""
        now = datetime.now()
        return (
            f"Сегодня {self._weekday()}, "
            f"{now.day} {self._month()} {now.year} года, Создатель"
        )

    @staticmethod
    def _plural(n: int, forms: tuple[str, str, str]) -> str:
        """
        Выбирает форму слова по числу.

        forms = (единственное, 2-4, 5+)
        Пример: _plural(1, ('час', 'часа', 'часов')) -> 'час'
                _plural(2, ('час', 'часа', 'часов')) -> 'часа'
                _plural(5, ('час', 'часа', 'часов')) -> 'часов'
        """
        n = abs(n) % 100
        n1 = n % 10

        if 10 < n < 20:
            return forms[2]
        if 1 < n1 < 5:
            return forms[1]
        if n1 == 1:
            return forms[0]
        return forms[2]

    @staticmethod
    def _day_part(hour: int) -> str:
        """Часть суток по часу."""
        if 5 <= hour < 12:
            return "утра"
        elif 12 <= hour < 18:
            return "дня"
        elif 18 <= hour < 23:
            return "вечера"
        else:
            return "ночи"

    @staticmethod
    def _weekday() -> str:
        """День недели по-русски."""
        days = [
            "понедельник", "вторник", "среда", "четверг",
            "пятница", "суббота", "воскресенье",
        ]
        return days[datetime.now().weekday()]

    @staticmethod
    def _month() -> str:
        """Месяц по-русски в родительном падеже."""
        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        ]
        return months[datetime.now().month - 1]


__all__ = ["AgentTime"]
