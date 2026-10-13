"""Path Tracker ??? ?????????? ???????????????????????? ???? Skill Graph.
??????????: Deliberate Practice (Ericsson), Spaced Repetition (FSRS),
        Octalysis (Yu-kai Chou).
"""
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from aura.kernel.agents.mentor.schema import SKILLS_SEED, Skill
from aura.kernel.agents.mentor.schema_branches import ALL_BRANCHES
from aura.kernel.agents.mentor.schema_extra import ALL_EXTRA

CUSTOM_SKILLS_FILE = Path.home() / ".local/share/aura/mentor/custom_skills.json"


def _load_custom() -> list:
    """Загрузить custom skills (Open-Closed)."""
    import json
    if not CUSTOM_SKILLS_FILE.exists():
        return []
    try:
        data = json.loads(CUSTOM_SKILLS_FILE.read_text(encoding="utf-8"))
        return [Skill(**s) for s in data.get("skills", [])]
    except Exception:
        return []

STORE = Path.home() / ".local/share/aura/mentor/profile.json"


@dataclass
class Progress:
    skill_id: str
    status: str           # locked | available | in_progress | done
    score: int = 0        # 0-100
    last_practice: str | None = None
    next_review: str | None = None


class PathTracker:
    def __init__(self, user: str = "batya"):
        self.user = user
        all_skills = SKILLS_SEED + ALL_EXTRA + ALL_BRANCHES + _load_custom()
        self.skills = {s.id: s for s in all_skills}
        self.progress: dict[str, Progress] = {}
        self._load()

    def _load(self):
        """Загрузить прогресс + синхронизировать новые skills."""
        STORE.parent.mkdir(parents=True, exist_ok=True)
        if STORE.exists():
            data = json.loads(STORE.read_text())
            for p in data.get("progress", []):
                self.progress[p["skill_id"]] = Progress(**p)

        # Синхронизация: добавить новые skills (Open-Closed)
        added = 0
        for sid, s in self.skills.items():
            if sid in self.progress:
                continue
            if not s.prerequisites:
                self.progress[sid] = Progress(sid, "available")
            else:
                # Проверяем: все prereq done?
                if all(
                    self.progress.get(pid) and self.progress[pid].status == "done"
                    for pid in s.prerequisites
                ):
                    self.progress[sid] = Progress(sid, "available")
                else:
                    self.progress[sid] = Progress(sid, "locked")
            added += 1

        if added or not self.progress:
            self._save()

    def _init(self):
        """?????? locked, ???????????????? ???????????? ????, ?? ???????? ?????? prereq."""
        for s in self.skills.values():
            if not s.prerequisites:
                self.progress[s.id] = Progress(s.id, "available")
            else:
                self.progress[s.id] = Progress(s.id, "locked")
        self._save()

    def _save(self):
        STORE.write_text(json.dumps({
            "user": self.user,
            "updated": datetime.now().isoformat(),
            "progress": [asdict(p) for p in self.progress.values()],
        }, ensure_ascii=False, indent=2))

    def next_task(self) -> Skill | None:
        """?????? ???????????? ???????????? ??? ?????????? ???????????? ?????????????????? ??????????????."""
        available = [self.skills[sid] for sid, p in self.progress.items()
                     if p.status == "available"]
        if not available:
            return None
        return sorted(available, key=lambda s: (s.level, s.id))[0]

    def start(self, skill_id: str) -> bool:
        if self.progress[skill_id].status != "available":
            return False
        self.progress[skill_id].status = "in_progress"
        self.progress[skill_id].last_practice = datetime.now().isoformat()
        self._save()
        return True

    def complete(self, skill_id: str, score: int = 80) -> list[str]:
        """?????????????????? ??? ?????????????? ??????????????????. ???????????????????? ???????????????? skills."""
        p = self.progress[skill_id]
        p.status = "done"
        p.score = score
        p.last_practice = datetime.now().isoformat()
        # FSRS-lite: ?????????? 1 ????????, 3 ??????, 7, 30
        p.next_review = (datetime.now() + timedelta(days=1)).isoformat()

        opened = []
        for s in self.skills.values():
            if skill_id not in s.prerequisites:
                continue
            prereq_status = [self.progress[pid].status
                             for pid in s.prerequisites]
            if all(st == "done" for st in prereq_status):
                if self.progress[s.id].status == "locked":
                    self.progress[s.id].status = "available"
                    opened.append(s.id)
        self._save()
        return opened

    def stats(self) -> dict:
        by_status = {"locked": 0, "available": 0, "in_progress": 0, "done": 0}
        for p in self.progress.values():
            by_status[p.status] += 1
        total = len(self.progress)
        done = by_status["done"]
        return {
            "total": total,
            "done": done,
            "percent": round(100 * done / total, 1) if total else 0,
            **by_status,
        }


if __name__ == "__main__":
    pt = PathTracker("test")
    print("=== INIT ===")
    print(pt.stats())
    print(f"\nNext task: {pt.next_task()}")

    print("\n=== COMPLETE bash-basics ===")
    pt.start("bash-basics")
    opened = pt.complete("bash-basics", score=85)
    print(f"Opened: {opened}")
    print(pt.stats())
    print(f"Next: {pt.next_task()}")
