"""Tier 0 NLU — intent classifier (ADR-152).

Наука:
- Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2016).
  Bag of Tricks for Efficient Text Classification. EACL 2017. arXiv:1607.01759.
- Warden, P. (2018). Speech Commands. arXiv:1804.03209.
"""
from __future__ import annotations
import re
from collections import Counter
from typing import Optional

INTENTS = {
    "music.play":   ["включи музыку", "поставь песню", "музыку хочу", "играй",
                     "включи радио", "поставь шансон"],
    "music.pause":  ["пауза", "останови", "стоп музыку", "выключи музыку", "тихо", "замолчи"],
    "music.next":   ["следующая", "дальше", "переключи", "следующий трек", "другую песню"],
    "music.prev":   ["предыдущая", "назад", "верни", "прошлый трек"],
    "music.volume_up":   ["громче", "прибавь звук", "сделай громче"],
    "music.volume_down": ["тише", "убавь звук", "сделай тише"],
    "time.now":     ["который час", "сколько времени", "время", "часы"],
    "time.date":    ["какое число", "какая дата", "какой день", "сегодня"],
    "care.remind":  ["напомни", "напоминание", "не забудь", "поставь будильник", "разбуди"],
    "care.list":    ["какие напоминания", "что я должен", "мои дела", "список дел"],
    "weather.now":  ["какая погода", "погода", "дождь", "холодно ли", "на улице"],
    "phone.call":   ["позвони", "набери", "позвони маме", "позвони сыну", "вызови"],
    "emergency":    ["помоги", "плохо", "вызови скорую", "позвони 103", "мне плохо", "врача"],
    "vk.open":      ["открой вк", "вконтакте", "открой вконтакте"],
    "vk.messages":  ["сообщения", "кто написал", "вк сообщения", "прочитай вк"],
    "news":         ["новости", "что нового", "что в мире"],
    "smart_home.light_on":  ["включи свет", "зажги", "свет"],
    "smart_home.light_off": ["выключи свет", "погаси", "темно"],
    "smart_home.tv_on":     ["включи телевизор", "телик"],
    "smart_home.tv_off":    ["выключи телевизор"],
    "yes":          ["да", "хорошо", "ок", "ага", "конечно"],
    "no":           ["нет", "не надо", "отмена", "не хочу"],
    "stop":         ["хватит", "остановись", "замолчи", "стоп"],
}


def _tokens(text: str):
    return re.findall(r"[а-яёa-z0-9]+", text.lower())


class IntentClassifier:
    def __init__(self) -> None:
        self._ref: dict = {}
        self._counts: dict = {}
        for intent, phrases in INTENTS.items():
            c = Counter()
            for p in phrases:
                c.update(_tokens(p))
            self._ref[intent] = c
            self._counts[intent] = sum(c.values())

    def classify(self, text: str):
        toks = _tokens(text)
        if not toks:
            return None, 0.0
        scores = {}
        for intent, ref in self._ref.items():
            s = sum(ref.get(t, 0) / (self._counts[intent] + 1) for t in toks)
            scores[intent] = s
        if not scores:
            return None, 0.0
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1.0
        conf = scores[best] / total
        return (best, round(conf, 3)) if conf >= 0.15 else (None, round(conf, 3))


_SINGLETON: Optional[IntentClassifier] = None


def classify(text: str):
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = IntentClassifier()
    return _SINGLETON.classify(text)


def all_intents() -> list:
    return sorted(INTENTS.keys())
