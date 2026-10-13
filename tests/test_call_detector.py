"""Bug 31 — тесты детектора звонков."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aura.core import call_detector as CD


def _fake_pactl(apps: list[str]):
    """Сделать fake stdout для pactl с заданными application.name."""
    lines = ["Source Output #1"]
    for a in apps:
        lines.append(f'\tapplication.name = "{a}"')
        lines.append("\tpulse.corked = \"false\"")
    return "\n".join(lines)


def test_has_pactl():
    """pactl должен быть в системе."""
    assert CD._has_pactl() is True


def test_get_source_outputs_empty():
    with patch("aura.core.call_detector.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout="")
        assert CD._get_source_outputs() == []


def test_get_source_outputs_zoom():
    with patch("aura.core.call_detector.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout=_fake_pactl(["Zoom"]))
        assert CD._get_source_outputs() == ["zoom"]


def test_get_source_outputs_multiple():
    with patch("aura.core.call_detector.subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout=_fake_pactl([
            "Firefox", "Zoom", "python3.12"
        ]))
        apps = CD._get_source_outputs()
        assert len(apps) == 3
        assert "firefox" in apps
        assert "zoom" in apps


def test_get_source_outputs_pactl_fail():
    with patch("aura.core.call_detector.subprocess.run") as m:
        m.return_value = MagicMock(returncode=1, stdout="")
        assert CD._get_source_outputs() == []


def test_get_source_outputs_exception():
    with patch("aura.core.call_detector.subprocess.run",
               side_effect=OSError("boom")):
        assert CD._get_source_outputs() == []


def test_is_call_active_false_no_apps():
    with patch.object(CD, "_get_source_outputs", return_value=[]):
        assert CD.is_call_active() is False


def test_is_call_active_false_aura_only():
    """ALSA plug-in — это Aura, не звонок."""
    with patch.object(CD, "_get_source_outputs",
                      return_value=["alsa plug-in [python3.12]"]):
        assert CD.is_call_active() is False


def test_is_call_active_true_zoom():
    with patch.object(CD, "_get_source_outputs", return_value=["zoom"]):
        assert CD.is_call_active() is True


def test_is_call_active_true_firefox():
    with patch.object(CD, "_get_source_outputs", return_value=["firefox"]):
        assert CD.is_call_active() is True


def test_is_call_active_true_telegram():
    with patch.object(CD, "_get_source_outputs", return_value=["telegram-desktop"]):
        assert CD.is_call_active() is True


def test_is_call_active_true_max():
    with patch.object(CD, "_get_source_outputs", return_value=["max"]):
        assert CD.is_call_active() is True


def test_is_call_active_false_obs():
    """OBS — стрим, не звонок (в EXCLUDE)."""
    with patch.object(CD, "_get_source_outputs", return_value=["obs-studio"]):
        assert CD.is_call_active() is False


def test_is_call_active_false_audacity():
    with patch.object(CD, "_get_source_outputs", return_value=["audacity"]):
        assert CD.is_call_active() is False


def test_is_call_active_mixed_returns_true():
    """Aura + Zoom → звонок активен."""
    with patch.object(CD, "_get_source_outputs", return_value=[
        "alsa plug-in [python3.12]", "zoom",
    ]):
        assert CD.is_call_active() is True


def test_get_call_apps_only_calls():
    with patch.object(CD, "_get_source_outputs", return_value=[
        "zoom", "alsa plug-in [python3.12]", "obs-studio", "firefox",
    ]):
        active = CD.get_call_apps()
        assert "zoom" in active
        assert "firefox" in active
        assert "obs-studio" not in active
        assert "alsa plug-in [python3.12]" not in active


def test_call_apps_contains_key_apps():
    """Проверяем ключевые приложения в списке."""
    for app in ("zoom", "telegram", "discord", "firefox", "max"):
        assert app in CD.CALL_APPS


def test_exclude_apps_contains_aura():
    """Aura и её зависимости должны быть в EXCLUDE."""
    for app in ("alsa plug-in", "python3", "obs"):
        assert any(app in ex for ex in CD.EXCLUDE_APPS)


# === Интеграция с listener ===

def test_listener_skips_on_call():
    """Bug 31: во время звонка listener возвращает None."""
    from aura.agents.listener import AgentListener
    from unittest.mock import patch as _p

    lst = AgentListener.__new__(AgentListener)
    lst.ready = True
    lst.active = True

    with _p("aura.core.call_detector.is_call_active", return_value=True):
        result = lst._listen_impl(timeout=1)
    assert result is None


def test_listener_continues_no_call():
    """Без звонка — listener не блокируется (проверяем что дошло до stream)."""
    from aura.agents.listener import AgentListener
    from unittest.mock import patch as _p

    lst = AgentListener.__new__(AgentListener)
    lst.ready = True
    lst.active = True
    # Без stream — выйдет с None после проверки
    lst.get_stream = lambda: None

    with _p("aura.core.call_detector.is_call_active", return_value=False):
        result = lst._listen_impl(timeout=1)
    assert result is None  # нет stream — None
