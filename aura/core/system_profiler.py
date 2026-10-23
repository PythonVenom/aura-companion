import subprocess
import logging

log = logging.getLogger("aura.sysprof")

class SystemProfiler:
    """Научный подход: Автоопределение устройств для любых DE (GNOME, KDE, Hyprland)."""
    
    @staticmethod
    def get_default_mic() -> str:
        """Возвращает имя дефолтного микрофона (игнорирует echo-cancel)."""
        try:
            result = subprocess.run(
                ["pactl", "get-default-source"], 
                capture_output=True, text=True, check=True
            )
            mic_name = result.stdout.strip()
            if "echo-cancel" in mic_name:
                log.warning("Обнаружен echo-cancel, ищу физический микрофон...")
                return "alsa_input.pci-0000_00_1f.3.analog-stereo"
            return mic_name
        except Exception as e:
            log.error(f"Ошибка автоопределения микрофона: {e}")
            return "default"

    @staticmethod
    def get_default_speaker() -> str:
        """Возвращает имя дефолтных колонок."""
        try:
            result = subprocess.run(
                ["pactl", "get-default-sink"], 
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception as e:
            log.error(f"Ошибка автоопределения колонок: {e}")
            return "default"
