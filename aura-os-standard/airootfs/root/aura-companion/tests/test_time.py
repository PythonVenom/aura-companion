"""
Тесты для AgentTime.

Проверяем:
- can_handle распознаёт запросы о времени и дате
- can_handle не реагирует на посторонние запросы
- handle возвращает корректный ответ
- _plural работает правильно
- _day_part работает правильно
"""

import pytest

from aura.agents.time import AgentTime
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentTime:
    return AgentTime()


class TestCanHandle:
    """Проверка распознавания запросов."""

    @pytest.mark.parametrize("text", [
        "который час",
        "сколько времени",
        "время",
        "какой сегодня день",
        "какая дата",
        "число",
    ])
    def test_handles_time_and_date(self, agent: AgentTime, text: str) -> None:
        request = AgentRequest(text=text)
        assert agent.can_handle(request) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "как дела",
        "включи музыку",
        "погода",
    ])
    def test_ignores_other(self, agent: AgentTime, text: str) -> None:
        request = AgentRequest(text=text)
        assert agent.can_handle(request) is False


class TestHandle:
    """Проверка обработки запросов."""

    @pytest.mark.asyncio
    async def test_time_response(self, agent: AgentTime) -> None:
        request = AgentRequest(text="который час")
        response = await agent.handle(request)

        assert response.status == AgentStatus.OK
        assert response.agent_name == "time"
        assert "Создатель" in response.text
        assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_date_response(self, agent: AgentTime) -> None:
        request = AgentRequest(text="какая дата")
        response = await agent.handle(request)

        assert response.status == AgentStatus.OK
        assert response.agent_name == "time"
        assert "Сегодня" in response.text
        assert "Создатель" in response.text


class TestPlural:
    """Проверка склонения слов."""

    @pytest.mark.parametrize("n, expected", [
        (1, "час"),
        (2, "часа"),
        (3, "часа"),
        (4, "часа"),
        (5, "часов"),
        (10, "часов"),
        (11, "часов"),
        (21, "час"),
        (22, "часа"),
        (25, "часов"),
    ])
    def test_plural_hour(self, n: int, expected: str) -> None:
        assert AgentTime._plural(n, ("час", "часа", "часов")) == expected

    @pytest.mark.parametrize("n, expected", [
        (1, "минута"),
        (2, "минуты"),
        (5, "минут"),
        (11, "минут"),
        (21, "минута"),
    ])
    def test_plural_minute(self, n: int, expected: str) -> None:
        assert AgentTime._plural(n, ("минута", "минуты", "минут")) == expected


class TestDayPart:
    """Проверка частей суток."""

    @pytest.mark.parametrize("hour, expected", [
        (0, "ночи"),
        (3, "ночи"),
        (5, "утра"),
        (9, "утра"),
        (12, "дня"),
        (15, "дня"),
        (18, "вечера"),
        (22, "вечера"),
        (23, "ночи"),
    ])
    def test_day_part(self, hour: int, expected: str) -> None:
        assert AgentTime._day_part(hour) == expected


class TestWeekday:
    """Проверка дня недели."""

    def test_weekday_returns_string(self) -> None:
        result = AgentTime._weekday()
        assert isinstance(result, str)
        assert result in [
            "понедельник", "вторник", "среда", "четверг",
            "пятница", "суббота", "воскресенье",
        ]


class TestMonth:
    """Проверка месяца."""

    def test_month_returns_string(self) -> None:
        result = AgentTime._month()
        assert isinstance(result, str)
        assert result in [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        ]
