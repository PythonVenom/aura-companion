"""
Dialog FSM — состояние многошагового диалога (ADR-012).

Messenger пишет состояние в файл, aura_main.py читает.
Как status.py — не ломает orchestrator.

Формат /tmp/aura_fsm.json:
    {"state": "idle|ask_text|ask_confirm",
     "chat": "имя чата",
     "text": "введённый текст",
     "ts": 1727000000.0}

Состояния:
- idle        — обычный цикл (ждёт «Аура»)
- ask_text    — открыт чат, ждём текст сообщения
- ask_confirm — текст введён, ждём «отправить? да/нет»

Таймауты: awaiting_command 10с, pending_read 180с, ask_* 30с.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

FSM_PATH = Path(os.environ.get("AURA_FSM_PATH", str(Path.home() / ".cache/aura/fsm.json")))
VALID_STATES = frozenset({"idle", "awaiting_command", "pending_read", "awaiting_reply", "ask_text", "ask_confirm"})
TIMEOUT_SEC = 30.0
TIMEOUT_AWAITING = 10.0
TIMEOUT_PENDING_READ = 180.0  # Bug 11: пожилым нужно 3 мин на ответ
TIMEOUT_AWAITING_REPLY = 180.0  # Bug 15: время на ответ в чат


def set_state(state: str, chat: str = "", text: str = "") -> None:
    """Записать состояние. Атомарно, best-effort."""
    if state not in VALID_STATES:
        state = "idle"
    payload = {
        "state": state,
        "chat": chat or "",
        "text": text or "",
        "ts": time.time(),
    }
    try:
        tmp = FSM_PATH.with_suffix(FSM_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, FSM_PATH)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.dialog_fsm').debug(
            'dialog_fsm error: %s', e)


def get_state() -> dict:
    """Прочитать состояние. Если файла нет или таймаут — idle."""
    try:
        if not FSM_PATH.exists():
            return {"state": "idle", "chat": "", "text": ""}
        data = json.loads(FSM_PATH.read_text(encoding="utf-8"))
        state = data.get("state", "idle")
        if state not in VALID_STATES:
            return {"state": "idle", "chat": "", "text": ""}
        # Таймаут по состоянию.
        ts = data.get("ts", 0)
        if state == "awaiting_command" and time.time() - ts > TIMEOUT_AWAITING:
            clear_state()
            return {"state": "idle", "chat": "", "text": ""}
        if state == "pending_read" and time.time() - ts > TIMEOUT_PENDING_READ:
            clear_state()
            return {"state": "idle", "chat": "", "text": ""}
        if state == "awaiting_reply" and time.time() - ts > TIMEOUT_AWAITING_REPLY:
            clear_state()
            return {"state": "idle", "chat": "", "text": ""}
        if state in ("ask_text", "ask_confirm") and time.time() - ts > TIMEOUT_SEC:
            clear_state()
            return {"state": "idle", "chat": "", "text": ""}
        return data
    except Exception:
        return {"state": "idle", "chat": "", "text": ""}


def clear_state() -> None:
    """Сбросить в idle."""
    try:
        FSM_PATH.unlink(missing_ok=True)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.dialog_fsm').debug(
            'dialog_fsm error: %s', e)


__all__ = ["FSM_PATH", "TIMEOUT_SEC", "VALID_STATES", "clear_state", "get_state", "set_state"]
