"""
Агент мозга (AgentBrain).

LLM-фолбэк: если реестр и tool_router не справились — brain.ask().
Ollama, модель qwen2.5:7b-instruct-q4_K_M.

Мигрирован из agents/brain.py (монолит).
Изменения при миграции:
- НЕ наследует BaseAgent (сервис, не агент)
- Убран get_latest_response (мёртвый метод)
- Убран execute (Orchestrator зовёт ask напрямую)
- Убран импорт agents.base

Наука:
- Сервис не знает про оркестратор
- Вызывается через asyncio.to_thread (синхронный)
- Тесты — на моках urllib, без живого Ollama

См. ADR-005.
"""

from __future__ import annotations

import json
import urllib.request


def _has_chinese(text: str) -> bool:
    """True если в тексте есть CJK-иероглифы (китайский, японский)."""
    if not text:
        return False
    for ch in text:
        cp = ord(ch)
        # CJK Unified Ideographs, Hiragana, Katakana, Hangul
        if (0x4E00 <= cp <= 0x9FFF or   # CJK Unified
            0x3400 <= cp <= 0x4DBF or   # CJK Ext A
            0x3040 <= cp <= 0x30FF or   # Hiragana/Katakana
            0xAC00 <= cp <= 0xD7AF):    # Hangul
            return True
    return False


def _chinese_ratio(text: str) -> float:
    """Доля CJK-символов в тексте."""
    if not text:
        return 0.0
    cjk = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF
              or 0x3040 <= ord(ch) <= 0x30FF)
    return cjk / max(len(text), 1)


class AgentBrain:
    """
    LLM-фолбэк Ауры.

    Публичный метод: ask(question) -> str.
    """

    OLLAMA_URL = "http://localhost:11434/api/chat"
    MODEL = "qwen2.5:7b-instruct-q4_K_M"
    TIMEOUT = 30
    MAX_HISTORY = 10

    @property
    def SYSTEM_PROMPT(self) -> str:
        """Динамический промпт из persona + онтология (2026-10-13)."""
        try:
            from aura.persona import build_system_prompt
            base = build_system_prompt()
            return (
                base + "\n\n"
                "ПРАВИЛА:\n"
                "1. История/сказка/анекдот — развёрнуто (10-20 предложений).\n"
                "2. Простой вопрос — кратко (1-3 предложения).\n"
                "3. Объяснение — понятно, без воды.\n"
                "4. ТОЛЬКО кириллица. Никаких иероглифов."
            )
        except Exception:
            return (
                "Ты — Аура, русскоязычный семейный ИИ-компаньон. "
                "Отвечай ТОЛЬКО на русском."
            )

    def __init__(self) -> None:
        self.context_history: list[dict] = []

    # AURA_LLM_FALLBACK_V1 — цепочка моделей + template fallback
    FALLBACK_MODELS = (
        "qwen2.5:7b-instruct-q4_K_M",   # primary
        "qwen2.5:3b",                    # fallback
        "gemma3:270m",                   # tiny
    )
    TEMPLATES = {
        "привет": "Привет! Я Аура. Чем помочь?",
        "как дела": "Всё хорошо. А у тебя как?",
        "спасибо": "Пожалуйста.",
        "пока": "До встречи!",
    }

    def _try_model(self, model: str, messages: list, timeout: int):
        """AURA_LLM_FALLBACK_V2: возвращает (resp, error)."""
        try:
            data = json.dumps({
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 700,
                    "num_ctx": 4096,
                },
            }).encode("utf-8")
            req = urllib.request.Request(
                self.OLLAMA_URL, data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                result = json.loads(r.read().decode("utf-8"))
                content = result.get("message", {}).get("content")
                # Пост-фильтр: китайский = плохой ответ
                if content and _chinese_ratio(content) > 0.10:
                    return None, RuntimeError(
                        f"chinese_detected: {_chinese_ratio(content):.0%} CJK"
                    )
                return content, None
        except Exception as e:
            return None, e

    def _template(self, question: str) -> str | None:
        q = question.lower().strip()
        for key, ans in self.TEMPLATES.items():
            if key in q:
                return ans
        return None

    def ask(self, question: str) -> str:
        """AURA_LLM_FALLBACK_V1: 7b → 3b → 270m → template."""
        self.context_history.append({"role": "user", "content": question})
        if len(self.context_history) > self.MAX_HISTORY:
            self.context_history = self.context_history[-self.MAX_HISTORY:]
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(self.context_history)

        timeouts = (20, 15, 10)
        last_error = None
        empty_seen = False
        for model, t in zip(self.FALLBACK_MODELS, timeouts, strict=False):
            resp, err = self._try_model(model, messages, t)
            if resp:
                self.context_history.append({"role": "assistant", "content": resp})
                return resp
            if err is not None:
                last_error = err
            else:
                empty_seen = True

        # Все модели упали с ошибкой — вернуть ошибку (для тестов и отладки)
        if last_error is not None:
            return f"❌ Ошибка: {last_error}"

        # Модели ответили но пусто
        if empty_seen:
            return "Я не поняла вопрос."

        # Ничего не получилось — template
        tpl = self._template(question)
        if tpl:
            return tpl
        return "Прости, не могу подумать прямо сейчас. Попробуй ещё раз."


__all__ = ["AgentBrain"]
