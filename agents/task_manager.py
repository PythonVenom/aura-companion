"""
Машинка 44: Менеджер задач (AgentTaskManager)
"""

import os
import json
from datetime import datetime
from agents.base import MicroAgent


class AgentTaskManager(MicroAgent):
    def __init__(self):
        super().__init__("task_manager", "Менеджер задач")
        self.tasks = {}
        self.tasks_file = os.path.expanduser("~/aura_project/tasks.json")
        self._load()

    def _load(self):
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = {}

    def _save(self):
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add_task(self, task):
        self.tasks[datetime.now().isoformat()] = task
        self._save()
        return f"✅ Добавила задачу: {task}"

    def get_tasks(self):
        if not self.tasks:
            return "📋 Задач нет, создатель. Добавить что-то?"
        tasks = list(self.tasks.values())[-5:]
        result = "📋 ВОТ ТВОИ ЗАДАЧИ:\n"
        for i, task in enumerate(tasks, 1):
            result += f"  {i}. {task}\n"
        return result

    def get_plan(self):
        if not self.tasks:
            return "📋 Задач нет. Могу предложить: открыть браузер, проверить обновления, поработать с кодом."
        return f"📋 Сегодня {len(self.tasks)} задач. Начнем с первой: {list(self.tasks.values())[0]}?"

    def execute(self, command):
        if 'задач' in command or 'план' in command or 'список' in command:
            return self.get_tasks()
        elif 'добавь' in command or 'запиши' in command:
            task = command.replace('добавь', '').replace('запиши', '').strip()
            return self.add_task(task)
        elif 'план на сегодня' in command:
            return self.get_plan()
        return "📋 Менеджер задач готов. Скажи: добавить задачу, список задач, план на сегодня"
