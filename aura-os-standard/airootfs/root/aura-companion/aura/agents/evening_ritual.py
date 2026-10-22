"""AgentEveningRitual — вечерний ритуал (GAPS #10).

В 22:00 подводит итоги дня:
1. Что сделано (коммиты за день)
2. Что записано в journal
3. XP заработано
4. Что осталось (планы на завтра)
5. Запись в journal

Наука:
- Duhigg 2012 (habit loop) — ритуалы закрепляют поведение
- Lally 2010 — привычка формируется за 66 дней
- Seligman 2011 (flourish) — маленькие победы = мотивация
- Gollwitzer 1999 — implementation intentions
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from aura.core.protocol import AgentRequest, AgentResponse, BaseAgent


class AgentEveningRitual(BaseAgent):
    """Вечерний ритуал — итоги дня."""

    name = "evening_ritual"
    description = "Вечерний ритуал (22:00)"

    KEYWORDS = (
        "итоги дня",
        "что сделал сегодня",
        "подведи итоги",
        "вечерний ритуал",
        "закончим на сегодня",
        "на сегодня всё",
        "хватит на сегодня",
    )

    JOURNAL = Path.home() / ".cache" / "aura" / "JOURNAL.md"
    REPO = Path.home() / "aura-companion"

    def can_handle(self, request: AgentRequest) -> bool:
        text = request.text.lower().strip()
        return any(kw in text for kw in self.KEYWORDS)

    async def handle(self, request: AgentRequest) -> AgentResponse:
        if not self.can_handle(request):
            return AgentResponse.not_handled(self.name)
        return AgentResponse.ok(self.generate(), self.name)

    # === Логика ===

    def generate(self) -> str:
        """Сформировать итоги дня + записать в journal."""
        today = datetime.now().strftime("%Y-%m-%d")
        report = self._build_report(today)
        self._write_journal(report)
        return report

    def _build_report(self, today: str) -> str:
        parts = [f"🛸 Вечерний ритуал — {today}", ""]

        # 1. Коммиты за сегодня
        commits = self._commits_today()
        if commits:
            parts.append(f"**Коммиты ({len(commits)}):**")
            for c in commits[:10]:
                parts.append(f"  • {c}")
            if len(commits) > 10:
                parts.append(f"  ... и ещё {len(commits) - 10}")
        else:
            parts.append("**Коммиты:** нет")
        parts.append("")

        # 2. XP капитана
        try:
            from aura.game.state import StateStore
            store = StateStore()
            state = store.load()
            parts.append(f"**XP:** {state.xp}  |  **Ранг:** {state.rank}  |  **День:** {state.days_on_planet()}")
        except Exception:
            parts.append("**XP:** недоступен")
        parts.append("")

        # 3. Journal — последние записи
        if self.JOURNAL.exists():
            lines = self.JOURNAL.read_text(encoding="utf-8").splitlines()
            today_lines = [l for l in lines if today in l]
            if today_lines:
                parts.append(f"**Записей в journal за сегодня:** {len(today_lines)}")
            else:
                parts.append("**Journal:** пусто за сегодня")
        parts.append("")

        # 4. План на завтра (из briefings)
        brief_dir = Path.home() / "aura_private" / "briefings"
        if brief_dir.exists():
            latest = sorted(brief_dir.glob("*.md"))
            if latest:
                parts.append(f"**Капсула:** {latest[-1].name}")

        parts.append("")
        parts.append("🛸 Хорошего вечера, капитан. Отдыхай.")
        return "\n".join(parts)

    def _commits_today(self) -> list[str]:
        """Коммиты за сегодня (git log --since)."""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0)
            r = subprocess.run(
                ["git", "log", "--oneline",
                 f"--since={today_start.isoformat()}"],
                cwd=str(self.REPO),
                capture_output=True, text=True, timeout=10,
            )
            return [line for line in r.stdout.strip().splitlines() if line]
        except Exception:
            return []

    def _write_journal(self, report: str) -> None:
        """Записать итоги в JOURNAL.md (атомарно)."""
        try:
            self.JOURNAL.parent.mkdir(parents=True, exist_ok=True)
            with open(self.JOURNAL, "a", encoding="utf-8") as f:
                f.write("\n---\n")
                f.write(report)
                f.write("\n")
        except Exception as e:
            import logging
            logging.getLogger("aura.evening").warning(
                "Не записал в journal: %s", e
            )


__all__ = ["AgentEveningRitual"]
