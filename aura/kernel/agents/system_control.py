"""Агент системного контроля с защитой HITL."""
import subprocess
import logging

logger = logging.getLogger("aura.system_control")
PENDING_CONFIRMATION = None

def handle_system_command(text: str) -> str | None:
    global PENDING_CONFIRMATION
    text = text.lower()

    if PENDING_CONFIRMATION:
        if "да" in text or "подтверждаю" in text:
            action = PENDING_CONFIRMATION
            PENDING_CONFIRMATION = None
            if action == "poweroff":
                subprocess.run(["systemctl", "poweroff"])
                return "Выключаю систему."
            elif action == "reboot":
                subprocess.run(["systemctl", "reboot"])
                return "Перезагружаюсь."
            elif action == "suspend":
                subprocess.run(["systemctl", "suspend"])
                return "Ухожу в сон."
        elif "нет" in text or "отмена" in text:
            PENDING_CONFIRMATION = None
            return "Отменено. Ничего не делаю."
        else:
            return "Жду ответа: 'Да' или 'Нет'."

    if "выключи" in text or "выруби" in text:
        PENDING_CONFIRMATION = "poweroff"
        return "⚠️ ВНИМАНИЕ: Выключить компьютер? Ответь 'Да' или 'Нет'."
    elif "перезагрузи" in text or "ребут" in text:
        PENDING_CONFIRMATION = "reboot"
        return "⚠️ ВНИМАНИЕ: Перезагрузить компьютер? Ответь 'Да' или 'Нет'."
    elif "сон" in text or "спать" in text:
        PENDING_CONFIRMATION = "suspend"
        return "⚠️ ВНИМАНИЕ: Уйти в сон? Ответь 'Да' или 'Нет'."

    return None
