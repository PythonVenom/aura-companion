"""Aura Mentor TUI — терминальный интерфейс Skill Graph.
Наука: Octalysis (Yu-kai Chou), Flow Theory (Csikszentmihalyi).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "aura_project"))

from aura.kernel.agents.mentor.path import PathTracker
from aura.kernel.agents.mentor.ledger import ProfileLedger
from aura.kernel.agents.mentor.schema import SKILLS_SEED
from aura.kernel.agents.mentor.schema_extra import ALL_EXTRA
from aura.kernel.agents.mentor.schema_branches import ALL_BRANCHES


# ANSI-цвета (без зависимостей)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

ICONS = {
    "locked": "🔒",
    "available": "🟢",
    "in_progress": "🟡",
    "done": "✅",
}


class MentorTUI:
    def __init__(self, user: str = "batya"):
        self.user = user
        self.tracker = PathTracker(user)
        self.ledger = ProfileLedger(user)

    def clear(self):
        print("\033[2J\033[H", end="")

    def header(self):
        s = self.tracker.stats()
        c = self.ledger.career_score()
        bar_len = 30
        filled = int(bar_len * s["done"] / s["total"]) if s["total"] else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"{BOLD}{CYAN}🛸 AURA MENTOR{RESET} · {self.user}")
        print(f"{DIM}{'─' * 60}{RESET}")
        print(f"  Прогресс: {GREEN}{s['done']}/{s['total']}{RESET}  [{bar}] {s['percent']}%")
        print(f"  Карьера:  {MAGENTA}{c['career_score']}{RESET} · ачивок: {c['achievements']}")
        print(f"  Статус:   🟢 {s['available']} доступно · 🟡 {s['in_progress']} в работе · "
              f"🔒 {s['locked']} заблокировано · ✅ {s['done']} готово")
        print()

    BRANCH_LABELS = {
        "it": "💻 IT",
        "art": "🎨 ART",
        "medicine": "🏥 MEDICINE",
        "business": "💼 BUSINESS",
        "lang": "🌐 LANG",
    }

    def skills_list(self):
        print(f"{BOLD}📚 НАВЫКИ (все ветки):{RESET}")
        all_skills = {s.id: s for s in SKILLS_SEED + ALL_EXTRA + ALL_BRANCHES}
        by_branch = {}
        for sid, p in self.tracker.progress.items():
            skill = all_skills.get(sid) or self.tracker.skills.get(sid)
            if not skill:
                continue
            by_branch.setdefault(skill.branch, []).append((skill, p))

        for branch, items in by_branch.items():
            label = self.BRANCH_LABELS.get(branch, branch)
            print(f"  {BOLD}{label}{RESET}")
            for skill, p in items:
                icon = ICONS.get(p.status, "❓")
                color = {
                    "locked": DIM, "available": GREEN,
                    "in_progress": YELLOW, "done": CYAN,
                }.get(p.status, "")
                print(f"    {icon} {color}[L{skill.level}] {skill.name:35}{RESET}")
        print()
    def next_task(self):
        task = self.tracker.next_task()
        if not task:
            print(f"{GREEN}{BOLD}🎉 Все доступные навыки пройдены!{RESET}")
            return
        print(f"{BOLD}▶️  СЛЕДУЮЩИЙ ШАГ:{RESET}")
        print(f"  {CYAN}{task.name}{RESET}")
        print(f"  {DIM}Уровень {task.level} · ~{task.duration_h:.0f}ч{RESET}")
        if task.resources:
            print(f"  {DIM}Ресурсы: {', '.join(task.resources[:3])}{RESET}")
        print()

    def menu(self):
        print(f"{BOLD}КОМАНДЫ:{RESET}")
        print(f"  {GREEN}[s]{RESET} старт  · {GREEN}[d]{RESET} готово (done)")
        print(f"  {GREEN}[r]{RESET} refresh · {GREEN}[q]{RESET} выход")
        print()

    def render(self):
        self.clear()
        self.header()
        self.skills_list()
        self.next_task()
        self.menu()

    def run(self):
        while True:
            self.render()
            try:
                cmd = input(f"{BOLD}>>> {RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if cmd in ("q", "quit", "exit"):
                print(f"{DIM}До связи.{RESET}")
                break

            elif cmd in ("r", "refresh", ""):
                continue

            elif cmd == "s":
                task = self.tracker.next_task()
                if task:
                    self.tracker.start(task.id)
                    print(f"{GREEN}✅ Старт: {task.name}{RESET}")
                    input(f"{DIM}Enter...{RESET}")

            elif cmd == "d":
                task = self.tracker.next_task()
                if not task:
                    continue
                score = input(f"{DIM}Оценка 0-100 [80]: {RESET}").strip()
                try:
                    score = int(score) if score else 80
                except ValueError:
                    score = 80
                opened = self.tracker.complete(task.id, score)
                self.ledger.add(task.id, score, reviewer="aura")
                print(f"{GREEN}✅ Готово: {task.name} ({score}){RESET}")
                if opened:
                    print(f"{CYAN}🔓 Открыто: {', '.join(opened)}{RESET}")
                input(f"{DIM}Enter...{RESET}")

            else:
                print(f"{RED}Не знаю команду: {cmd}{RESET}")
                input(f"{DIM}Enter...{RESET}")


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "batya"
    MentorTUI(user).run()
