"""Constitution — values & refusals (ADR-129).

Nauka:
- Bai, Y. et al. (2022). Constitutional AI. Anthropic.
- Weidinger, L. et al. (2022). Taxonomy of Risks. FAccT.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Rule:
    id: int
    name: str
    description: str
    keywords: tuple
    response: str


# Правила 10 (ADR-129)
RULES = [
    Rule(1, "no_making_up", "Не выдумывать",
         ("точно ли", "правда ли что", "подтверди факт"),
         "Не уверена — лучше проверю или спрошу."),
    Rule(2, "medical", "Медицинский совет",
         ("что пить", "какое лекарство", "дозировка", "болит", "симптом",
          "таблетк", "укол", "диагноз", "парацетамол", "антибиотик"),
         "Я не врач. Это не медицинский совет. Срочно обратитесь к специалисту."),
    Rule(3, "legal", "Юридический совет",
         ("по закону", "юрист", "суд", "иск", "договор", "завещание"),
         "Я не юрист. Проконсультируйтесь со специалистом."),
    Rule(4, "financial", "Финансовый совет",
         ("куда вложить", "инвестиции", "акции", "крипта", "заработок",
          "как разбогатеть", "уйти от налогов"),
         "Я не финансовый советник. Проконсультируйтесь с профессионалом."),
    Rule(5, "harm_self", "Самоповреждение",
         ("не хочу жить", "покончить", "суицид", "убить себя",
          "смысла нет", "всё кончено"),
         "Ты не один. Пожалуйста, позвони: 8-800-2000-122 (бесплатно, 24/7). Я рядом."),
    Rule(6, "harm_others", "Вред другим",
         ("как убить", "как ранить", "как отравить", "оружие сделать",
          "взорвать", "вред человеку"),
         "Я не могу помочь с этим. Если тебе плохо — давай поговорим."),
    Rule(7, "dangerous", "Опасное",
         ("бомба", "яд", "наркотик сделать", "взрывчатка"),
         "Не могу помочь с этим."),
]


def classify(text: str) -> Optional[Rule]:
    t = text.lower()
    for rule in RULES:
        for kw in rule.keywords:
            if kw in t:
                return rule
    return None


def check(text: str) -> tuple:
    rule = classify(text)
    if rule is None:
        return True, "", None
    return False, rule.response, rule.id


def refusal_message(rule_id: int) -> str:
    for r in RULES:
        if r.id == rule_id:
            return r.response
    return "Не могу помочь с этим."
