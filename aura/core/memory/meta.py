"""Meta-Memory — confidence & calibration (ADR-131, 10-й слой).

Наука:
- Kadavath, S. et al. (2022). Language Models (Mostly) Know What They Know. Anthropic.
- Guo, C. et al. (2017). On Calibration of Modern Neural Networks. ICML.

confidence = alpha*extraction + beta*evidence + gamma*recency + delta*consistency
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass


ALPHA = 0.4   # extraction score
BETA = 0.3    # evidence count
GAMMA = 0.2   # recency
DELTA = 0.1   # consistency


@dataclass
class Confidence:
    value: float
    label: str    # "sure" | "probable" | "unsure" | "unknown"


def _recency(ts: float, halflife_days: float = 30.0) -> float:
    if ts <= 0:
        return 1.0
    age = (time.time() - ts) / 86400.0
    return math.exp(-age * math.log(2) / halflife_days)


def score(extraction: float = 0.7,
          evidence_count: int = 1,
          ts: float = 0.0,
          consistency: float = 0.8) -> Confidence:
    evid_norm = 1.0 - math.exp(-evidence_count / 3.0)
    rec = _recency(ts) if ts else 1.0
    val = (ALPHA * extraction
           + BETA * evid_norm
           + GAMMA * rec
           + DELTA * consistency)
    val = max(0.0, min(1.0, val))
    if val > 0.8:
        label = "sure"
    elif val > 0.5:
        label = "probable"
    elif val > 0.0:
        label = "unsure"
    else:
        label = "unknown"
    return Confidence(value=round(val, 3), label=label)


def hedged(response: str, conf: Confidence, lang: str = "ru") -> str:
    """Добавить хедж в зависимости от уверенности."""
    if conf.label == "sure":
        return response
    if conf.label == "probable":
        pre = {"ru": "Кажется, ", "en": "I think "}.get(lang, "")
        return pre + response
    if conf.label == "unsure":
        pre = {"ru": "Не уверена, но возможно: ",
               "en": "Not sure, but maybe: "}.get(lang, "")
        return pre + response
    return {"ru": "Не помню.", "en": "I don't remember."}.get(lang, "?")


def calibration_error(pairs: list) -> float:
    """ECE (Expected Calibration Error). pairs=[(conf, correct:bool), ...]."""
    if not pairs:
        return 0.0
    bins = [[] for _ in range(10)]
    for c, ok in pairs:
        bins[min(9, int(c * 10))].append(ok)
    ece = 0.0
    n = len(pairs)
    for i, b in enumerate(bins):
        if not b:
            continue
        avg_conf = (i + 0.5) / 10
        acc = sum(b) / len(b)
        ece += (len(b) / n) * abs(avg_conf - acc)
    return round(ece, 4)
