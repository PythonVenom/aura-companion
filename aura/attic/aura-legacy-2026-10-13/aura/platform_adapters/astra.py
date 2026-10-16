"""Astra Linux adapter — stub для интеграции.
Наука: Portability (POSIX), Cross-compilation.
"""
import logging
import platform

log = logging.getLogger("aura.platform.astra")


class AstraAdapter:
    name = "astra"
    version = "0.1.0"

    @staticmethod
    def detect() -> bool:
        """Astra Linux SE detection."""
        try:
            with open("/etc/os-release") as f:
                return "astra" in f.read().lower()
        except Exception:
            return False

    @staticmethod
    def info() -> dict:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "is_astra": AstraAdapter.detect(),
            "is_e2k": platform.machine() in ("e2k", "elbrus"),
        }

    @staticmethod
    def install_aura() -> str:
        """TODO: e2k-сборка piper + paplay + ollama."""
        return "TODO: см. docs/PLATFORM_ASTRA.md"


if __name__ == "__main__":
    print(AstraAdapter.info())
