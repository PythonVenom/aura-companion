import subprocess
from .base import SoundAdapter


class PipeWireAdapter(SoundAdapter):
    name = "pipewire"

    def _run(self, *args) -> str:
        try:
            return subprocess.run(
                args, capture_output=True, text=True, timeout=3).stdout.strip()
        except Exception:
            return ""

    def get_default_source(self) -> str:
        return self._run("pactl", "get-default-source")

    def set_volume(self, pct: int) -> bool:
        self._run("pactl", "set-sink-volume", "@DEFAULT_SINK@", str(pct) + "%")
        return True

    def list_sinks(self) -> list:
        out = self._run("pactl", "list", "sinks", "short")
        result = []
        for line in out.splitlines():
            parts = line.split(chr(9))
            if len(parts) >= 2:
                result.append({"id": parts[0], "name": parts[1]})
        return result
