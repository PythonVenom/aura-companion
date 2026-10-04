"""Универсальный X11 адаптер (для бати на Mint + Cinnamon)."""
import subprocess
from .base import WindowManager


class X11GenericAdapter(WindowManager):
    name = "x11_generic"

    def _run(self, *args, timeout=3) -> str:
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip()
        except Exception:
            return ""

    def list_windows(self) -> list:
        out = self._run("wmctrl", "-l")
        result = []
        for line in out.splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                result.append({
                    "id": parts[0],
                    "desktop": parts[1],
                    "pid": parts[2],
                    "title": parts[3],
                })
        return result

    def focus(self, window_id: str) -> bool:
        self._run("wmctrl", "-ia", window_id)
        return True

    def switch_desktop(self, n: int) -> bool:
        self._run("wmctrl", "-s", str(n - 1))
        return True

    def close(self, window_id: str) -> bool:
        self._run("wmctrl", "-ic", window_id)
        return True
