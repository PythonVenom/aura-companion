import subprocess
from pathlib import Path


class GNOMEScreenshot:
    name = "gnome"

    def capture(self, path: str) -> bool:
        try:
            subprocess.run(["gnome-screenshot", "-f", path], timeout=5)
            return Path(path).exists()
        except Exception:
            return False
