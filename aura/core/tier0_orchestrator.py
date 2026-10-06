"""Tier 0 Orchestrator — без LLM (ADR-152)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tier0Result:
    intent: Optional[str]
    confidence: float
    response: str
    source: str


class Tier0Orchestrator:
    def __init__(self) -> None:
        from aura.core.intent_classifier import classify
        from aura.core.templates import render_now
        self._classify = classify
        self._render = render_now

    def process(self, text: str) -> Tier0Result:
        try:
            from aura.core.constitution import check as cc
            allowed, refusal, _ = cc(text)
            if not allowed:
                return Tier0Result(None, 1.0, refusal, "constitution")
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.tier0_orchestrator').warning(
                'tier0_orchestrator error: %s', e)
        intent, conf = self._classify(text)
        if intent is None:
            return Tier0Result(None, conf,
                "Не расслышала. Повторите, пожалуйста.", "fallback")
        try:
            from aura.core import dispatcher
            h = dispatcher.get_handler(intent)
            if h is not None:
                ok, res = dispatcher.dispatch(intent, {})
                if ok:
                    return Tier0Result(intent, conf, str(res)[:200], "dispatcher")
        except Exception as e:
            # F-006: не глотать (раздел 17 промта)
            import logging
            logging.getLogger('aura.tier0_orchestrator').warning(
                'tier0_orchestrator error: %s', e)
        return Tier0Result(intent, conf, self._render(intent), "template")


_SINGLETON: Optional[Tier0Orchestrator] = None


def get_tier0() -> Tier0Orchestrator:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = Tier0Orchestrator()
    return _SINGLETON
