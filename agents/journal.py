"""
Машинка RAG: Авто-дневник (AgentJournal)
Пишет все диалоги в Markdown-журнал, группирует по дням,
поддерживает задачи [ ] / [x], показывает последнюю сессию.
"""

import os
import re
from datetime import datetime
from agents.base import MicroAgent


class AgentJournal(MicroAgent):
    def __init__(self):
        super().__init__("journal", "Авто-дневник")
        self.journal_file = os.path.expanduser("~/aura_project/JOURNAL.md")
        self.ready = True
        self._ensure_file()
        print(f"✅ Авто-дневник загружен ({self.journal_file})")

    def _ensure_file(self):
        """Создать файл, если его нет"""
        if not os.path.exists(self.journal_file):
            with open(self.journal_file, 'w', encoding='utf-8') as f:
                f.write("# 📔 Журнал Ауры\n\n")
                f.write("Автоматический дневник работы. Каждый диалог записывается сюда.\n\n")
                f.write("Формат задач:\n")
                f.write("- `[ ]` — не сделано\n")
                f.write("- `[x]` — сделано\n\n")

    def _today_header(self):
        """Заголовок сегодняшнего дня"""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"## {today}"

    def _has_today_header(self):
        """Есть ли уже заголовок сегодняшнего дня"""
        if not os.path.exists(self.journal_file):
            return False
        with open(self.journal_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return self._today_header() in content

    def _add_today_header(self):
        """Добавить заголовок сегодняшнего дня"""
        if not self._has_today_header():
            with open(self.journal_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{self._today_header()}\n\n")

    def log_dialog(self, user_text, aura_response):
        """Записать диалог в журнал"""
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            self._add_today_header()

            time_str = datetime.now().strftime("%H:%M")
            # Короткая запись: только суть
            user_short = user_text[:100].strip()
            aura_short = aura_response[:150].strip()

            with open(self.journal_file, 'a', encoding='utf-8') as f:
                f.write(f"### {time_str} — {user_short}\n")
                f.write(f"> {aura_short}\n\n")

            return f"📔 Записала в журнал"
        except Exception as e:
            return f"❌ Ошибка журнала: {e}"

    def add_task(self, task):
        """Добавить задачу в журнал"""
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            self._add_today_header()

            with open(self.journal_file, 'a', encoding='utf-8') as f:
                f.write(f"- [ ] {task}\n")

            return f"✅ Добавила задачу: {task}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def close_task(self, task_text):
        """Отметить задачу выполненной"""
        if not self.ready:
            return "❌ Журнал не готов"

        try:
            with open(self.journal_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем задачу и заменяем [ ] на [x]
            pattern = rf'- \[ \] ({re.escape(task_text)}.*)'
            new_content, count = re.subn(pattern, r'- [x] \1', content, flags=re.IGNORECASE)

            if count == 0:
                return f"❌ Задача не найдена: {task_text}"

            with open(self.journal_file, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"✅ Задача закрыта: {task_text}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def get_pending_tasks(self):
        """Вернуть список невыполненных задач"""
        if not os.path.exists(self.journal_file):
            return []

        with open(self.journal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        pending = re.findall(r'- \[ \] (.+)', content)
        return pending

    def get_done_tasks(self):
        """Вернуть список выполненных задач"""
        if not os.path.exists(self.journal_file):
            return []

        with open(self.journal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        done = re.findall(r'- \[x\] (.+)', content, flags=re.IGNORECASE)
        return done

    def get_last_session(self):
        """Информация о последней сессии"""
        if not os.path.exists(self.journal_file):
            return None

        with open(self.journal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Найти последнюю дату
        dates = re.findall(r'## (\d{4}-\d{2}-\d{2})', content)
        if not dates:
            return None

        last_date = dates[-1]
        today = datetime.now().strftime("%Y-%m-%d")

        # Найти последнюю запись времени
        times = re.findall(r'### (\d{2}:\d{2})', content)
        last_time = times[-1] if times else "неизвестно"

        pending = self.get_pending_tasks()

        return {
            "date": last_date,
            "time": last_time,
            "is_today": last_date == today,
            "pending": pending[:5],
            "pending_count": len(pending)
        }

    def show_journal(self, days=3):
        """Показать последние N дней журнала"""
        if not os.path.exists(self.journal_file):
            return "📔 Журнал пуст"

        with open(self.journal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Разделить по дням
        parts = re.split(r'\n## ', content)
        if len(parts) <= 1:
            return content[:1000]

        # Взять последние N дней
        recent = parts[-(days + 1):]
        result = "📔 Последние " + str(days) + " дней:\n\n"
        for part in recent:
            result += "## " + part.strip() + "\n\n"

        return result[:2000]

    def show_pending(self):
        """Показать невыполненные задачи"""
        pending = self.get_pending_tasks()
        if not pending:
            return "✅ Невыполненных задач нет!"

        result = f"📋 Осталось задач: {len(pending)}\n\n"
        for i, task in enumerate(pending, 1):
            result += f"{i}. [ ] {task}\n"

        return result

    def execute(self, command):
        cmd = command.lower().strip()

        # Показать журнал
        if 'покажи журнал' in cmd or 'что я делал' in cmd or 'что было' in cmd:
            session = self.get_last_session()
            if session:
                result = f"📔 Последняя сессия: {session['date']} в {session['time']}\n"
                if not session['is_today']:
                    result += f"⚠️ Это было не сегодня!\n"
                result += f"\n📋 Осталось задач: {session['pending_count']}\n"
                for task in session['pending']:
                    result += f"  • [ ] {task}\n"
                return result
            return "📔 Журнал пуст"

        # Показать невыполненные
        if 'что осталось' in cmd or 'что не сделано' in cmd or 'список задач' in cmd:
            return self.show_pending()

        # Добавить задачу
        if 'добавь задачу' in cmd or 'запиши задачу' in cmd:
            task = cmd
            for word in ['добавь задачу', 'запиши задачу', 'добавь в журнал']:
                task = task.replace(word, '')
            task = task.strip()
            if not task:
                return "Что добавить?"
            return self.add_task(task)

        # Закрыть задачу
        if 'закрой задачу' in cmd or 'выполнил' in cmd or 'сделал' in cmd:
            task = cmd
            for word in ['закрой задачу', 'выполнил', 'сделал']:
                task = task.replace(word, '')
            task = task.strip()
            if not task:
                return "Что закрыть?"
            return self.close_task(task)

        # Статистика
        if 'статистика журнала' in cmd:
            pending = len(self.get_pending_tasks())
            done = len(self.get_done_tasks())
            return f"📔 Журнал: ✅ {done} сделано, 📋 {pending} осталось"

        return "📔 Журнал готов. Команды: что я делал, что осталось, добавь задачу X, закрой задачу X"
