import subprocess
from pathlib import Path


class KDEScreenshot:
    name = "kde"

    def capture(self, path: str) -> bool:
        try:
            subprocess.run(["spectacle", "-b", "-n", "-o", path], timeout=5)
            return Path(path).exists()
        except Exception:
            return False
