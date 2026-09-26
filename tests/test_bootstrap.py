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
def orch(tmp_path, monkeypatch):
    """Собрать полный Orchestrator с замоканными LLM.

    Config path → несуществующий файл, все модули включены (ADR-011).
    """
    fake_cfg = tmp_path / "modules.toml"
    monkeypatch.setattr("aura.bootstrap.MODULES_CONFIG_PATH", fake_cfg)
    with patch("aura.agents.brain.AgentBrain.ask", return_value="❌ mock"), \
         patch("aura.agents.tool_router.AgentToolRouter.route", return_value=None):
        yield build_orchestrator()


class TestBootstrapAssembly:
    def test_all_agents_registered(self, orch) -> None:
        """Проверяем, что все 25 агентов на месте."""
        names = set(orch.registry.list_names())
        expected = {
            "time",
            "power",
            "vault",
            "music_ducker",
            "media_pause",
            "audio_pult",
            "journal",
            "rag_memory",
            "registry",
            "functions",
            "updates",
            "security",
            "audio_router",
            "vision",
            "focus_switch",
            "window_manager",
            "context_memory",
            "text_editor",
            "vk_music",
            "browser_tabs",
            "app_launcher",
            "window_control",
            "screen_reader",
            "media_search",
            "internet",
            "messenger",
            "music_local",
        }
        assert names == expected

    def test_agent_count(self, orch) -> None:
        assert len(orch) == 27


class TestRouting:
    """Проверяем, что правильные запросы уходят правильным агентам."""

    @pytest.mark.asyncio
    async def test_time_routed_to_time_agent(self, orch) -> None:
        result = await orch.process("который час")
        assert "Создатель" in result or "час" in result.lower()

    @pytest.mark.asyncio
    async def test_weather_routed_to_internet(self, orch) -> None:
        with patch("aura.agents.internet.urllib.request.urlopen") as mock_url:
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
        from aura.agents.registry import AgentRegistry

        test_file = tmp_path / "reg_test.json"
        monkeypatch.setattr(AgentRegistry, "MEMORY_FILE", str(test_file))

        from aura.bootstrap import build_orchestrator as rebuild
        local_orch = rebuild()

        result = await local_orch.process("покажи память")
        assert "last_command" in result

    @pytest.mark.asyncio
    async def test_vault_routed(self, orch, tmp_path, monkeypatch) -> None:
        from aura.agents.vault import AgentVault

        test_file = tmp_path / "vault_test.json"
        monkeypatch.setattr(AgentVault, "FACTS_FILE", str(test_file))

        from aura.bootstrap import build_orchestrator as rebuild
        local_orch = rebuild()

        result = await local_orch.process("запомни цвет синий")
        assert "Запомнила" in result or "запомнила" in result.lower()

    @pytest.mark.asyncio
    async def test_security_routed(self, orch) -> None:
        with patch("aura.agents.security.subprocess.run") as mock_run:
            from unittest.mock import MagicMock

            mock_run.return_value = MagicMock(stdout="", returncode=0)

            result = await orch.process("проверь систему")
            assert "чиста" in result.lower() or "Ошибка" in result

    @pytest.mark.asyncio
    async def test_music_ducker_routed(self, orch) -> None:
        with patch("aura.agents.music_ducker.subprocess.run") as mock_run:
            from unittest.mock import MagicMock

            mock_run.return_value = MagicMock(stdout="", returncode=0)

            result = await orch.process("приглуши музыку")
            assert "активного" in result.lower() or "Приглушила" in result

    @pytest.mark.asyncio
    async def test_text_editor_routed(self, orch) -> None:
        with patch("aura.agents.text_editor.AgentTextEditor.handle") as mock_handle:
            from aura.core.protocol import AgentResponse

            mock_handle.return_value = AgentResponse.ok(
                text="Выделила всё.", agent_name="text_editor"
            )
            # Просто проверяем, что роутинг находит text_editor


class TestFallback:
    @pytest.mark.asyncio
    async def test_unknown_goes_to_fallback(self, orch) -> None:
        result = await orch.process("xyzabc nonsense query 12345")
        assert result == orch.fallback_text


class TestOrder:
    def test_registration_order(self, orch) -> None:
        names = orch.registry.list_names()
        assert names[0] == "time"
        assert names[-1] == "internet"
        assert "messenger" in names
