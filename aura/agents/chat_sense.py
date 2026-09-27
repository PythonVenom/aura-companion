"""Bug 16: ChatSense — смысл чатов + напоминания.

MVP:
- Найти неотвеченные сообщения (последнее — от собеседника)
- Напомнить раз в N часов
- Формат: «Тебе не ответили: <чат> — с <время>»

Phase 2:
- Календарь из чатов (ADR-015)
- Смысловые события
"""
from __future__ import annotations

import json
import time
from pathlib import Path


STATE_PATH = Path("/tmp/aura_chat_sense.json")
RE_MIND_TTL = 4 * 3600   # не напоминать чаще 4 часов про один чат


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"reminded": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"reminded": {}}


def _save_state(state: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def find_unanswered(previews: list) -> list:
    """previews: [{'chat':..., 'preview':...}].

    Возвращает список неотвеченных:
    [{'chat':..., 'preview':..., 'reason':'unanswered'}]

    «Неотвеченное» = preview НЕ начинается с «Вы:» и не пуст.
    """
    out = []
    for p in previews:
        chat = p.get("chat", "").strip()
        prev = p.get("preview", "").strip()
        if not chat or not prev:
            continue
        if prev.startswith("Вы:"):
            continue
        # Системные/инфо-чаты
        if any(x in chat.lower() for x in ("коды подтверждения", "max на iphone")):
            continue
        out.append({"chat": chat, "preview": prev, "reason": "unanswered"})
    return out


def filter_by_reminder_ttl(items: list, state: dict | None = None) -> list:
    """Убрать те, о которых недавно напоминали."""
    if state is None:
        state = _load_state()
    reminded = state.get("reminded", {})
    now = time.time()
    out = []
    for it in items:
        chat = it["chat"]
        last = reminded.get(chat, 0)
        if now - last < RE_MIND_TTL:
            continue
        out.append(it)
    return out


def mark_reminded(items: list) -> None:
    state = _load_state()
    now = time.time()
    for it in items:
        state.setdefault("reminded", {})[it["chat"]] = now
    _save_state(state)


def summary(items: list) -> str:
    """Короткий текст для голоса."""
    if not items:
        return ""
    if len(items) == 1:
        return f"Тебе не ответили: {items[0]['chat']}"
    return f"Тебе не ответили в {len(items)} чатах. Первый — {items[0]['chat']}"


__all__ = [
    "find_unanswered", "filter_by_reminder_ttl", "mark_reminded",
    "summary", "STATE_PATH", "RE_MIND_TTL",
]
