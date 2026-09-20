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
        """Проверяем, что все 16 агентов на месте."""
        names = set(orch.registry.list_names())
        expected = {
            "time",
            "power",
            "audio_pult",
            "journal",
            "rag_memory",
            "registry",
            "functions",
            "updates",
            "audio_router",
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
        assert len(orch) == 16


class TestRouting:
    """Проверяем, что правильные запросы уходят правильным агентам."""

    @pytest.mark.asyncio
    async def test_time_routed_to_time_agent(self, orch) -> None:
        result = await orch.process("который час")
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

    @pytest.mark.asyncio
    async def test_functions_routed(self, orch) -> None:
        result = await orch.process("что ты умеешь")
        assert "Доступные функции" in result

    @pytest.mark.asyncio
    async def test_updates_routed(self, orch) -> None:
        with patch("aura.agents.updates.subprocess.run") as mock_run:
            from unittest.mock import MagicMock

            mock_run.return_value = MagicMock(stdout="0\n", returncode=0)

            result = await orch.process("проверь обновления")
            assert "обновлена" in result.lower() or "Доступно" in result

    @pytest.mark.asyncio
    async def test_registry_routed(self, orch, tmp_path, monkeypatch) -> None:
        """Проверяем, что registry отвечает на "покажи память"."""
        from aura.agents.registry import AgentRegistry

        test_file = tmp_path / "reg_test.json"
        monkeypatch.setattr(AgentRegistry, "MEMORY_FILE", str(test_file))

        # Пересобираем оркестратор с новым путём
        from aura.bootstrap import build_orchestrator as rebuild
        local_orch = rebuild()

        result = await local_orch.process("покажи память")
        # registry вернёт JSON с last_command
        assert "last_command" in result


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
        assert names[0] == "time"
        assert names[-1] == "internet"
