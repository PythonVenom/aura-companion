"""
Тесты для AgentAudioPult.

ВАЖНО: Все тесты используют mock для subprocess.
Реальные pactl НЕ вызываются.
"""

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.audio_pult import AgentAudioPult
from aura.core.protocol import AgentRequest, AgentStatus


@pytest.fixture
def agent() -> AgentAudioPult:
    return AgentAudioPult()


class TestCanHandle:
    @pytest.mark.parametrize("text", [
        "громкость 5",
        "громче",
        "тише",
        "выключи звук",
        "включи звук",
    ])
    def test_handles_volume_commands(self, agent: AgentAudioPult, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is True

    @pytest.mark.parametrize("text", [
        "привет",
        "который час",
        "какая погода",
        "открой браузер",
    ])
    def test_ignores_other(self, agent: AgentAudioPult, text: str) -> None:
        assert agent.can_handle(AgentRequest(text=text)) is False


class TestSetVolume:
    @pytest.mark.asyncio
    @patch("aura.agents.audio_pult.subprocess.run")
    async def test_set_volume_50(self, mock_run, agent: AgentAudioPult) -> None:
        response = await agent.handle(AgentRequest(text="громкость 5"))

        assert response.status == AgentStatus.OK
        assert "50%" in response.text
        # Проверяем, что pactl set-sink-volume вызван с 50%
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        assert args == ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "50%"]

    @pytest.mark.asyncio
    @patch("aura.agents.audio_pult.subprocess.run")
    async def test_set_volume_word(self, mock_run, agent: AgentAudioPult) -> None:
        response = await agent.handle(AgentRequest(text="громкость семь"))

        assert response.status == AgentStatus.OK
        assert "70%" in response.text


class TestMute:
    @pytest.mark.asyncio
    @patch("aura.agents.audio_pult.subprocess.run")
    async def test_mute(self, mock_run, agent: AgentAudioPult) -> None:
        response = await agent.handle(AgentRequest(text="выключи звук"))

        assert response.status == AgentStatus.OK
        assert "выключен" in response.text
        args = mock_run.call_args[0][0]
        assert args == ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"]

    @pytest.mark.asyncio
    @patch("aura.agents.audio_pult.subprocess.run")
    async def test_unmute(self, mock_run, agent: AgentAudioPult) -> None:
        response = await agent.handle(AgentRequest(text="включи звук"))

        assert response.status == AgentStatus.OK
        assert "включен" in response.text
        args = mock_run.call_args[0][0]
        assert args == ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"]


class TestUnknown:
    @pytest.mark.asyncio
    async def test_unknown_returns_not_handled(self, agent: AgentAudioPult) -> None:
        response = await agent.handle(AgentRequest(text="привет"))
        assert response.status == AgentStatus.NOT_HANDLED
