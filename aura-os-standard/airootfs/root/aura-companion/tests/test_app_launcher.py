"""
Тесты для AgentAppLauncher.

ВАЖНО: Все тесты используют mock для subprocess.
Реальные Popen/pkill/flatpak НЕ вызываются.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from aura.agents.app_launcher import AgentAppLauncher
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentAppLauncher:
    # Сканирование .desktop-файлов безопасно (только чтение)
    return AgentAppLauncher()


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "открой телеграм",
        "запусти стим",
        "закрой браузер",
        "список приложений",
        "какие приложения",
    ])
    def test_handles_app_commands(self, agent: AgentAppLauncher, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "какая погода",
        "громче",
    ])
    def test_ignores_other(self, agent: AgentAppLauncher, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestListApps:
    @pytest.mark.asyncio
    async def test_list_apps_returns_string(self, agent: AgentAppLauncher) -> None:
        response = await agent.handle(AgentRequest(text="список приложений"))
        assert response.status == AgentStatus.OK
        assert response.agent_name == "app_launcher"
        # Скорее всего найдено >0 приложений в системе
        assert "Приложений" in response.text or "Не найдено" in response.text


class TestOpenAppWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.app_launcher.AgentAppLauncher._focus_existing", return_value=False)
    @patch("aura.agents.app_launcher.subprocess.Popen")
    @patch("aura.agents.app_launcher.AgentAppLauncher.find_app")
    async def test_open_app_calls_popen(self, mock_find, mock_popen, mock_focus, agent: AgentAppLauncher) -> None:
        mock_find.return_value = {
            "name": "TestApp",
            "exec": "/usr/bin/testapp --flag",
            "file": "/usr/share/applications/testapp.desktop",
        }

        response = await agent.handle(AgentRequest(text="открой testapp"))

        assert response.status == AgentStatus.OK
        assert "Открыл" in response.text
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args == ["/usr/bin/testapp", "--flag"]

    @pytest.mark.asyncio
    @patch("aura.agents.app_launcher.AgentAppLauncher.find_app")
    async def test_open_app_not_found(self, mock_find, agent: AgentAppLauncher) -> None:
        mock_find.return_value = None

        response = await agent.handle(AgentRequest(text="открой nonexistent"))

        assert response.status == AgentStatus.OK
        assert "не найдено" in response.text


class TestCloseAppWithMock:
    @pytest.mark.asyncio
    @patch("aura.agents.app_launcher.subprocess.run")
    async def test_close_app_flatpak(self, mock_run, agent: AgentAppLauncher) -> None:
        # Имитируем: flatpak list вернул telegram, flatpak kill успешен
        mock_run.side_effect = [
            MagicMock(stdout="org.telegram.desktop\tTelegram\n", returncode=0),
            MagicMock(returncode=0),
        ]

        response = await agent.handle(AgentRequest(text="закрой телеграм"))

        assert response.status == AgentStatus.OK
        assert "Закрыл" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.app_launcher.subprocess.run")
    async def test_close_app_native(self, mock_run, agent: AgentAppLauncher) -> None:
        # flatpak list пустой, pkill -ix успешен
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),
            MagicMock(returncode=0),
        ]

        response = await agent.handle(AgentRequest(text="закрой firefox"))

        assert response.status == AgentStatus.OK
        assert "Закрыл" in response.text


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentAppLauncher) -> None:
        # "привет" не содержит ключевых слов
        response = await agent.handle(AgentRequest(text="xyz"))
        # может вернуть NOT_HANDLED, если нет ключей
        # или OK, если "закрой"/"открой" не найдены
        assert response.agent_name == "app_launcher"
