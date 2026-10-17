"""System tray - иконка AURA + быстрое меню.

Наука: Whispr, Hanzo, cmd0 - AI в трее с глобальным хоткеем.
pystray 0.19.5 - кросс-платформенный, Python.

Функции:
- Иконка в трее (цвет = статус)
- Меню: Открыть чат / Статус / Режим тишины / Выход
- Глобальный хоткей Super+A (через pynput)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


def _make_icon(color: str = "green") -> Image.Image:
    """Сгенерировать простую иконку (кружок)."""
    colors = {
        "green": (76, 175, 80),
        "yellow": (255, 193, 7),
        "red": (244, 67, 54),
        "gray": (128, 128, 128),
    }
    rgb = colors.get(color, colors["green"])
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 8, 56, 56], fill=rgb)
    # «А» в центре
    d.text((22, 18), "A", fill=(255, 255, 255))
    return img


def _status_text() -> str:
    """Краткий статус для меню."""
    try:
        from aura.core import blackboard as bb
        snap = bb.snapshot()
        sector = snap.get("sector", "unknown")
        alerts = len(bb.recent_alerts(window_sec=300))
        return f"Сектор: {sector} | Тревог: {alerts}"
    except Exception:
        return "AURA на связи"


def _open_chat(icon, item) -> None:
    """Открыть чат в терминале."""
    subprocess.Popen(
        ["x-terminal-emulator", "-e", "bash", "-c",
         "cd ~/aura-companion && export PYTHONPATH=$PWD && ./venv/bin/python -m aura.chat"],
    )


def _show_status(icon, item) -> None:
    try:
        from aura.core import blackboard as bb
        snap = bb.snapshot()
        print(f"🛸 Сектор: {snap.get('sector')}")
        print(f"   Тревог: {len(bb.recent_alerts(window_sec=300))}")
        print(f"   Задач: {len(bb.active_tasks())}")
    except Exception as e:
        print(f"Ошибка: {e}")


def _toggle_silent(icon, item) -> None:
    """Переключить режим тишины."""
    flag = Path.home() / ".cache" / "aura" / "silent_mode"
    if flag.exists():
        flag.unlink()
        print("🔊 Звук включён")
    else:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()
        print("🔇 Режим тишины")


def _quit(icon, item) -> None:
    icon.stop()


def main() -> int:
    if not HAS_TRAY:
        print("❌ pystray не установлен: ./venv/bin/pip install pystray pillow")
        return 1
    icon = pystray.Icon(
        "aura",
        _make_icon("green"),
        (f"AURA - {_status_text()}").encode("ascii", "replace").decode("ascii"),
        menu=pystray.Menu(
            pystray.MenuItem("Открыть чат", _open_chat),
            pystray.MenuItem("Статус", _show_status),
            pystray.MenuItem("Режим тишины", _toggle_silent),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", _quit),
        ),
    )
    print("🛸 AURA tray запущен")
    icon.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
