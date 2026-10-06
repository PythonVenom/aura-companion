"""Context Management — sliding + summary + priority recall (ADR-124).

Наука:
- Liu, N. F. et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. TACL.
- Packer, C. et al. (2023). MemGPT: Towards LLMs as Operating Systems.
- Baddeley & Hitch (1974). Working Memory.

Стратегия:
1. Sliding window — последние N сообщений
2. Summary buffer — каждые 10 реплик → 1 абзац (LLM)
3. Priority recall — top-K из memory recall в начало
"""
from __future__ import annotations
import json
import urllib.request
from pathlib import Path
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
SUMMARY_PATH = Path.home() / ".cache" / "aura" / "context_summary.txt"


class ContextManager:
    def __init__(self, window: int = 10, summary_every: int = 10) -> None:
        self.window = window
        self.summary_every = summary_every
        self._summary = self._load_summary()
        self._since_summary = 0

    def _load_summary(self) -> str:
        if SUMMARY_PATH.exists():
            try:
                return SUMMARY_PATH.read_text(encoding="utf-8").strip()
            except Exception:
                return ""
        return ""

    def _save_summary(self, text: str) -> None:
        try:
            SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
            SUMMARY_PATH.write_text(text, encoding="utf-8")
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.context_manager').warning(
                'context_manager error: %s', e)

    def summary(self) -> str:
        return self._summary

    def _llm_summarize(self, old_summary: str, new_turns: list) -> str:
        lines = [f"{t.role}: {t.text}" for t in new_turns]
        prompt = (
            f"Предыдущая сводка диалога: {old_summary or '(нет)'}\n\n"
            f"Новые реплики:\n" + "\n".join(lines) + "\n\n"
            "Обнови сводку — 2-3 предложения, только ключевые факты и темы. "
            "Без приветствий, без воды."
        )
        try:
            data = json.dumps({
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 200},
            }).encode("utf-8")
            req = urllib.request.Request(OLLAMA_URL, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as r:
                body = json.loads(r.read().decode("utf-8"))
            return body.get("message", {}).get("content", "").strip() or old_summary
        except Exception:
            return old_summary

    def push(self, role: str, text: str) -> None:
        from aura.core.memory.working import get_working
        get_working().push(role, text)
        self._since_summary += 1
        if self._since_summary >= self.summary_every:
            self._rollup()
            self._since_summary = 0

    def _rollup(self) -> None:
        from aura.core.memory.working import get_working
        w = get_working()
        turns = w.all()
        if len(turns) <= self.window:
            return
        old = turns[:-self.window]
        self._summary = self._llm_summarize(self._summary, old)
        self._save_summary(self._summary)

    def build_messages(self, user_text: str, recall_hits: Optional[list] = None) -> list[dict]:
        """Собрать messages для LLM: system + summary + recall + last window + user."""
        messages: list[dict] = []

        # System
        try:
            from aura.i18n import t
            sys_msg = t("llm.system")
        except Exception:
            sys_msg = "Ты — Аура, семейный ИИ-компаньон. Отвечай кратко, по-русски."
        messages.append({"role": "system", "content": sys_msg})

        # Summary (если есть)
        if self._summary:
            messages.append({"role": "system",
                             "content": f"Сводка прошлого разговора: {self._summary}"})

        # Priority recall — топ-5 в начало (не в середину — Liu 2023)
        if recall_hits:
            lines = []
            for h in recall_hits[:5]:
                if h.source == "semantic":
                    p = h.payload
                    lines.append(f"- {p.get('subject')} {p.get('predicate')} {p.get('object')}")
                elif h.source == "social":
                    p = h.payload
                    if "kind" in p:
                        lines.append(f"- {p.get('src')} {p.get('kind')} {p.get('dst')}")
                    elif "event" in p:
                        lines.append(f"- событие {p.get('event')} у {p.get('of')} ({p.get('date')})")
            if lines:
                messages.append({"role": "system",
                                 "content": "Релевантные воспоминания:\n" + "\n".join(lines)})

        # Working window
        from aura.core.memory.working import get_working
        messages.extend(get_working().as_messages(self.window))

        # Current user message
        messages.append({"role": "user", "content": user_text})
        return messages


_SINGLETON: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = ContextManager()
    return _SINGLETON
