"""Window manager adapters."""
from .base import WindowManager
from .x11_generic import X11GenericAdapter
from .kde_x11 import KDEX11Adapter

__all__ = ["WindowManager", "X11GenericAdapter", "KDEX11Adapter", "get_window_manager"]


def get_window_manager():
    from aura.env.detect import detect
    env = detect()
    if env["de"] == "kde" and env["session"] == "x11":
        return KDEX11Adapter()
    return X11GenericAdapter()
