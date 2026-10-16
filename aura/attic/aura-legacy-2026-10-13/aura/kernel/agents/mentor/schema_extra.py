"""Mentor Skills Extension — backend, data, devops."""
from aura.kernel.agents.mentor.schema import Skill

SKILLS_BACKEND = [
    Skill("docker-basics", "Docker: контейнеры", 3, "it",
          ["git-basics", "bash-basics"], 10, []),
    Skill("ci-cd", "CI/CD: GitHub Actions", 4, "it",
          ["docker-basics"], 12, []),
    Skill("postgres", "PostgreSQL: базы", 3, "it",
          ["sql-basics"], 15, []),
    Skill("rest-api", "REST API: дизайн", 3, "it",
          ["python-api"], 10, []),
]
SKILLS_DATA = [
    Skill("numpy", "NumPy: массивы", 3, "it",
          ["python-syntax"], 8, []),
    Skill("pandas", "Pandas: DataFrames", 3, "it",
          ["numpy"], 12, []),
    Skill("ml-basics", "ML: scikit-learn", 4, "it",
          ["pandas"], 20, []),
]
SKILLS_DEVOPS = [
    Skill("linux-admin", "Linux: администрирование", 3, "it",
          ["bash-basics"], 20, []),
    Skill("ansible", "Ansible: автоматизация", 4, "it",
          ["linux-admin"], 15, []),
    Skill("monitoring", "Мониторинг: Prometheus", 4, "it",
          ["docker-basics"], 12, []),
]

ALL_EXTRA = SKILLS_BACKEND + SKILLS_DATA + SKILLS_DEVOPS
