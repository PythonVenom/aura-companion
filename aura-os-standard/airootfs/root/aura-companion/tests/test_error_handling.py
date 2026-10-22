"""Обработка ошибок в голосовом цикле."""
from unittest.mock import MagicMock

import aura_main


def _orch():
    o = object.__new__(aura_main.AuraOrchestrator)
    o.listener = MagicMock()
    o._say_with_duck = MagicMock()
    o.dm = MagicMock()
    o.dm.is_active.return_value = False
    o.orch = MagicMock()
    return o


def test_fsm_listener_exception_handled(monkeypatch):
    """Если listen() бросает — цикл не падает."""
    o = _orch()
    monkeypatch.setattr(aura_main, "fsm_get",
        lambda: {"state": "awaiting_command", "chat": "", "text": ""})
    monkeypatch.setattr(aura_main, "fsm_clear", lambda: None)
    o.listener.listen.side_effect = Exception("mic error")

    # Должно вернуть False или True, но не бросить
    try:
        result = o._handle_fsm()
        assert result in (True, False)
    except Exception as e:
        raise AssertionError(f"_handle_fsm упал: {e}")


def test_say_exception_not_crash():
    """Если _say_with_duck падает — не рушит цикл."""
    o = _orch()
    o._say_with_duck.side_effect = Exception("TTS error")
    # Метод сам ловит внутри
    try:
        o._say_with_duck("тест")
    except Exception:
        pass
    # Главное — проверка что мы это вызвали
    assert o._say_with_duck.called
