"""
Тесты для AgentWindowControl.

ВАЖНО: Все тесты используют mock для subprocess.
Реальные wmctrl/xdotool НЕ вызываются.
"""

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.window_control import AgentWindowControl
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentWindowControl:
    return AgentWindowControl()


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "фокус на телеграм",
        "переключись на браузер",
        "разверни окно",
        "на весь экран",
        "сверни окно",
        "закрой окно",
        "список окон",
    ])
    def test_handles_window_commands(self, agent: AgentWindowControl, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "громче",
        "погода",
    ])
    def test_ignores_other(self, agent: AgentWindowControl, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestListWindows:
    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_list_ok(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(
            stdout=(
                "0x01 0 host Firefox\n"
                "0x02 0 host Telegram\n"
            ),
            returncode=0,
        )

        response = await agent.handle(AgentRequest(text="список окон"))

        assert response.status == AgentStatus.OK
        assert "Firefox" in response.text
        assert "Telegram" in response.text
        assert "2" in response.text

    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_list_empty(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        response = await agent.handle(AgentRequest(text="список окон"))

        assert response.status == AgentStatus.OK
        assert "нет" in response.text.lower()


class TestFocus:
    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_focus_ok(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        response = await agent.handle(AgentRequest(text="фокус на телеграм"))

        assert response.status == AgentStatus.OK
        assert "телеграм" in response.text.lower()
        args = mock_run.call_args[0][0]
        assert args == ["wmctrl", "-a", "телеграм"]

    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_focus_not_found(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(returncode=1)

        response = await agent.handle(AgentRequest(text="фокус на xyzabc"))

        assert response.status == AgentStatus.OK
        assert "не найдено" in response.text


class TestFullscreen:
    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_fullscreen(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        response = await agent.handle(AgentRequest(text="разверни окно"))

        assert response.status == AgentStatus.OK
        assert "Полноэкранный" in response.text
        args = mock_run.call_args[0][0]
        assert args == ["wmctrl", "-r", ":ACTIVE:", "-b", "toggle,fullscreen"]


class TestMinimize:
    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_minimize(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        response = await agent.handle(AgentRequest(text="сверни окно"))

        assert response.status == AgentStatus.OK
        assert "свёрнуто" in response.text.lower()


class TestClose:
    @pytest.mark.asyncio
    @patch("aura.agents.window_control.subprocess.run")
    async def test_close(self, mock_run, agent: AgentWindowControl) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        # Bug 31: сначала подтверждение
        r1 = await agent.handle(AgentRequest(text="закрой окно"))
        assert "да" in r1.text.lower() or "нет" in r1.text.lower()
        # Подтверждаем
        response = await agent.handle(AgentRequest(text="да"))

        assert response.status == AgentStatus.OK
        assert "закрыто" in response.text.lower()
        args = mock_run.call_args[0][0]
        assert args == ["wmctrl", "-c", ":ACTIVE:"]


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentWindowControl) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
