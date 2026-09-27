"""
Proactive Engine — Аура сама инициирует диалог (ADR-014).

Проверяет триггеры раз в N секунд. Если триггер сработал —
возвращает текст для речи. Аура говорит.

По науке:
- Изолирован (только логика + хранилище состояния).
- Тестируем (mock времени).
- Не знает про AuraCore.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from dataclasses import dataclass
import re
from aura.agents import chat_sense
from aura.agents.messenger import is_own_message
from pathlib import Path
from typing import Callable


STATE_PATH = Path(os.environ.get("AURA_PROACTIVE_PATH", "/tmp/aura_proactive.json"))
CHECK_INTERVAL_SEC = 30


@dataclass
class Trigger:
    """Один триггер проактивности."""
    name: str
    priority: int
    cooldown_sec: int
    condition: Callable[[dict], bool] = lambda state: False
    action: Callable[[], str] = lambda: ""


class ProactiveEngine:
    """Движок проактивности. Проверяет триггеры, выбирает лучший."""

    def __init__(self) -> None:
        self.triggers: list[Trigger] = []
        self._last_check = 0.0
        self._state = self._load_state()

    def register(self, trigger: Trigger) -> None:
        self.triggers.append(trigger)
        self.triggers.sort(key=lambda t: t.priority, reverse=True)

    def _load_state(self) -> dict:
        try:
            if STATE_PATH.exists():
                return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_state(self) -> None:
        try:
            tmp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
            tmp.write_text(json.dumps(self._state, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, STATE_PATH)
        except Exception:
            pass

    def _is_in_cooldown(self, trigger: Trigger) -> bool:
        last_ts = self._state.get(trigger.name, 0)
        return (time.time() - last_ts) < trigger.cooldown_sec

    def _mark_triggered(self, trigger: Trigger) -> None:
        self._state[trigger.name] = time.time()
        self._save_state()

    def check(self) -> str | None:
        """Проверить все триггеры. Вернуть текст для речи или None."""
        now = time.time()
        if now - self._last_check < CHECK_INTERVAL_SEC:
            return None
        self._last_check = now

        for trigger in self.triggers:
            if self._is_in_cooldown(trigger):
                continue
            try:
                if trigger.condition(self._state):
                    self._mark_triggered(trigger)
                    return trigger.action()
            except Exception:
                continue
        return None


def _collect_briefing(get_agent) -> str:
    """Собрать утренний брифинг из блоков."""
    blocks = []

    # Блок 1: приветствие + время
    time_agent = get_agent("time") if get_agent else None
    if time_agent:
        try:
            blocks.append("Доброе утро, Создатель.")
        except Exception:
            blocks.append("Доброе утро, Создатель.")
    else:
        blocks.append("Доброе утро, Создатель.")

    # Блок 2: погода (internet)
    internet = get_agent("internet") if get_agent else None
    if internet:
        try:
            # Используем публичный метод internet — спросить погоду.
            # Заглушка — Фаза 17.2 доработает.
            pass
        except Exception:
            pass

    # Блок 3: задачи (journal)
    journal = get_agent("journal") if get_agent else None
    if journal and hasattr(journal, "get_pending_tasks"):
        try:
            tasks = journal.get_pending_tasks()
            if tasks:
                blocks.append(f"Незакрытых задач: {len(tasks)}.")
        except Exception:
            pass

    return " ".join(blocks) if blocks else "Доброе утро, Создатель."


def morning_briefing_trigger(get_agent=None) -> Trigger:
    """Утренний брифинг: 1 раз в день, 07:30-09:30."""
    def condition(state: dict) -> bool:
        now = datetime.now()
        if not (7 <= now.hour < 10):
            return False
        today = now.date().isoformat()
        if state.get("briefing_date") == today:
            return False
        state["briefing_date"] = today
        return True

    def action() -> str:
        return _collect_briefing(get_agent)

    return Trigger(
        name="morning_briefing",
        priority=10,
        cooldown_sec=3600,
        condition=condition,
        action=action,
    )


def _normalize_preview(preview: str) -> str:
    """Bug 9: убрать из preview счётчик непрочитанных и timestamp.

    MAX отдаёт preview в виде:
      "1 | Прогуляться не хочешь"
      "Привет | 10:45"
      "1 | текст | 10:45"
    Нормализуем — иначе ключ меняется каждый пул → триггер дублируется.
    """
    if not preview:
        return ""
    t = preview.strip()
    # Ведущий счётчик: "N | "
    t = re.sub(r"^\d+\s*\|\s*", "", t)
    # Trailing timestamp: " | HH:MM" или " | 22 сент."
    t = re.sub(r"\s*\|\s*\d{1,2}:\d{2}\s*$", "", t)
    t = re.sub(r"\s*\|\s*\d{1,2}\s+[а-яА-Я]{3,}\.?\s*$", "", t)
    return t.strip()


def _extract_chat_cooldown_key(chat: str, preview: str) -> str:
    """Ключ для cooldown — имя чата + нормализованный preview."""
    return f"{chat}:{_normalize_preview(preview)}"


def max_new_message_trigger(get_agent) -> Trigger:
    """Новое сообщение в Максе — pull через list_chats (без observer)."""
    PENDING_PATH = Path("/tmp/aura_max_pending.json")

    def _fetch_previews(messenger):
        """get_all_previews с fallback на get_last_message_preview (Strangler Fig)."""
        try:
            if hasattr(messenger, "get_all_previews"):
                return messenger.get_all_previews() or []
            if hasattr(messenger, "get_last_message_preview"):
                one = messenger.get_last_message_preview() or {}
                if one.get("chat") and one.get("preview"):
                    return [one]
        except Exception:
            pass
        return []

    def condition(state: dict) -> bool:
        if get_agent is None:
            return False
        messenger = get_agent("messenger")
        if messenger is None:
            return False

        previews = _fetch_previews(messenger)

        # Фильтр: пустые и «Вы: ...» (Bug 3 — свои сообщения).
        filtered = []
        for p in previews:
            chat = p.get("chat", "")
            preview = p.get("preview", "")
            if not chat or not preview:
                continue
            if preview.strip().startswith("Вы:"):
                continue
            # Bug 13: не триггерить на собственные отправленные.
            try:
                if is_own_message(chat, preview):
                    continue
            except Exception:
                pass
            filtered.append({"chat": chat, "preview": preview})

        seen = set(state.get("max_seen_keys", []))
        current = {_extract_chat_cooldown_key(p['chat'], p['preview'])
                   for p in filtered}

        # Первый прогон — populate без триггера.
        if not seen:
            state["max_seen_keys"] = sorted(current)
            return False

        new_keys = current - seen
        if not new_keys:
            return False

        # Bug 9: per-chat cooldown — 5 минут. Если уже говорили про этот
        # чат недавно — пропускаем (защита от изменения preview).
        now = time.time()
        per_chat = state.get("max_chat_last_ts", {})
        COOLDOWN_CHAT = 300.0

        candidates = []
        for p in filtered:
            key = _extract_chat_cooldown_key(p['chat'], p['preview'])
            if key not in new_keys:
                continue
            last = per_chat.get(p['chat'], 0)
            if now - last < COOLDOWN_CHAT:
                continue
            candidates.append((p, key))

        if not candidates:
            # Всё новое — в cooldown. Запоминаем и молчим.
            state["max_seen_keys"] = sorted(seen | current)
            return False

        # Берём первый после фильтра (Bug 4 — по имени, не по индексу).
        new_one, new_key = candidates[0]
        per_chat[new_one['chat']] = now
        state["max_chat_last_ts"] = per_chat
        state["max_seen_keys"] = sorted(seen | current)
        try:
            PENDING_PATH.write_text(
                json.dumps({"chat": new_one["chat"], "preview": new_one["preview"]},
                           ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass
        return True

    def action() -> str:
        try:
            data = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
            chat = data.get("chat", "")
            preview = data.get("preview", "")
            # FSM: ждать ответа «да/нет» (ADR-013).
            try:
                from aura.dialog_fsm import set_state as fsm_set
                fsm_set("pending_read", chat=chat, text=preview)
            except Exception:
                pass
            if chat:
                return f"Создатель, новое сообщение от {chat}. Зачитать?"
            return "Создатель, новое сообщение в Максе. Зачитать?"
        except Exception:
            return "Создатель, в Максе новое сообщение."

    return Trigger(
        name="max_new_message",
        priority=8,
        cooldown_sec=120,
        condition=condition,
        action=action,
    )


def unanswered_messages_trigger(get_agent) -> Trigger:
    """Bug 16: раз в 30 мин — неотвеченные в Максе.

    Замыкание _cache: condition сохраняет items, action читает.
    """
    _cache: dict = {}

    def condition(state: dict) -> bool:
        if get_agent is None:
            return False
        messenger = get_agent("messenger")
        if messenger is None or not hasattr(messenger, "get_all_previews"):
            return False
        try:
            previews = messenger.get_all_previews() or []
            items = chat_sense.find_unanswered(previews)
            items = chat_sense.filter_by_reminder_ttl(items)
            if not items:
                return False
            _cache["items"] = items
            return True
        except Exception:
            return False

    def action() -> str:
        items = _cache.pop("items", [])
        if not items:
            return "Неотвеченные: (пусто)"
        chat_sense.mark_reminded(items)
        return chat_sense.summary(items)

    return Trigger(
        name="unanswered_messages",
        priority=7,
        cooldown_sec=1800,
        condition=condition,
        action=action,
    )


def default_engine(get_agent=None) -> ProactiveEngine:
    """Стандартный набор триггеров."""
    engine = ProactiveEngine()
    engine.register(morning_briefing_trigger(get_agent))
    engine.register(max_new_message_trigger(get_agent))
    engine.register(unanswered_messages_trigger(get_agent))
    return engine


__all__ = [
    "Trigger",
    "ProactiveEngine",
    "morning_briefing_trigger",
    "default_engine",
    "STATE_PATH",
    "CHECK_INTERVAL_SEC",
]
