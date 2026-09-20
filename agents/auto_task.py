"""
Машинка 63: Автономный режим (AgentAutoTask)
"""

import subprocess
import threading
import time
from agents.base import MicroAgent


class AgentAutoTask(MicroAgent):
    def __init__(self):
        super().__init__("auto_task", "Автономный режим")
        self.running = False
        self.task_queue = []
        self.thread = None

    def start_auto_mode(self):
        if self.running:
            return "⚡ Автономный режим уже работает"

        self.running = True
        self.thread = threading.Thread(target=self._auto_worker, daemon=True)
        self.thread.start()
        return "⚡ Автономный режим запущен"

    def _auto_worker(self):
        while self.running:
            try:
                result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
                count = result.stdout.strip()
                if count and int(count) > 0:
                    self.task_queue.append(f"⚠️ Есть обновления: {count} шт.")

                result = subprocess.run("df -h / | awk 'NR==2 {print $5}'", shell=True, capture_output=True, text=True)
                disk = result.stdout.strip()
                if disk and int(disk[:-1]) > 80:
                    self.task_queue.append(f"⚠️ Диск занят на {disk}")

                while self.task_queue and self.running:
                    task = self.task_queue.pop(0)
                    print(f"🤖 [Авто] {task}")
                    time.sleep(3)

                time.sleep(30)
            except:
                time.sleep(5)

    def stop_auto_mode(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.task_queue = []
        return "⏹️ Автономный режим остановлен"

    def execute(self, command):
        if 'автономный' in command or 'сам работай' in command or 'авто' in command:
            return self.start_auto_mode()
        elif 'стоп авто' in command or 'останови' in command:
            return self.stop_auto_mode()
        return "⚡ Автономный режим готов. Скажи: 'включи автономный режим'"
