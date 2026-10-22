"""Skill Graph Schema — Skill, seed-набор."""
from dataclasses import dataclass, field


@dataclass
class Skill:
    id: str
    name: str
    level: int
    branch: str
    prerequisites: list[str] = field(default_factory=list)
    duration_h: float = 10.0
    resources: list[str] = field(default_factory=list)


SKILLS_SEED = [
    Skill("bash-basics", "Bash: базовые команды", 1, "it",
          [], 8, ["man bash", "tldp.org"]),
    Skill("python-syntax", "Python: синтаксис", 1, "it",
          ["bash-basics"], 12, ["docs.python.org/tutorial"]),
    Skill("python-files", "Python: работа с файлами", 2, "it",
          ["python-syntax"], 10, []),
    Skill("python-api", "Python: HTTP API", 3, "it",
          ["python-files"], 15, []),
    Skill("git-basics", "Git: базовые операции", 2, "it",
          ["bash-basics"], 8, []),
    Skill("sql-basics", "SQL: SELECT/INSERT", 2, "it",
          ["python-files"], 12, []),
    Skill("backend-flask", "Backend на Flask", 4, "it",
          ["python-api", "sql-basics"], 30, []),
]
