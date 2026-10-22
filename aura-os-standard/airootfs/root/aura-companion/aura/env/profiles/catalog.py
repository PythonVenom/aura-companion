"""ENV-2: Каталог компонентов Aura Shell.

Наука: Component Catalog (Gamma, GoF 1994).
Все компоненты — готовые из Arch/AUR. Не изобретаем велосипед.
"""
from __future__ import annotations

# 3 профиля сборки. Каждый — композиция готовых компонентов.
PROFILES = {
    # === Профиль 1: "Aura Minimal" — простота GNOME + быстрота i3 ===
    "minimal": {
        "wm": "i3-wm",
        "panel": "polybar",
        "launcher": "rofi",
        "notify": "dunst",
        "terminal": "kitty",
        "files": "pcmanfm",
        "sound": "pipewire-pulse pavucontrol",
        "screenshot": "maim slop",
        "clipboard": "clipmenu",
        "session": "lightdm lightdm-gtk-greeter",
        "extra": ["i3status", "feh", "compton", "xss-lock"],
        "desc": "Легковесно, быстро, минимум.",
    },
    # === Профиль 2: "Aura Plasma X11" — пластичность KDE + X11 ===
    "plasma_x11": {
        "wm": "kwin-x11",
        "panel": "plasma-workspace",
        "launcher": "plasma-desktop (krunner)",
        "notify": "plasma-workspace",
        "terminal": "konsole",
        "files": "dolphin",
        "sound": "pipewire-pulse pavucontrol-qt",
        "screenshot": "spectacle",
        "clipboard": "klipper",
        "session": "plasma-x11-session sddm",
        "extra": ["plasma-x11-session", "kwin-x11", "plasma-workspace"],
        "desc": "Пластичность Plasma, X11 (совместимо с NVIDIA 470).",
    },
    # === Профиль 4: "Aura Shell" — финальная сборка (SonicDE + Krema + QuickBar) ===
    "aura_shell": {
        "wm": "sonic-win",  # kwin-x11 форк
        "workspace": "sonic-workspace",
        "addons": "sonic-workspace-addons",
        "dock": "krema",  # параболический зум как macOS
        "launcher": "plasma6-applets-quickbar",  # глобальное меню
        "panel": "plasma-panel (X11)",  # панель сверху
        "notify": "plasma-workspace",
        "terminal": "konsole",
        "files": "dolphin",
        "sound": "pipewire-pulse pavucontrol-qt",
        "screenshot": "spectacle",
        "clipboard": "klipper",
        "session": "sddm (X11 session)",
        "aura": ["aura.service", "aura-dbus.service", "aura-tray.service"],
        "plasmoid": "org.aura.status",
        "extra": [
            "latte-dock-ng-git",  # fallback dock
            "plasma6-applets-panel-colorizer",  # кастомизация
            "plasma6-applets-quickbar",
        ],
        "gpu": "nvidia_470 (X11 mandatory)",
        "desc": "Финальная сборка: SonicDE + Krema + QuickBar + Aura из коробки.",
    },
    # === Профиль 3: "Aura Composed" — гибрид GNOME-простота + KDE-настройки + i3-скорость ===
    "composed": {
        "wm": "kwin-x11",  # можно переключить на i3
        "panel": "polybar",  # лёгкая панель
        "launcher": "rofi",  # минимализм
        "notify": "dunst",
        "terminal": "kitty",
        "files": "dolphin",  # мощный файлменеджер
        "sound": "pipewire-pulse pavucontrol-qt",
        "screenshot": "spectacle",
        "clipboard": "clipmenu",
        "settings": "systemsettings",  # KDE настройки отдельно
        "session": "sddm (custom session file)",
        "extra": [
            "plasma-workspace (только systemsettings)",
            "kwin-x11",
            "polybar rofi dunst kitty",
        ],
        "desc": "Гибрид: GNOME-простота + KDE-настройки + i3-скорость.",
    },
}

GPU_REQUIREMENTS = {
    "nvidia_470": {
        "driver": "nvidia-470xx-dkms",
        "wayland_support": False,
        "recommended_sessions": ["minimal", "plasma_x11", "composed"],
        "avoid": ["plasma_wayland", "gnome_wayland_native"],
    },
}

def get_profile(name: str) -> dict:
    return PROFILES.get(name, {})

def all_profiles() -> list[str]:
    return list(PROFILES.keys())

if __name__ == "__main__":
    print("=== ПРОФИЛИ AURA SHELL ===")
    for name, prof in PROFILES.items():
        print(f"\n[{name}] {prof['desc']}")
        for k, v in prof.items():
            if k == "desc": continue
            print(f"  {k}: {v}")
