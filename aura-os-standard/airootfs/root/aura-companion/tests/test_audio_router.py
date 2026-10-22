"""
Тесты для AgentAudioRouter.

Никаких живых pactl-вызовов — всё через моки.
Никаких реальных переключений звука.

Проверяем:
- can_handle ловит нужные фразы и не ловит лишние
- handle возвращает корректный AgentResponse
- check_route возвращает message только при смене профиля
- логика детекта профиля (headset / internal / usb / bluetooth / unknown)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.agents.audio_router import AgentAudioRouter
from aura.core.protocol import AgentRequest, AgentStatus


# --- Фикстура: агент с замоканным detect_and_route ---

@pytest.fixture
def router():
    """
    AgentAudioRouter с отключённым первичным детектом.
    Иначе конструктор дёрнет pactl.
    """
    with patch.object(AgentAudioRouter, "detect_and_route", return_value=("internal", None)):
        r = AgentAudioRouter()
    return r


# --- can_handle ---

def test_can_handle_audio_check(router):
    assert router.can_handle(AgentRequest(text="проверь аудио"))


def test_can_handle_status(router):
    assert router.can_handle(AgentRequest(text="аудио статус"))


def test_can_handle_switch(router):
    assert router.can_handle(AgentRequest(text="переключи аудио"))


def test_can_handle_headphones(router):
    assert router.can_handle(AgentRequest(text="какая гарнитура подключена"))


def test_can_handle_connected(router):
    assert router.can_handle(AgentRequest(text="что подключено"))


def test_cannot_handle_unrelated(router):
    assert not router.can_handle(AgentRequest(text="который час"))


def test_cannot_handle_empty(router):
    assert not router.can_handle(AgentRequest(text=""))


# --- handle: проверь аудио ---

@pytest.mark.asyncio
async def test_handle_audio_status(router):
    router.current_profile = "headset"
    router.current_source = "alsa_input.fake"
    router.current_sink = "alsa_output.fake"

    resp = await router.handle(AgentRequest(text="проверь аудио"))

    assert resp.status == AgentStatus.OK
    assert resp.agent_name == "audio_router"
    assert "headset" in resp.text
    assert "alsa_input.fake" in resp.text
    assert "alsa_output.fake" in resp.text


# --- handle: какая гарнитура ---

@pytest.mark.asyncio
async def test_handle_headphones_jack(router):
    with patch.object(router, "_detect_profile", return_value="headset"):
        resp = await router.handle(AgentRequest(text="какая гарнитура"))

    assert resp.status == AgentStatus.OK
    assert "Гарнитура" in resp.text


@pytest.mark.asyncio
async def test_handle_headphones_internal(router):
    with patch.object(router, "_detect_profile", return_value="internal"):
        resp = await router.handle(AgentRequest(text="какая гарнитура"))

    assert "Встроенные" in resp.text


@pytest.mark.asyncio
async def test_handle_headphones_usb(router):
    with patch.object(router, "_detect_profile", return_value="usb"):
        resp = await router.handle(AgentRequest(text="что подключено"))

    assert "USB" in resp.text


@pytest.mark.asyncio
async def test_handle_headphones_bluetooth(router):
    with patch.object(router, "_detect_profile", return_value="bluetooth"):
        resp = await router.handle(AgentRequest(text="что подключено"))

    assert "Bluetooth" in resp.text


@pytest.mark.asyncio
async def test_handle_headphones_unknown(router):
    with patch.object(router, "_detect_profile", return_value="unknown"):
        resp = await router.handle(AgentRequest(text="что подключено"))

    assert "Неизвестно" in resp.text


# --- handle: переключи аудио ---

@pytest.mark.asyncio
async def test_handle_switch_returns_message(router):
    with patch.object(
        router, "detect_and_route", return_value=("headset", "🎧 Гарнитура найдена")
    ):
        resp = await router.handle(AgentRequest(text="переключи аудио"))

    assert resp.status == AgentStatus.OK
    assert "Гарнитура" in resp.text


@pytest.mark.asyncio
async def test_handle_switch_no_message_fallback(router):
    with patch.object(router, "detect_and_route", return_value=("internal", None)):
        resp = await router.handle(AgentRequest(text="переключи аудио"))

    assert resp.status == AgentStatus.OK
    assert "обновлена" in resp.text.lower()


# --- handle: not_handled для чужих команд ---

@pytest.mark.asyncio
async def test_handle_not_handled(router):
    # can_handle вернёт False, но handle не должен падать
    resp = await router.handle(AgentRequest(text="просто болтовня"))

    assert resp.status == AgentStatus.NOT_HANDLED


# --- check_route: интервал и сообщения ---

def test_check_route_respects_interval(router):
    """Второй вызов сразу после первого не должен дёргать detect_and_route."""
    with patch.object(
        router, "detect_and_route", return_value=("headset", "🎧 Гарнитура")
    ) as mock_detect:
        # Первый вызов — сбрасываем last_check
        router.last_check = 0.0
        profile1, msg1 = router.check_route()
        assert profile1 == "headset"
        assert msg1 == "🎧 Гарнитура"
        assert mock_detect.call_count == 1

        # Второй вызов сразу — интервал не прошёл, detect не зовём
        profile2, msg2 = router.check_route()
        assert msg2 is None
        assert mock_detect.call_count == 1


def test_check_route_returns_none_on_no_change(router):
    """Профиль не сменился — detect вернул (profile, None)."""
    router.last_check = 0.0
    with patch.object(
        router, "detect_and_route", return_value=("internal", None)
    ):
        profile, msg = router.check_route()

    assert profile == "internal"
    assert msg is None


def test_check_route_returns_message_on_change(router):
    """Профиль сменился — detect вернул (profile, message)."""
    router.last_check = 0.0
    with patch.object(
        router, "detect_and_route", return_value=("usb", "🎙️ USB-аудио")
    ):
        profile, msg = router.check_route()

    assert profile == "usb"
    assert msg == "🎙️ USB-аудио"


# --- detect_and_route: логика ---

def test_detect_and_route_first_call_sets_profile(router):
    router.current_profile = None
    with patch.object(router, "_detect_profile", return_value="internal"), \
         patch.object(router, "_set_default_source"), \
         patch.object(router, "_set_default_sink"), \
         patch.object(router, "_fix_speaker_volume"):
        profile, msg = router.detect_and_route()

    assert profile == "internal"
    # Bug 42: при первом вызове для internal — silent (msg=None)
    assert msg is None
    assert router.current_profile == "internal"
    assert router.current_source == AgentAudioRouter.DEFAULT_SOURCE
    assert router.current_sink == AgentAudioRouter.DEFAULT_SINK


def test_detect_and_route_same_profile_no_message(router):
    router.current_profile = "internal"
    with patch.object(router, "_detect_profile", return_value="internal"):
        profile, msg = router.detect_and_route()

    assert profile == "internal"
    assert msg is None


def test_detect_and_route_usb(router):
    router.current_profile = None
    with patch.object(router, "_detect_profile", return_value="usb"), \
         patch.object(router, "_fix_speaker_volume"):
        profile, msg = router.detect_and_route()

    assert profile == "usb"
    assert "USB" in msg


def test_detect_and_route_bluetooth(router):
    router.current_profile = None
    with patch.object(router, "_detect_profile", return_value="bluetooth"), \
         patch.object(router, "_fix_speaker_volume"):
        profile, msg = router.detect_and_route()

    assert profile == "bluetooth"
    assert "Bluetooth" in msg


def test_detect_and_route_unknown(router):
    router.current_profile = None
    with patch.object(router, "_detect_profile", return_value="unknown"):
        profile, msg = router.detect_and_route()

    assert profile == "unknown"
    assert "обновлена" in msg.lower()
