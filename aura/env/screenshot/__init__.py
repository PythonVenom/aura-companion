"""Screenshot adapters."""
from .cinnamon import CinnamonScreenshot
from .kde import KDEScreenshot
from .gnome import GNOMEScreenshot

__all__ = ["CinnamonScreenshot", "KDEScreenshot", "GNOMEScreenshot", "get_screenshot"]


def get_screenshot():
    from aura.env.detect import detect
    de = detect()["de"]
    if de == "kde":
        return KDEScreenshot()
    if de == "gnome":
        return GNOMEScreenshot()
    return CinnamonScreenshot()
