"""Quiz Game — простой когнитивный тренажёр для elder-care.

Наука: Cognitive Training (Rebok 2014), SeniorCare.
Адаптировано для бати: память, внимание, счёт.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class QuizQuestion:
    text: str
    answer: str
    hint: str = ""


@dataclass
class QuizSession:
    questions: list[QuizQuestion] = field(default_factory=list)
    current: int = 0
    score: int = 0
    active: bool = False

    def start(self, n: int = 5) -> QuizQuestion:
        self.questions = _generate_questions(n)
        self.current = 0
        self.score = 0
        self.active = True
        return self.questions[0]

    def answer(self, text: str) -> tuple[bool, str]:
        if not self.active or self.current >= len(self.questions):
            return False, "Игра завершена."
        q = self.questions[self.current]
        correct = q.answer.lower() in text.lower()
        if correct:
            self.score += 1
        self.current += 1
        if self.current >= len(self.questions):
            self.active = False
            return correct, f"{'✅' if correct else '❌'} Правильный: {q.answer}. Итог: {self.score}/{len(self.questions)}"
        nq = self.questions[self.current]
        return correct, f"{'✅' if correct else '❌'} Правильный: {q.answer}. Следующий: {nq.text}"


_SESSION: QuizSession | None = None


def get_session() -> QuizSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = QuizSession()
    return _SESSION


def _generate_questions(n: int) -> list[QuizQuestion]:
    """Сгенерировать когнитивные вопросы."""
    pool = [
        QuizQuestion("Сколько будет 5 + 3?", "8", "Посчитай"),
        QuizQuestion("Сколько будет 10 - 4?", "6", "Посчитай"),
        QuizQuestion("Назови столицу России", "москва", "Город"),
        QuizQuestion("Сколько дней в неделе?", "7", "Посчитай"),
        QuizQuestion("Какого цвета трава?", "зелёная", "Цвет"),
        QuizQuestion("Сколько будет 2 × 4?", "8", "Посчитай"),
        QuizQuestion("Назови время года после зимы", "весна", "Сезон"),
        QuizQuestion("Сколько месяцев в году?", "12", "Посчитай"),
        QuizQuestion("Какой день после пятницы?", "суббота", "День"),
        QuizQuestion("Сколько будет 20 + 15?", "35", "Посчитай"),
    ]
    random.shuffle(pool)
    return pool[:n]


__all__ = ["QuizQuestion", "QuizSession", "get_session"]
