import subprocess
import logging

logger = logging.getLogger("aura.system_control")

def handle_system_command(text: str) -> str | None:
    text = text.lower()
    
    if "выключи" in text or "выруби" in text:
        logger.info("User requested poweroff")
        subprocess.run(["systemctl", "poweroff"])
        return "Выключаю систему."
        
    elif "перезагрузи" in text or "ребут" in text:
        logger.info("User requested reboot")
        subprocess.run(["systemctl", "reboot"])
        return "Перезагружаюсь."
        
    elif "сон" in text or "спать" in text:
        logger.info("User requested suspend")
        subprocess.run(["systemctl", "suspend"])
        return "Ухожу в сон."
        
    return None
