"""
Тесты для AgentPower.

ВАЖНО: Все тесты используют mock для subprocess.Popen.
Реальные systemctl/shutdown/loginctl НЕ вызываются.
"""

from unittest.mock import patch

import pytest

from aura.agents.power import AgentPower
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentPower:
    return AgentPower()


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "выключи пк",
        "перезагрузи",
        "спящий режим",
        "заблокируй экран",
        "выйди из системы",
        "гибернация",
    ])
    def test_handles_power_commands(self, agent: AgentPower, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "включи музыку",
        "какая погода",
    ])
    def test_ignores_other(self, agent: AgentPower, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestHandleWithMock:
    """Тесты handle с mock для subprocess.Popen."""

    @pytest.mark.asyncio
    @patch("aura.agents.power.subprocess.Popen")
    async def test_shutdown_calls_systemctl_poweroff(self, mock_popen, agent: AgentPower) -> None:
        response = await agent.handle(AgentRequest(text="выключи пк"))

        assert response.status == AgentStatus.OK
        assert response.agent_name == "power"
        assert "Выключаю" in response.text
        # Проверяем, что вызван systemctl poweroff
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args == ["systemctl", "poweroff"]

    @pytest.mark.asyncio
    @patch("aura.agents.power.subprocess.Popen")
    async def test_reboot_calls_systemctl_reboot(self, mock_popen, agent: AgentPower) -> None:
        response = await agent.handle(AgentRequest(text="перезагрузи"))

        assert response.status == AgentStatus.OK
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args == ["systemctl", "reboot"]

    @pytest.mark.asyncio
    @patch("aura.agents.power.subprocess.Popen")
    async def test_suspend_calls_systemctl_suspend(self, mock_popen, agent: AgentPower) -> None:
        response = await agent.handle(AgentRequest(text="спящий режим"))

        assert response.status == AgentStatus.OK
        args = mock_popen.call_args[0][0]
        assert args == ["systemctl", "suspend"]

    @pytest.mark.asyncio
    @patch("aura.agents.power.subprocess.Popen")
    async def test_lock_calls_loginctl(self, mock_popen, agent: AgentPower) -> None:
        response = await agent.handle(AgentRequest(text="заблокируй"))

        assert response.status == AgentStatus.OK
        args = mock_popen.call_args[0][0]
        assert args == ["loginctl", "lock-session"]

    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentPower) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
