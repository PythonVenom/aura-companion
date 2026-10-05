#!/usr/bin/env python3
"""Standalone Aura tray — без импорта aura.* (для systemd + system python)."""
import subprocess
import urllib.request
import json
from PIL import Image, ImageDraw
import pystray

CTL = "/home/pythonvenom/aura_project/scripts/aura_ctl.py"
PYTHON = "/home/pythonvenom/aura_project/venv/bin/python"
API = "http://127.0.0.1:8765"

STATE_COLORS = {
    "idle": "#5a7a9a", "listening": "#f5c542", "thinking": "#f58742",
    "speaking": "#42c55a", "paused": "#666666", "error": "#c54242",
    "unknown": "#888888",
}

def make_icon(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, 58, 58], fill=color)
    return img

def get_state():
    try:
        with urllib.request.urlopen(f"{API}/status", timeout=1) as r:
            return json.loads(r.read()).get("state", "unknown")
    except Exception:
        return "unknown"

def run_ctl(cmd):
    subprocess.Popen([PYTHON, CTL, cmd],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def on_sos(icon, item): run_ctl("panic")
def on_pause(icon, item): run_ctl("pause")
def on_resume(icon, item): run_ctl("resume")
def on_mute(icon, item): run_ctl("mute")
def on_unmute(icon, item): run_ctl("unmute")
def on_kill(icon, item): run_ctl("kill")
def on_quit(icon, item): icon.stop()

def make_menu():
    return pystray.Menu(
        pystray.MenuItem("SOS", on_sos),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Пауза", on_pause),
        pystray.MenuItem("Продолжить", on_resume),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Mute", on_mute),
        pystray.MenuItem("Unmute", on_unmute),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Kill Aura", on_kill),
        pystray.MenuItem("Выход", on_quit),
    )

def main():
    state = get_state()
    icon = pystray.Icon(
        "aura",
        make_icon(STATE_COLORS.get(state, STATE_COLORS["unknown"])),
        f"Aura: {state}",
        menu=make_menu(),
    )
    icon.run()

if __name__ == "__main__":
    main()
