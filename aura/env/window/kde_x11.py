"""KDE X11 адаптер (для тебя)."""
import subprocess

from .base import WindowManager


class KDEX11Adapter(WindowManager):
    name = "kde_x11"
    QDBUS = "qdbus6"

    def _q(self, *args, timeout=3) -> str:
        try:
            r = subprocess.run(
                [self.QDBUS, "org.kde.KWin", "/KWin"] + list(args),
                capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip()
        except Exception:
            return ""

    def list_windows(self) -> list:
        from .x11_generic import X11GenericAdapter
        return X11GenericAdapter().list_windows()

    def focus(self, window_id: str) -> bool:
        from .x11_generic import X11GenericAdapter
        return X11GenericAdapter().focus(window_id)

    def switch_desktop(self, n: int) -> bool:
        self._q("setCurrentDesktop", str(n))
        return True

    def close(self, window_id: str) -> bool:
        from .x11_generic import X11GenericAdapter
        return X11GenericAdapter().close(window_id)
