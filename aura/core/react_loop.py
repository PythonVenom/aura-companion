"""Full ReAct Loop — plan/act/observe/reflect (ADR-123).

Наука:
- Yao, S. et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. ICLR 2023.
- Shinn, N. et al. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. NeurIPS.
- Wang, X. et al. (2022). Self-Consistency Improves Chain of Thought Reasoning. ICLR 2023.
- Yao, S. et al. (2023). Tree of Thoughts: Deliberate Problem Solving. NeurIPS.

Архитектура:
    User input → THOUGHT → ACTION → OBSERVE → (loop ≤3) → ANSWER

Безопасность:
- max_iterations=3
- whitelist capability (не все handler доступны)
- каждый шаг → observability.log
- при ошибке → graceful fallback
"""
from __future__ import annotations
import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct-q4_K_M"
TIMEOUT = 30

# Capability, доступные ReAct-агенту (не power.*, не control.*)
REACT_WHITELIST = {
    "music.play", "music.pause", "music.next", "music.prev",
    "time.now", "time.date",
    "app.launch", "browser.open",
    "world.state", "context.recent",
    "care.list", "journal.stats",
    "recon.run", "focus.enable", "focus.disable",
}

SYSTEM_PROMPT = """Ты — Аура, локальный семейный ИИ. Ты рассуждаешь шаг за шагом (ReAct).

На каждом шаге верни ТОЛЬКО JSON:
{"thought": "...", "action": "capability.name" или null, "args": {}, "answer": "..."}

Правила:
1. Если нужна информация/действие — задай action.
2. Если можешь ответить прямо — задай answer, action=null.
3. Не выдумывай capability, которых нет в списке.
4. Отвечай кратко, по-русски.

Доступные capabilities:
- music.play (query), music.pause, music.next, music.prev
- time.now, time.date
- app.launch (name), browser.open (url)
- world.state, context.recent (minutes)
- care.list, journal.stats (days)
- recon.run
- focus.enable, focus.disable
"""


@dataclass
class ReActStep:
    thought: str
    action: Optional[str]
    args: dict
    observation: Optional[str] = None
    answer: Optional[str] = None


def _llm(messages: list[dict]) -> Optional[dict]:
    try:
        data = json.dumps({
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_predict": 400},
        }).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = json.loads(r.read().decode("utf-8"))
        text = body.get("message", {}).get("content", "").strip()
        return json.loads(text) if text else None
    except Exception:
        return None


def react_loop(user_text: str, max_iterations: int = 3,
               history: Optional[list[dict]] = None) -> dict:
    """Запустить ReAct. Возвращает {answer, steps, iterations}."""
    try:
        from aura.observability import new_trace, log
        new_trace("react")
    except Exception:
        log = lambda *a, **kw: None

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-5:])
    messages.append({"role": "user", "content": user_text})

    steps: list[ReActStep] = []
    for i in range(max_iterations):
        obj = _llm(messages)
        if not obj:
            log("react.llm_fail", iteration=i)
            break

        step = ReActStep(
            thought=str(obj.get("thought", "")),
            action=obj.get("action"),
            args=obj.get("args") or {},
            answer=obj.get("answer"),
        )
        steps.append(step)
        log("react.step", iteration=i, action=step.action or "answer")

        if step.answer and not step.action:
            return {"answer": step.answer, "steps": steps, "iterations": i + 1}

        if step.action:
            if step.action not in REACT_WHITELIST:
                step.observation = f"capability '{step.action}' недоступна"
            else:
                try:
                    from aura.core import dispatcher
                    ok, res = dispatcher.dispatch(step.action, step.args)
                    step.observation = res if ok else f"error: {res}"
                except Exception as e:
                    step.observation = f"exception: {e}"
            messages.append({"role": "assistant", "content": json.dumps({
                "thought": step.thought, "action": step.action, "args": step.args
            }, ensure_ascii=False)})
            messages.append({"role": "user", "content": f"Observation: {step.observation}"})

    # Финальный ответ если не было answer
    final = steps[-1].answer if steps and steps[-1].answer else             (steps[-1].observation if steps else "Не смогла")
    return {"answer": final, "steps": steps, "iterations": len(steps)}


def should_use_react(text: str) -> bool:
    """Эвристика: использовать ли ReAct вместо простого dispatch."""
    t = text.lower()
    # Многошаговые маркеры
    markers = (" и потом ", " и заодно ", " сначала ", " после этого ",
               " если ", " когда ", " а затем ", " затем ")
    if any(m in t for m in markers):
        return True
    # Длинные запросы
    if len(text.split()) > 12:
        return True
    return False
