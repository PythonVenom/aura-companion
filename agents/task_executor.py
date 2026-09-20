"""
Машинка 45: Ночной исполнитель (AgentTaskExecutor)
"""

import os
import time
from datetime import datetime
from agents.base import MicroAgent


class AgentTaskExecutor(MicroAgent):
    def __init__(self):
        super().__init__("task_executor", "Ночной исполнитель")
        self.ready = True
        self.task_queue = []
        self.task_log = []
        self.running = False
        self.current_task = None
        self.tasks_file = os.path.expanduser("~/aura_project/tasks.txt")
        self._load_tasks()

    def _load_tasks(self):
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r') as f:
                    self.task_queue = [line.strip() for line in f.readlines() if line.strip()]
            except:
                self.task_queue = []

    def add_task(self, task):
        self.task_queue.append(task)
        try:
            with open(self.tasks_file, 'a') as f:
                f.write(f"{task}\n")
        except:
            pass
        return f"✅ Добавила задачу: {task}"

    def clear_tasks(self):
        self.task_queue = []
        try:
            with open(self.tasks_file, 'w') as f:
                f.write("")
        except:
            pass
        return "🗑️ Все задачи удалены."

    def execute_task(self, task):
        self.current_task = task
        self.task_log.append({"task": task, "status": "running", "time": datetime.now().isoformat()})
        print(f"🚀 Выполняю задачу: {task}")
        self.task_log.append({"task": task, "status": "done", "time": datetime.now().isoformat()})
        return f"✅ Задача '{task}' выполнена."

    def run_all_tasks(self):
        if self.running:
            return "Уже работаю, не мешай!"
        if not self.task_queue:
            return "Задач нет. Добавь: 'дай задачу'"

        self.running = True
        while self.task_queue:
            task = self.task_queue.pop(0)
            self.execute_task(task)
            time.sleep(1)
        self.running = False
        return "🌅 Все задачи выполнены! Могу перезагрузиться."

    def execute(self, command):
        if 'задача' in command:
            if 'добавь' in command:
                task = command.replace('добавь задачу', '').replace('дай задачу', '').strip()
                return self.add_task(task)
            elif 'выполни' in command or 'все' in command:
                return self.run_all_tasks()
            elif 'сверни' in command or 'удалить' in command:
                return self.clear_tasks()
        return "Ночной исполнитель готов. Скажи: дай задачу, выполни все задачи"
