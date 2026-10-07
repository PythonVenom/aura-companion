"""Тесты VoiceOrchestrator (speaker мокается)."""

from unittest.mock import MagicMock

from aura.voice.orchestrator import VoiceOrchestrator


def _make_orch():
    sp = MagicMock()
    sp.say.return_value = "🗣️ ok"
    sp.wait.return_value = None
    return VoiceOrchestrator(speaker=sp), sp


def test_speak_and_scan_calls_say_and_wait():
    orch, sp = _make_orch()
    orch.speak_and_scan("fix_success", hull=1570)
    sp.say.assert_called_once()
    sp.wait.assert_called_once()

def test_speak_and_scan_returns_scan_result():
    orch, _ = _make_orch()
    result = orch.speak_and_scan("fix_success", scan_fn=lambda: 42, hull=1570)
    assert result == 42

def test_speak_and_scan_without_scan_fn():
    orch, _ = _make_orch()
    assert orch.speak_and_scan("fix_success", hull=1570) is None

def test_speak_and_scan_handles_scan_exception():
    orch, _ = _make_orch()
    def boom():
        raise RuntimeError("scan failed")
    result = orch.speak_and_scan("fix_success", scan_fn=boom, hull=1570)
    assert "error" in result

def test_say_only():
    orch, sp = _make_orch()
    orch.say("morning", day=1, sector="STABILIZE", xp=0)
    sp.say.assert_called_once()
    sp.wait.assert_called_once()

def test_say_uses_line_template():
    orch, sp = _make_orch()
    orch.say("fix_success", hull=1570)
    args, _ = sp.say.call_args
    assert "1570" in args[0]
    assert "Залп принят" in args[0]
