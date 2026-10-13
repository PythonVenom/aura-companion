"""Bug 31 — Детектор активного звонка.

Проблема:
  Во время звонков (MAX/TG/Zoom) Aura ловит разговор и мешает.
  Wake-word активируется на фразы юзера, который говорит в звонке.

Решение:
  Проверить, какие приложения занимают микрофон (pactl source-outputs).
  Если это известные call-приложения → is_call_active() = True.
  В listener: если True → skip wake-word (Aura молчит, только слушает).

Наука:
- ITU-T G.168 — Acoustic Echo Control
- Nielsen 1993 #3 — User Control and Freedom (юзер может прервать)
- ADR-007 — AEC (родственная фича для echo-pause)

Почему pactl:
- Уже используется в проекте (system_check, barge_in)
- Работает через PipeWire/PulseAudio на Linux
- Не требует root
"""
from __future__ import annotations

import shutil
import subprocess

# Известные call-приложения (по application.name в pactl)
CALL_APPS = {
    # Мобильные мессенджеры
    "max", "max messenger", "макс",
    "telegram", "telegram-desktop", "telegramdesktop",
    "whatsapp", "whatsapp for linux",
    # Видеоконференции
    "zoom", "zoom.us", "zoom workplace",
    "discord", "discord canary",
    "skype", "skypeforlinux",
    "slack", "slack-desktop",
    "teams", "microsoft teams", "ms-teams",
    "jitsi", "jitsi meet",
    # Браузеры (WebRTC в web-версиях)
    "firefox", "firefox-esr", "mozilla firefox",
    "chrome", "google-chrome", "google chrome",
    "chromium", "chromium-browser",
    "brave", "brave-browser",
    "edge", "microsoft-edge",
    "opera", "vivaldi",
}

# Исключения — это НЕ звонки, даже если занимают микрофон
EXCLUDE_APPS = {
    "alsa plug-in",         # Aura сама
    "aura", "python3", "python3.12", "python",
    "pipewire", "pulseaudio",
    "obs", "obs-studio",    # стрим, не звонок
    "audacity",             # запись
}


def _has_pactl() -> bool:
    return shutil.which("pactl") is not None


def _get_source_outputs() -> list[str]:
    """Вернуть список application.name, занявших микрофон."""
    if not _has_pactl():
        return []
    try:
        r = subprocess.run(
            ["pactl", "list", "source-outputs"],
            capture_output=True, text=True, timeout=3,
        )
        if r.returncode != 0:
            return []
    except Exception:
        return []

    apps: list[str] = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("application.name"):
            # application.name = "Zoom"
            _, _, value = line.partition("=")
            value = value.strip().strip('"').lower()
            if value:
                apps.append(value)
    return apps


def is_call_active() -> bool:
    """True если звонок активен (кто-то кроме Aura занял микрофон)."""
    for app in _get_source_outputs():
        # Сначала проверяем исключения
        if any(ex in app for ex in EXCLUDE_APPS):
            continue
        # Потом — известные call-приложения
        if any(call in app for call in CALL_APPS):
            return True
    return False


def get_call_apps() -> list[str]:
    """Список активных call-приложений (для отладки)."""
    active = []
    for app in _get_source_outputs():
        if any(ex in app for ex in EXCLUDE_APPS):
            continue
        if any(call in app for call in CALL_APPS):
            active.append(app)
    return active


__all__ = ["is_call_active", "get_call_apps", "CALL_APPS", "EXCLUDE_APPS"]
