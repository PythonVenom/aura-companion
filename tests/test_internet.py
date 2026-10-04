"""
Тесты для AgentInternet.

ВАЖНО: Все тесты используют mock для urllib.request.urlopen.
Реальные сетевые запросы НЕ выполняются.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.internet import AgentInternet
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentInternet:
    return AgentInternet()


def make_response(payload: dict | str) -> MagicMock:
    """Создать mock-ответ urlopen."""
    if isinstance(payload, dict):
        body = json.dumps(payload).encode("utf-8")
    else:
        body = payload.encode("utf-8")
    mock = MagicMock()
    mock.read.return_value = body
    mock.__enter__ = lambda self: self
    mock.__exit__ = lambda self, *a: None
    return mock


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "погода",
        "погода в Москве",
        "курс доллара",
        "курс евро",
        "что такое Питон",
        "кто такой Пушкин",
        "найди Луну",
    ])
    def test_handles_internet_commands(self, agent: AgentInternet, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "включи музыку",
        "громче",
    ])
    def test_ignores_other(self, agent: AgentInternet, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestWeather:
    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_weather_ok(self, mock_urlopen, agent: AgentInternet) -> None:
        mock_urlopen.return_value = make_response("Moscow: ☀️ +15°C, ветер 3 м/с")

        response = await agent.handle(AgentRequest(text="погода в Москве"))

        assert response.status == AgentStatus.OK
        assert "Погода" in response.text
        assert "Moscow" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_weather_unknown_city(self, mock_urlopen, agent: AgentInternet) -> None:
        mock_urlopen.return_value = make_response("Unknown location: xyz")

        response = await agent.handle(AgentRequest(text="погода в xyz"))

        assert response.status == AgentStatus.OK
        assert "Не нашла" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_weather_network_error(self, mock_urlopen, agent: AgentInternet) -> None:
        mock_urlopen.side_effect = OSError("network down")

        response = await agent.handle(AgentRequest(text="погода"))

        assert response.status == AgentStatus.OK
        assert "Не удалось" in response.text


class TestCurrency:
    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_currency_usd(self, mock_urlopen, agent: AgentInternet) -> None:
        payload = {
            "Valute": {
                "USD": {"Value": 92.5, "Nominal": 1},
                "EUR": {"Value": 100.3, "Nominal": 1},
            }
        }
        mock_urlopen.return_value = make_response(payload)

        response = await agent.handle(AgentRequest(text="курс доллара"))

        assert response.status == AgentStatus.OK
        assert "USD" in response.text
        assert "92.50" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_currency_all(self, mock_urlopen, agent: AgentInternet) -> None:
        payload = {
            "Valute": {
                "USD": {"Value": 92.5, "Nominal": 1},
                "EUR": {"Value": 100.3, "Nominal": 1},
                "CNY": {"Value": 12.8, "Nominal": 1},
            }
        }
        mock_urlopen.return_value = make_response(payload)

        response = await agent.handle(AgentRequest(text="курс валют"))

        assert response.status == AgentStatus.OK
        assert "USD" in response.text
        assert "EUR" in response.text
        assert "CNY" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_currency_network_error(self, mock_urlopen, agent: AgentInternet) -> None:
        mock_urlopen.side_effect = OSError("network down")

        response = await agent.handle(AgentRequest(text="курс доллара"))

        assert response.status == AgentStatus.OK
        assert "Не удалось" in response.text


class TestWiki:
    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_wiki_ok(self, mock_urlopen, agent: AgentInternet) -> None:
        payload = {"extract": "Питон — язык программирования."}
        mock_urlopen.return_value = make_response(payload)

        response = await agent.handle(AgentRequest(text="что такое питон"))

        assert response.status == AgentStatus.OK
        assert "Питон" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_wiki_empty(self, mock_urlopen, agent: AgentInternet) -> None:
        mock_urlopen.return_value = make_response({"extract": ""})

        response = await agent.handle(AgentRequest(text="что такое xyzabc"))

        assert response.status == AgentStatus.OK
        assert "Ничего не нашла" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.internet.urllib.request.urlopen")
    async def test_wiki_truncates_long(self, mock_urlopen, agent: AgentInternet) -> None:
        payload = {"extract": "x" * 1000}
        mock_urlopen.return_value = make_response(payload)

        response = await agent.handle(AgentRequest(text="что такое длинное"))

        assert response.status == AgentStatus.OK
        assert response.text.endswith("...")
        assert len(response.text) < 600


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentInternet) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
