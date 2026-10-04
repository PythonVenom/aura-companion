"""ReAct Loop — Reason + Act + Observe + Reflect (ADR-103).

Итеративный цикл: план → действие → наблюдение → оценка → повтор.
Используется для многошаговых задач («напиши сайт», «почини X»).

MVP: 3 итерации макс, рефлексия через простые эвристики.
Позже — LLM-рефлексия.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Step:
    iteration: int
    operator: str
    args: dict
    result: str = ""
    ok: bool = False
    error: str = ""


@dataclass
class Episode:
    goal: str
    steps: list = field(default_factory=list)
    done: bool = False
    reason: str = ""


class ReActLoop:
    MAX_ITERATIONS = 3

    def __init__(self, executor: Callable, reflector: Callable = None):
        """executor(operator, args) → (ok, result_or_error)
        reflector(goal, steps) → (done: bool, reason: str)
        """
        self.executor = executor
        self.reflector = reflector or self._default_reflector

    def _default_reflector(self, goal: str, steps: list) -> tuple:
        """Simple: done если все шаги ok, иначе нет."""
        if not steps:
            return False, "no steps executed"
        if all(s.ok for s in steps):
            return True, "all steps succeeded"
        return False, f"failed: {[s.error for s in steps if not s.ok]}"

    def run(self, goal: str, operators: list) -> Episode:
        ep = Episode(goal=goal)
        for i, op in enumerate(operators[:self.MAX_ITERATIONS], 1):
            step = Step(iteration=i, operator=op.capability, args=op.args)
            try:
                ok, result = self.executor(op.capability, op.args)
                step.ok = bool(ok)
                step.result = str(result)[:200]
            except Exception as e:
                step.ok = False
                step.error = str(e)
            ep.steps.append(step)

        ep.done, ep.reason = self.reflector(goal, ep.steps)
        return ep


def format_episode(ep: Episode) -> str:
    lines = [f"Цель: {ep.goal}", f"Статус: {'DONE' if ep.done else 'FAILED'}"]
    for s in ep.steps:
        mark = "OK" if s.ok else "ERR"
        lines.append(f"  {s.iteration}. [{mark}] {s.operator} → {s.result or s.error}")
    lines.append(f"Итог: {ep.reason}")
    return "\n".join(lines)


__all__ = ["Step", "Episode", "ReActLoop", "format_episode"]

# ============ v4.0 (ADR-123): high-level ReAct ============
import json as _json
import urllib.request as _ur

_REACT_MODEL = "qwen2.5:7b-instruct-q4_K_M"
_REACT_URL = "http://localhost:11434/api/chat"
_REACT_TIMEOUT = 30

REACT_WHITELIST = {
    "music.play", "music.pause", "music.next", "music.prev",
    "time.now", "time.date",
    "app.launch", "browser.open",
    "world.state", "context.recent",
    "care.list", "journal.stats",
    "recon.run", "focus.enable", "focus.disable",
}

_REACT_SYSTEM = (
    "Ты Аура. Рассуждай шаг за шагом. Верни ТОЛЬКО JSON: "
    "{\"thought\":\"...\",\"action\":\"capability.name\" или null,"
    "\"args\":{},\"answer\":\"...\"}. "
    "Не выдумывай capability. Отвечай кратко по-русски."
)


def should_use_react(text):
    raw = text.lower().strip()
    t = " " + raw + " "
    markers = (" и потом ", " и заодно ", " сначала ", " после этого ",
               " если ", " когда ", " а затем ", " затем ")
    if any(m in t for m in markers):
        return True
    if len(raw.split()) > 12:
        return True
    return False


def _llm_json(messages):
    try:
        data = _json.dumps({
            "model": _REACT_MODEL,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_predict": 400},
        }).encode("utf-8")
        req = _ur.Request(_REACT_URL, data=data,
                          headers={"Content-Type": "application/json"})
        with _ur.urlopen(req, timeout=_REACT_TIMEOUT) as r:
            body = _json.loads(r.read().decode("utf-8"))
        text = body.get("message", {}).get("content", "").strip()
        return _json.loads(text) if text else None
    except Exception:
        return None


def react_loop(user_text, max_iterations=3, history=None):
    msgs = [{"role": "system", "content": _REACT_SYSTEM}]
    if history:
        msgs.extend(history[-5:])
    msgs.append({"role": "user", "content": user_text})

    steps = []
    for i in range(max_iterations):
        obj = _llm_json(msgs)
        if not obj:
            break
        thought = str(obj.get("thought", ""))
        action = obj.get("action")
        args = obj.get("args") or {}
        answer = obj.get("answer")
        steps.append({"thought": thought, "action": action,
                      "args": args, "answer": answer})

        if answer and not action:
            return {"answer": answer, "steps": steps, "iterations": i + 1}

        if action:
            if action not in REACT_WHITELIST:
                obs = "capability недоступна: " + action
            else:
                try:
                    from aura.core import dispatcher
                    ok, res = dispatcher.dispatch(action, args)
                    obs = res if ok else "error: " + str(res)
                except Exception as e:
                    obs = "exception: " + str(e)
            msgs.append({"role": "assistant",
                         "content": _json.dumps({"thought": thought,
                                                 "action": action,
                                                 "args": args},
                                                ensure_ascii=False)})
            msgs.append({"role": "user", "content": "Observation: " + obs})

    final = steps[-1].get("answer") if steps else None
    if not final and steps and steps[-1].get("observation"):
        final = steps[-1]["observation"]
    return {"answer": final or "Не смогла",
            "steps": steps, "iterations": len(steps)}
