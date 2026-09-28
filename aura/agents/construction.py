"""ConstructionCalc — калькулятор ремонта (ADR-044 шаг 6)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


# Нормы расхода на м² (ГОСТ-приближение)
NORMS = {
    "плитка": {"norm": 1.10, "unit": "м²", "desc": "плитка с запасом 10%"},
    "штукатурка": {"norm": 15.0, "unit": "кг", "desc": "15 кг/м² при слое 10мм"},
    "шпаклевка": {"norm": 1.2, "unit": "кг", "desc": "1.2 кг/м² финишная"},
    "краска": {"norm": 0.25, "unit": "л", "desc": "0.25 л/м² в 2 слоя"},
    "обои": {"norm": 1.05, "unit": "рул", "desc": "1.05 рулона/м² (10м×0.53)"},
    "ламинат": {"norm": 1.07, "unit": "м²", "desc": "с запасом 7%"},
    "линолеум": {"norm": 1.05, "unit": "м²", "desc": "с запасом 5%"},
    "грунтовка": {"norm": 0.15, "unit": "л", "desc": "0.15 л/м²"},
    "клей_плитка": {"norm": 4.5, "unit": "кг", "desc": "4.5 кг/м²"},
    "гипсокартон": {"norm": 1.05, "unit": "лист", "desc": "1.05 листа 2.5×1.2 м"},
}


@dataclass
class CalcResult:
    material: str
    area: float
    amount: float
    unit: str
    description: str


def calc_material(material: str, area: float) -> CalcResult | None:
    """Рассчитать количество материала на площадь."""
    key = material.lower().replace("ё", "е")
    if key not in NORMS:
        return None
    n = NORMS[key]
    return CalcResult(
        material=material,
        area=area,
        amount=round(area * n["norm"], 2),
        unit=n["unit"],
        description=n["desc"],
    )


class AgentConstruction(BaseAgent):
    """Калькулятор стройматериалов.

    Команды:
      - «сколько плитки на 29 м²»
      - «сколько штукатурки на 100 м²»
      - «какие материалы знаешь»
    """

    name = "construction"
    MODULE_ALWAYS = True
    KEYWORDS = (
        "сколько плитк", "сколько штукатурк", "сколько обоев",
        "сколько краск", "сколько ламинат", "сколько линолеум",
        "сколько шпаклевк", "сколько грунтовк", "какие материалы",
        "норма расхода",
    )

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        text = request.text.lower()

        if "какие материалы" in text or "норма расхода" in text:
            names = sorted(NORMS.keys())
            return AgentResponse.ok(
                "📐 Материалы: " + ", ".join(names), self.name
            )

        # Парсим: материал + площадь
        m = re.search(r"на\s+(\d+(?:[.,]\d+)?)\s*м", text)
        if not m:
            return AgentResponse.ok(
                "Скажи: «сколько плитки на 29 м²»", self.name
            )
        area = float(m.group(1).replace(",", "."))

        # Определяем материал
        for key in NORMS:
            kw_variants = (key, key.replace("_", " "))
            if any(v in text for v in kw_variants):
                result = calc_material(key, area)
                if result:
                    return AgentResponse.ok(
                        f"📐 {result.material}: {result.amount} {result.unit} "
                        f"на {area} м² ({result.description})",
                        self.name,
                    )

        return AgentResponse.ok(
            "Не поняла материал. Скажи: «сколько плитки на 29 м²»", self.name
        )


__all__ = ["AgentConstruction", "calc_material", "NORMS", "CalcResult"]
