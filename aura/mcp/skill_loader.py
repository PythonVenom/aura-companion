"""Загрузчик навыков из ~/.aura/skills/.

Парсит YAML файлы и превращает их в словарь навыков.
"""
import logging
from pathlib import Path
import yaml

logger = logging.getLogger("aura.skills")

SKILLS_DIR = Path.home() / ".aura" / "skills"

def load_skills() -> dict:
    """Загрузить все навыки из папки."""
    if not SKILLS_DIR.exists():
        logger.warning(f"Папка навыков не найдена: {SKILLS_DIR}")
        return {}

    skills = {}
    for file in SKILLS_DIR.glob("*.yaml"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "name" in data and "command" in data:
                    skills[data["name"]] = data
                    logger.info(f"Загружен навык: {data['name']}")
        except Exception as e:
            logger.error(f"Ошибка загрузки {file}: {e}")

    return skills

def find_skill(text: str) -> dict | None:
    """Найти навык по триггеру (ключевым словам)."""
    text = text.lower()
    skills = load_skills()
    
    for name, skill in skills.items():
        triggers = skill.get("triggers", [])
        for trigger in triggers:
            if trigger.lower() in text:
                return skill
    return None
