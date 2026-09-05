import pystray
from PIL import Image, ImageDraw
import os
import subprocess
import threading
import time

def create_image():
    img = Image.new('RGB', (64, 64), color='#6C63FF')
    d = ImageDraw.Draw(img)
    d.ellipse((12, 12, 52, 52), fill='#FFFFFF')
    d.text((24, 24), "A", fill='#6C63FF')
    return img

def restart_aura():
    os.system("sudo systemctl restart aura.service")
    print("AURA restarted")

def stop_aura():
    os.system("sudo systemctl stop aura.service")
    print("AURA stopped")

def start_aura():
    os.system("sudo systemctl start aura.service")
    print("AURA started")

def status_aura():
    result = subprocess.run(["sudo", "systemctl", "is-active", "aura.service"], capture_output=True, text=True)
    return result.stdout.strip()

def tray_loop():
    icon = pystray.Icon("aura", create_image(), title="AURA")
    
    def on_quit():
        icon.stop()
    
    def get_menu():
        status = status_aura()
        return pystray.Menu(
            pystray.MenuItem(f"Status: {status}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restart", restart_aura),
            pystray.MenuItem("Stop", stop_aura),
            pystray.MenuItem("Start", start_aura),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", on_quit)
        )
    
    icon.menu = get_menu()
    icon.run()

if __name__ == "__main__":
    tray_loop()
