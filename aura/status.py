"""
Статус Ауры для внешних наблюдателей (KDE виджет, tmux, etc).

Пишет /tmp/aura_status.json атомарно. Формат:
{"state": "idle|listening|thinking|speaking|error", "text": "...", "ts": float}

Состояния:
- idle      — ждёт «Аура»
- listening — услышала, распознаёт
- thinking  — обрабатывает команду
- speaking  — говорит ответ
- paused    — на паузе (hotkey)
- error     — ошибка

По науке:
- Модуль ничего не знает про агентов и оркестратор
- Атомарная запись (tmp + os.replace) — читатель никогда не видит полуфайл
- Без зависимостей, чистый stdlib
- Ошибки записи глотаются — статус не критичен для работы Ауры
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


STATUS_PATH = Path(os.environ.get("AURA_STATUS_PATH", str(Path.home() / ".cache/aura/aura_status.json")))

VALID_STATES = frozenset({"idle", "listening", "thinking", "speaking", "paused", "error"})


def set_status(state: str, text: str = "") -> None:
    """Записать статус. Атомарно, best-effort.

    Если state не из VALID_STATES — пишем "error".
    Ошибки записи игнорируются.
    """
    if state not in VALID_STATES:
        state = "error"
    payload = {
        "state": state,
        "text": (text or "")[:200],
        "ts": time.time(),
    }
    try:
        tmp = STATUS_PATH.with_suffix(STATUS_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, STATUS_PATH)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.status').debug(
            'status error: %s', e)


def clear_status() -> None:
    """Убрать файл статуса (при остановке)."""
    try:
        STATUS_PATH.unlink(missing_ok=True)
    except Exception as e:
        # F-006: не глотать (раздел 17 промта)
        import logging
        logging.getLogger('aura.status').debug(
            'status error: %s', e)


__all__ = ["set_status", "clear_status", "STATUS_PATH", "VALID_STATES"]
