"""Screenshot adapters."""
from .cinnamon import CinnamonScreenshot
from .gnome import GNOMEScreenshot
from .kde import KDEScreenshot

__all__ = ["CinnamonScreenshot", "GNOMEScreenshot", "KDEScreenshot", "get_screenshot"]


def get_screenshot():
    from aura.env.detect import detect
    de = detect()["de"]
    if de == "kde":
        return KDEScreenshot()
    if de == "gnome":
        return GNOMEScreenshot()
    return CinnamonScreenshot()
