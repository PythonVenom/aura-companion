"""Window manager adapters."""
from .base import WindowManager
from .kde_x11 import KDEX11Adapter
from .x11_generic import X11GenericAdapter

__all__ = ["KDEX11Adapter", "WindowManager", "X11GenericAdapter", "get_window_manager"]


def get_window_manager():
    from aura.env.detect import detect
    env = detect()
    if env["de"] == "kde" and env["session"] == "x11":
        return KDEX11Adapter()
    return X11GenericAdapter()
