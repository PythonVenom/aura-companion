"""Global hotkey — Super+A для вызова AURA.

Наука: Spotlight (Apple 2005), Whispr, Hanzo.
Fallback: pynput если есть, иначе — systemd unit с ydotool.
"""
from __future__ import annotations

import subprocess

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False


def launch_chat() -> None:
    """Открыть чат AURA в терминале."""
    subprocess.Popen(
        ["x-terminal-emulator", "-e", "bash", "-c",
         "cd ~/aura-companion && export PYTHONPATH=$PWD && ./venv/bin/python -m aura.chat"],
    )


def launch_widget() -> None:
    """Открыть GUI-виджет."""
    subprocess.Popen(
        ["bash", "-c",
         "cd ~/aura-companion && export PYTHONPATH=$PWD && ./venv/bin/python -m aura.cockpit.ui.widget"],
    )


class HotkeyListener:
    """Слушатель глобальных хоткеев."""

    def __init__(self) -> None:
        self._listener = None
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready and HAS_PYNPUT

    def start(self) -> bool:
        """Запустить слушатель Super+A → виджет."""
        if not HAS_PYNPUT:
            return False
        try:
            hotkey = keyboard.HotKey(
                keyboard.HotKey.parse("<cmd>+a"),
                lambda: launch_widget(),
            )

            def for_canonical(f):
                return lambda k: f(self._listener.canonical(k))

            self._listener = keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release),
            )
            self._listener.start()
            self._ready = True
            return True
        except Exception:
            return False

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()


def main() -> int:
    if not HAS_PYNPUT:
        print("❌ pynput не установлен: ./venv/bin/pip install pynput")
        return 1
    listener = HotkeyListener()
    if listener.start():
        print("🎯 Hotkey Super+A запущен (открывает AURA Widget)")
        print("   Ctrl+C для выхода")
        try:
            listener._listener.join()
        except KeyboardInterrupt:
            listener.stop()
        return 0
    print("❌ Не удалось запустить hotkey")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())


__all__ = ["HAS_PYNPUT", "HotkeyListener", "launch_chat", "launch_widget"]
