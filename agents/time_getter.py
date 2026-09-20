"""
Машинка 03: Время (AgentTimeGetter)
"""

from datetime import datetime
from agents.base import MicroAgent


class AgentTimeGetter(MicroAgent):
    def __init__(self):
        super().__init__("time", "Показывает время")
        self._last_command = ""

    def _plural(self, n, forms):
        n = abs(n) % 100
        n1 = n % 10
        if n > 10 and n < 20:
            return forms[2]
        if n1 > 1 and n1 < 5:
            return forms[1]
        if n1 == 1:
            return forms[0]
        return forms[2]

    def _day_part(self, hour):
        if 5 <= hour < 12:
            return "утра"
        elif 12 <= hour < 18:
            return "дня"
        elif 18 <= hour < 23:
            return "вечера"
        else:
            return "ночи"

    def _weekday(self):
        days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        return days[datetime.now().weekday()]

    def _month(self):
        months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        return months[datetime.now().month - 1]

    def execute(self, _):
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

        if minutes_str:
            result = f"{hours_str} {minutes_str} {self._day_part(hour)}, Создатель"
        else:
            result = f"{hours_str} {self._day_part(hour)}, Создатель"

        if "день" in self._last_command or "дата" in self._last_command:
            result = f"Сегодня {self._weekday()}, {now.day} {self._month()} {now.year} года, Создатель"

        return result

    def execute_with_command(self, command):
        self._last_command = command
        return self.execute(None)
