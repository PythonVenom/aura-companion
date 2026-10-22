import json, os, time, threading
from pathlib import Path

REMINDERS_FILE = Path.home() / ".cache/aura/reminders.json"

class ReminderSystem:
    def __init__(self, speaker):
        self.speaker = speaker
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            try:
                if REMINDERS_FILE.exists():
                    data = json.loads(REMINDERS_FILE.read_text())
                    now = time.strftime("%H:%M")
                    if data.get("time") == now:
                        self.speaker.say(f"Капитан, напоминание: {data['text']}")
                        REMINDERS_FILE.unlink()
            except Exception:
                pass
            time.sleep(10)
