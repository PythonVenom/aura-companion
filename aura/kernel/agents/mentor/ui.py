"""Task Engine UI — text-меню для Skill Graph.
Наука: Octalysis (Yu-kai Chou) — 8 мотиваторов.
"""
from aura.kernel.agents.mentor.path import PathTracker


def render_menu(tracker: PathTracker) -> str:
    s = tracker.stats()
    lines = [
        f"📚 МЕНТОР · прогресс {s['done']}/{s['total']} ({s['percent']}%)",
        "",
    ]
    for sid, p in tracker.progress.items():
        skill = tracker.skills[sid]
        icon = {"locked": "🔒", "available": "🟢",
                "in_progress": "🟡", "done": "✅"}[p.status]
        lines.append(f"  {icon} [{skill.level}] {skill.name} ({skill.duration_h:.0f}ч)")
    nxt = tracker.next_task()
    if nxt:
        lines.append("")
        lines.append(f"▶️  СЛЕДУЮЩИЙ: {nxt.name}")
    return "\n".join(lines)


if __name__ == "__main__":
    t = PathTracker("test")
    print(render_menu(t))
