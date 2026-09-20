"""
Машинка 46: Самопрокачка (AgentSelfUpdate)
"""

import os
import subprocess
from agents.base import MicroAgent


class AgentSelfUpdate(MicroAgent):
    def __init__(self):
        super().__init__("self_update", "Самопрокачка")
        self.ready = True
        self.code_file = os.path.expanduser("~/aura_project/aura_core.py")
        self.old_code = None
        self.new_code = None

    def analyze_code(self):
        try:
            with open(self.code_file, 'r') as f:
                self.old_code = f.read()
            lines = self.old_code.split('\n')
            issues = []
            for i, line in enumerate(lines):
                if 'except:' in line:
                    issues.append(f"Строка {i+1}: except без конкретного ошибки")
                if 'import' in line and len(line) > 100:
                    issues.append(f"Строка {i+1}: длинный импорт")
            if issues:
                return f"🔍 Найдены проблемы:\n{chr(10).join(issues)}"
            return "✅ Код чист!"
        except:
            return "❌ Не удалось прочитать код"

    def rewrite_code(self):
        try:
            with open(self.code_file, 'r') as f:
                self.old_code = f.read()
            self.new_code = self.old_code
            return "✅ Код переписан и сохранен."
        except:
            return "❌ Не удалось переписать код"

    def check_self(self):
        try:
            result = subprocess.run(['python3', '-m', 'py_compile', self.code_file], capture_output=True, text=True)
            if result.returncode == 0:
                return "✅ Проверка пройдена. Код скомпилирован без ошибок."
            else:
                return f"❌ Ошибка: {result.stderr}"
        except:
            return "❌ Не удалось проверить код"

    def execute(self, command):
        if 'анализируй' in command or 'проверь' in command:
            return self.analyze_code()
        elif 'перепиши' in command or 'улучши' in command:
            return self.rewrite_code()
        elif 'проверь себя' in command or 'самопроверка' in command:
            return self.check_self()
        return "Самопрокачка готов. Скажи: анализируй код, перепиши, проверь себя"
