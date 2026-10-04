"""Bug 6: DM-подтверждение рушится, если «аура» внутри фразы.

Из лога 04:45:
- «напиши в чат X привет» → DM: awaiting_confirm=True, «Написала? Отправить?»
- «да отправ шаура» → _is_activated=True → сброс DM → отправка НЕ выполнилась
"""

from unittest.mock import MagicMock

import aura_main
from aura.dialogue_manager import DialogueState, Scenario


def _make_orch(awaiting_confirm=True):
    orch = object.__new__(aura_main.AuraOrchestrator)
    orch.listener = MagicMock()
    orch._say_with_duck = MagicMock()

    sc = Scenario(
        name="send_message", agent="messenger",
        keywords=["напиши"], required_slots=["chat", "text"],
    )
    dm = MagicMock(spec=aura_main.DialogueManager)
    dm.is_active.return_value = True
    dm.state = DialogueState(scenario=sc, awaiting_confirm=awaiting_confirm)
    dm.process.return_value = "Отправила"
    orch.dm = dm
    return orch, dm


def test_dm_confirm_with_aura_in_text():
    """«да отправ шаура» — «аура» в конце не должна рушить подтверждение."""
    orch, dm = _make_orch(awaiting_confirm=True)
    orch.listener.listen.return_value = "да отправ шаура"
    result = orch._handle_dialog()
    assert result is True
    dm.process.assert_called_once()
    dm.reset.assert_not_called()
    orch._say_with_duck.assert_called_once_with("Отправила")


def test_dm_activation_outside_confirm_still_resets():
    """Вне awaiting_confirm «аура» всё ещё сбрасывает DM — это не регрессия."""
    orch, dm = _make_orch(awaiting_confirm=False)
    orch.listener.listen.return_value = "аура открой макс"
    result = orch._handle_dialog()
    assert result is False
    dm.reset.assert_called_once()
    dm.process.assert_not_called()
