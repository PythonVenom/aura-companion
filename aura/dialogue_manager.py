"""
Dialogue Manager — сценарный диалог для мессенджеров (ADR-013).

Frame-based dialogue. Сценарий = keywords + required_slots + questions.
Менеджер читает слоты, решает шаг, зовёт агента через get_agent().

Работает поверх ADR-012 (FSM). Когда активен сценарий —
команды идут сюда, а не в обычный цикл.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

TIMEOUT_SEC = 120.0   # 2 минуты на весь сценарий

# Bug 8: слова, которые означают начало ТЕКСТА, не имени чата.
# «петруха чип тест финал» → chat=«петруха чип», text=«тест финал».
_TEXT_MARKERS = {
    "привет", "приветствую", "здравствуй", "здравствуйте",
    "как", "что", "где", "когда", "кто", "зачем", "почему", "куда",
    "тест", "финал", "проверка", "дела", "новости", "спасибо",
    "покажи", "скажи", "давай", "мне", "нам", "ему", "ей", "им",
    "хочу", "буду", "надо", "нужно", "можно", "не", "да",
}

_MAX_CHAT_WORDS = 3


def _split_chat_text(words: list) -> tuple:
    """Разделить на (chat, text). chat — до 3 слов без маркеров текста."""
    chat_words = []
    for i, w in enumerate(words):
        clean = w.strip(".,!? ").lower()
        if clean in _TEXT_MARKERS:
            break
        chat_words.append(w)
        if len(chat_words) >= _MAX_CHAT_WORDS:
            break
    if not chat_words:
        chat_words = [words[0]]
    chat = " ".join(chat_words)
    text = " ".join(words[len(chat_words):]).strip()
    return chat, text


@dataclass
class Scenario:
    name: str
    agent: str
    keywords: list
    required_slots: list
    questions: dict = field(default_factory=dict)


@dataclass
class DialogueState:
    scenario: Scenario | None = None
    slots: dict = field(default_factory=dict)
    started_at: float = 0.0
    awaiting_confirm: bool = False


class DialogueManager:
    """Сценарный менеджер диалога для мессенджеров."""

    def __init__(self, scenarios, get_agent):
        self.scenarios = {s.name: s for s in scenarios}
        self.get_agent = get_agent
        self.state = DialogueState()

    # --- Публичные ---

    def reset(self):
        self.state = DialogueState()

    def is_active(self):
        if self.state.scenario is None:
            return False
        if time.time() - self.state.started_at > TIMEOUT_SEC:
            self.reset()
            return False
        return True

    def detect(self, text):
        """Найти сценарий по keywords. None если не наш."""
        t = text.lower()
        for s in self.scenarios.values():
            if any(kw in t for kw in s.keywords):
                return s
        return None

    def start(self, scenario):
        self.state = DialogueState(
            scenario=scenario,
            started_at=time.time(),
        )

    def process(self, text):
        """
        Обработать команду в контексте сценария.
        Возвращает ответ (str) или None — если сценарий не активен.
        """
        if not self.is_active():
            return None

        low = text.lower().strip()

        # Отмена
        if "отмена" in low or "стоп" in low:
            self.reset()
            return "Отменила"

        # Подтверждение
        if self.state.awaiting_confirm:
            if any(w in low for w in ("да", "отправ", "ок")):
                agent = self.get_agent(self.state.scenario.agent)
                self.reset()
                if agent and hasattr(agent, "finalize_send"):
                    return agent.finalize_send()
                return "Отправила"
            if any(w in low for w in ("нет", "не надо", "не отправляй")):
                agent = self.get_agent(self.state.scenario.agent)
                self.reset()
                if agent and hasattr(agent, "clear_input"):
                    agent.clear_input()
                return "Отменила"
            return "Скажи да или нет"

        # Извлечь слоты
        self._extract_slots(text)

        # Что-то не хватает?
        missing = self._missing_slot()
        if missing:
            return self.state.scenario.questions.get(missing, f"Что {missing}?")

        # Всё есть — выполнить
        return self._execute()

    # --- Внутренние ---

    def _missing_slot(self):
        for s in self.state.scenario.required_slots:
            if s not in self.state.slots:
                return s
        return None

    def _extract_after(self, text, markers):
        for m in markers:
            idx = text.lower().find(m)
            if idx >= 0:
                rest = text[idx + len(m):].strip(".,!? ")
                if rest:
                    return rest
        return ""

    def _extract_slots(self, text):
        sc = self.state.scenario
        low = text.lower()

        # chat: «чату X», «чат X», «с X», «для X»
        if "chat" in sc.required_slots and "chat" not in self.state.slots:
            chat = self._extract_after(text, ["чату ", "чат ", "для "])
            if not chat:
                # «напиши Петруха ...» — берём первое слово после «напиши»
                chat = self._extract_after(text, ["напиши ", "отправь "])
            if chat:
                parts = chat.split()
                if parts:
                    chat_part, text_part = _split_chat_text(parts)
                    self.state.slots["chat"] = chat_part.strip(".,!?")
                    if text_part and "text" in sc.required_slots:
                        self.state.slots["text"] = text_part

        # text: если chat уже есть и есть остаток
        if "text" in sc.required_slots and "text" not in self.state.slots:
            c = self.state.slots.get("chat", "")
            if c:
                idx = low.find(c.lower())
                if idx >= 0:
                    rest = text[idx + len(c):].strip(".,!? ")
                    if rest:
                        self.state.slots["text"] = rest

    def _execute(self):
        sc = self.state.scenario
        agent = self.get_agent(sc.agent)
        if not agent:
            self.reset()
            return "Агент не найден"

        results = []

        # find_chat
        if "chat" in self.state.slots and hasattr(agent, "find_chat"):
            r = agent.find_chat(self.state.slots["chat"])
            results.append(r)

        # send_message
        if "text" in self.state.slots and hasattr(agent, "send_message"):
            r = agent.send_message(
                self.state.slots.get("chat", ""),
                self.state.slots["text"],
            )
            results.append(r)

        self.state.awaiting_confirm = True
        text = self.state.slots.get("text", "")
        prefix = " ".join(results)
        return f"{prefix} Написала: «{text}». Отправить?"


SCENARIOS = [
    Scenario(
        name="messenger_send",
        agent="messenger",
        keywords=["напиши", "отправить", "сообщение"],
        required_slots=["chat", "text"],
        questions={
            "chat": "Кому написать?",
            "text": "Что написать?",
        },
    ),
]


__all__ = ["SCENARIOS", "TIMEOUT_SEC", "DialogueManager", "DialogueState", "Scenario"]
