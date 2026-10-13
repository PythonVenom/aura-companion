"""Aura Mentor TUI — терминальный интерфейс Skill Graph.
Наука: Octalysis (Yu-kai Chou), Flow Theory (Csikszentmihalyi).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "aura-companion"))

from aura.kernel.agents.mentor.path import PathTracker
from aura.kernel.agents.mentor.ledger import ProfileLedger
from aura.kernel.agents.mentor.schema import SKILLS_SEED, Skill
from aura.kernel.agents.mentor.schema_extra import ALL_EXTRA
from aura.kernel.agents.mentor.schema_branches import ALL_BRANCHES

CUSTOM_SKILLS_FILE = Path.home() / ".local/share/aura/mentor/custom_skills.json"


def load_custom_skills() -> list:
    """Загрузить user-defined skills (Open-Closed: seed не трогаем)."""
    import json
    if not CUSTOM_SKILLS_FILE.exists():
        return []
    try:
        data = json.loads(CUSTOM_SKILLS_FILE.read_text(encoding="utf-8"))
        return [Skill(**s) for s in data.get("skills", [])]
    except Exception:
        return []


def save_custom_skills(skills: list) -> None:
    """Сохранить custom skills."""
    import json
    from dataclasses import asdict
    CUSTOM_SKILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CUSTOM_SKILLS_FILE.write_text(
        json.dumps({"skills": [asdict(s) for s in skills]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def all_skills() -> list:
    """Все skills: seed + extra + branches + custom."""
    return SKILLS_SEED + ALL_EXTRA + ALL_BRANCHES + load_custom_skills()


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
        all_skills = {s.id: s for s in all_skills()}
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
        print(f"  {GREEN}[s]{RESET} старт  · {GREEN}[d]{RESET} готово  · {GREEN}[r]{RESET} refresh")
        print(f"  {YELLOW}[a]{RESET} добавить  · {YELLOW}[e]{RESET} изменить  · {YELLOW}[x]{RESET} удалить")
        print(f"  {GREEN}[q]{RESET} выход")
        print()

    def render(self):
        self.clear()
        self.header()
        self.skills_list()
        self.next_task()
        self.menu()

    def add_skill(self):
        """Добавить custom skill (Open-Closed: seed не трогаем)."""
        print(f"{BOLD}➕ НОВЫЙ НАВЫК{RESET}")
        try:
            sid = input(f"{DIM}ID (латиница, дефисы) [{RESET}").strip()
            if not sid:
                return
            name = input(f"{DIM}Название: {RESET}").strip()
            if not name:
                return
            level = input(f"{DIM}Уровень (1-5) [1]: {RESET}").strip()
            level = int(level) if level else 1
            branch = input(f"{DIM}Ветка (it/art/medicine/business/lang) [it]: {RESET}").strip() or "it"
            prereq = input(f"{DIM}Пререквизиты (через запятую, пусто): {RESET}").strip()
            prereqs = [p.strip() for p in prereq.split(",") if p.strip()] if prereq else []

            from aura.kernel.agents.mentor.schema import Skill
            new_skill = Skill(sid, name, level, branch, prereqs, 10.0, [])

            customs = load_custom_skills()
            customs.append(new_skill)
            save_custom_skills(customs)
            print(f"{GREEN}✅ Добавлен: {name}{RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
        except Exception as e:
            print(f"{RED}❌ Ошибка: {e}{RESET}")
        input(f"{DIM}Enter...{RESET}")

    def edit_skill(self):
        """Изменить custom skill."""
        customs = load_custom_skills()
        if not customs:
            print(f"{YELLOW}Нет custom skills для редактирования{RESET}")
            input(f"{DIM}Enter...{RESET}")
            return

        print(f"{BOLD}✏️  CUSTOM SKILLS:{RESET}")
        for i, s in enumerate(customs, 1):
            print(f"  [{i}] {s.name} ({s.id})")

        try:
            idx = input(f"{DIM}Номер для редактирования: {RESET}").strip()
            if not idx.isdigit() or not (1 <= int(idx) <= len(customs)):
                return
            skill = customs[int(idx) - 1]

            name = input(f"{DIM}Название [{skill.name}]: {RESET}").strip()
            if name:
                skill.name = name

            level = input(f"{DIM}Уровень [{skill.level}]: {RESET}").strip()
            if level.isdigit():
                skill.level = int(level)

            save_custom_skills(customs)
            print(f"{GREEN}✅ Сохранено{RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
        input(f"{DIM}Enter...{RESET}")

    def delete_skill(self):
        """Удалить custom skill."""
        customs = load_custom_skills()
        if not customs:
            print(f"{YELLOW}Нет custom skills{RESET}")
            input(f"{DIM}Enter...{RESET}")
            return

        print(f"{BOLD}🗑  CUSTOM SKILLS:{RESET}")
        for i, s in enumerate(customs, 1):
            print(f"  [{i}] {s.name} ({s.id})")

        try:
            idx = input(f"{DIM}Номер для удаления: {RESET}").strip()
            if not idx.isdigit() or not (1 <= int(idx) <= len(customs)):
                return
            removed = customs.pop(int(idx) - 1)
            save_custom_skills(customs)
            print(f"{GREEN}✅ Удалён: {removed.name}{RESET}")
        except (EOFError, KeyboardInterrupt):
            print()
        input(f"{DIM}Enter...{RESET}")

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

            elif cmd == "a":
                self.add_skill()

            elif cmd == "e":
                self.edit_skill()

            elif cmd == "x":
                self.delete_skill()

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
