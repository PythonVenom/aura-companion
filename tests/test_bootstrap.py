"""
Интеграционные тесты сборки Ауры.

Проверяют, что Orchestrator с зарегистрированными агентами
правильно роутит запросы в нужные агенты.

ВАЖНО: Никаких реальных действий (нет poweroff, нет pactl, нет сети).
Все опасные вызовы замоканы.
"""

from unittest.mock import patch

import pytest

from aura.bootstrap import build_orchestrator


@pytest.fixture
def orch():
    """Собрать полный Orchestrator."""
    return build_orchestrator()


class TestBootstrapAssembly:
    def test_all_agents_registered(self, orch) -> None:
        """Проверяем, что все 9 агентов на месте."""
        names = set(orch.registry.list_names())
        expected = {
            "time",
            "power",
            "audio_pult",
            "app_launcher",
            "window_control",
            "screen_reader",
            "browser_tabs",
            "media_search",
            "vk_music",
            "internet",
        }
        assert names == expected

    def test_agent_count(self, orch) -> None:
        assert len(orch) == 10


class TestRouting:
    """Проверяем, что правильные запросы уходят правильным агентам."""

    @pytest.mark.asyncio
    async def test_time_routed_to_time_agent(self, orch) -> None:
        result = await orch.process("который час")
        # AgentTime отвечает что-то про время суток
        assert "Создатель" in result or "час" in result.lower()

    @pytest.mark.asyncio
    async def test_weather_routed_to_internet(self, orch) -> None:
        with patch("aura.agents.internet.urllib.request.urlopen") as mock_url:
            import json
            from unittest.mock import MagicMock

            mock = MagicMock()
            mock.read.return_value = b"Moscow: +15"
            mock.__enter__ = lambda s: s
            mock.__exit__ = lambda s, *a: None
            mock_url.return_value = mock

            result = await orch.process("погода в Москве")
            assert "Погода" in result

    @pytest.mark.asyncio
    async def test_volume_routed_to_audio_pult(self, orch) -> None:
        with patch("aura.agents.audio_pult.subprocess.run") as mock_run:
            from unittest.mock import MagicMock

            mock_run.return_value = MagicMock(returncode=0)

            result = await orch.process("громкость 5")
            assert "50" in result


class TestFallback:
    """Проверяем, что неизвестный запрос уходит в fallback."""

    @pytest.mark.asyncio
    async def test_unknown_goes_to_fallback(self, orch) -> None:
        result = await orch.process("xyzabc nonsense query 12345")
        assert result == orch.fallback_text


class TestOrder:
    """Проверяем порядок регистрации — первый подходящий выигрывает."""

    def test_registration_order(self, orch) -> None:
        names = orch.registry.list_names()
        # time должен быть первым (простые — раньше)
        assert names[0] == "time"
        # internet последним (сеть — в конце)
        assert names[-1] == "internet"
