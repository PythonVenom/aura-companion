"""Исполнитель навыков. Запускает команды из skill_loader."""
import subprocess
import logging

logger = logging.getLogger("aura.skills")

def execute_skill(skill: dict) -> str:
    """Выполнить команду навыка и вернуть результат."""
    command = skill.get("command")
    if not command:
        return "Ошибка: команда не указана."

    try:
        logger.info(f"Выполнение навыка: {skill['name']}")
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip() or "Готово (без вывода)."
        else:
            return f"Ошибка (код {result.returncode}): {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Ошибка: команда выполнялась слишком долго."
    except Exception as e:
        return f"Ошибка выполнения: {e}"
