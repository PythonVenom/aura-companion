import subprocess
from pathlib import Path


class CinnamonScreenshot:
    name = "cinnamon"

    def capture(self, path: str) -> bool:
        for cmd in (
            ["cinnamon-screenshot", "-f", path],
            ["mate-screenshot", "-f", path],
            ["xfce4-screenshooter", "-f", "-s", path],
            ["gnome-screenshot", "-f", path],
            ["scrot", path],
        ):
            try:
                r = subprocess.run(cmd, timeout=5)
                if r.returncode == 0 and Path(path).exists():
                    return True
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return False
