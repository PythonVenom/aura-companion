"""Problem — структура одной задачи-фазы.

Не «враг с HP», а конкретная проблема с паттерном и кодом.
Turn-based: каждая фаза — один Problem, до решения.

Наука: McGonigal 2011 (игра для реальных задач),
       Csikszentmihalyi 1990 (flow через пошаговость).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.game.patterns import Pattern, pattern_for


@dataclass
class Problem:
    """Одна проблема. Одна фаза. Одно решение."""

    code: str                # Ruff-код: F541, SIM105
    sector: str              # файл
    line: int                # строка
    raw_message: str = ""    # оригинальный текст ruff

    # Состояние решения
    attempts: int = 0
    recon_done: bool = False  # разведка проведена?
    read_done: bool = False   # паттерн прочитан?
    solved: bool = False

    # История проб
    history: list[str] = field(default_factory=list)

    @property
    def max_hp(self) -> int:
        """HP цели по сложности паттерна."""
        return 50 + self.pattern.difficulty * 20

    @property
    def hp(self) -> int:
        """Текущий HP. Урон от промахов — по сложности."""
        return max(10, self.max_hp - self._total_damage)

    @property
    def _total_damage(self) -> int:
        """Суммарный урон. Умная игра = меньше урона."""
        base = self.pattern.difficulty * 5
        # Каждая попытка дала урон
        dmg = base * self.attempts
        # Разведка/чтение срезают урон
        if self.recon_done:
            dmg = int(dmg * 0.7)
        if self.read_done:
            dmg = int(dmg * 0.5)
        return dmg

    @property
    def importance(self) -> str:
        """Важность цели — по сложности."""
        d = self.pattern.difficulty
        return {1: "мелкая", 2: "обычная", 3: "важная",
                4: "серьёзная", 5: "критичная"}.get(d, "?")

    @property
    def pattern(self) -> Pattern:
        """Паттерн этого кода."""
        return pattern_for(self.code)

    def apply_recon(self) -> str:
        """Разведка: что узнали."""
        self.recon_done = True
        self.attempts += 1
        p = self.pattern
        return (
            f"🔍 Разведка сектора {self.sector}:{self.line}\n"
            f"   Паттерн: {p.title}\n"
            f"   Стратегия: {p.strategy}\n"
            f"   Сложность: {p.difficulty}/5"
        )

    def try_solve(self, strategy: str) -> tuple[bool, str]:
        """Попытка решить. True, если стратегия совпала."""
        self.attempts += 1
        self.history.append(strategy)
        p = self.pattern

        # Успех, если стратегия совпадает с паттерном
        if strategy == p.strategy:
            self.solved = True
            return True, f"✅ Верно: {p.title}"

        # Разведка помогает
        if strategy == "recon" and not self.recon_done:
            return False, self.apply_recon()

        # Иначе — попробуй ещё
        hints = {
            "patch": "попробуй точечную правку",
            "rewrite": "перепиши целиком",
            "recon": "собери контекст",
            "autofix": "пусть ruff сам",
            "reset": "откати и подумай",
            "defer": "отложи",
            "suppress": "замени try/except/pass",
            "remove_prefix": "убери лишний f''",
            "remove_import": "удали import",
            "wrap": "перенеси строку",
            "alias": "замени на короткий alias",
            "bind_default": "привяжи default-arg",
            "sort": "отсортируй",
        }
        hint = hints.get(p.strategy, "попробуй другой подход")
        return False, f"❌ Не то. Подсказка: {hint}"


__all__ = ["Problem"]
