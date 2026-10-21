import logging
import subprocess

logger = logging.getLogger("aura.system_control")

def handle_system_command(text: str) -> str | None:
    text = text.lower()

    if "выключи" in text or "выруби" in text:
        logger.info("User requested poweroff")
        print("🛑 poweroff disabled_for_safety")
        return "Выключаю систему."

    elif "перезагрузи" in text or "ребут" in text:
        logger.info("User requested reboot")
        print("🛑 reboot disabled_for_safety")
        return "Перезагружаюсь."

    elif "сон" in text or "спать" in text:
        logger.info("User requested suspend")
        print("🛑 suspend disabled_for_safety")
        return "Ухожу в сон."

    return None
