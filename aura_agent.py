#!/usr/bin/env python3
"""
Аура - фрактальный мульти-агент с микро-агентами
"""

import subprocess
import re
from datetime import datetime

class MicroAgent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def execute(self, input_data):
        raise NotImplementedError

class AgentNoiseFilter(MicroAgent):
    def __init__(self):
        super().__init__("noise_filter", "Убирает шум")
    
    def execute(self, text):
        cleaned = re.sub(r'[^\w\s.,!?-]', '', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

class AgentTextParser(MicroAgent):
    def __init__(self):
        super().__init__("text_parser", "Разбивает на слова")
    
    def execute(self, text):
        return text.split()

class AgentWordJoiner(MicroAgent):
    def __init__(self):
        super().__init__("word_joiner", "Собирает слова")
    
    def execute(self, words):
        return ' '.join(words)

class AgentIntentRecognizer(MicroAgent):
    def __init__(self):
        super().__init__("intent_recognizer", "Определяет намерение")
        self.intents = {
            'time': ['время', 'час', 'сколько времени', 'который час'],
            'update': ['обновление', 'обновить', 'пакеты', 'обнова', 'проверь обновл'],
            'upgrade': ['установи обновл', 'обнови систему', 'установить обновл', 'сделай обновл', 'обнови'],
            'shell': ['выполни', 'запусти', 'команду', 'терминал'],
            'help': ['помощь', 'что ты умеешь', 'помоги'],
        }
    
    def execute(self, text):
        text_lower = text.lower()
        for intent, keywords in self.intents.items():
            for kw in keywords:
                if kw in text_lower:
                    return intent
        return 'chat'

class AgentCommandExecutor(MicroAgent):
    def __init__(self):
        super().__init__("command_executor", "Выполняет команды")
    
    def execute(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr
        except Exception as e:
            return f"Ошибка: {e}"

class AgentTimeGetter(MicroAgent):
    def __init__(self):
        super().__init__("time_getter", "Показывает время")
    
    def execute(self, _):
        now = datetime.now()
        return now.strftime("%A, %d %B %Y, %H:%M:%S %Z")

class AgentUpdateChecker(MicroAgent):
    def __init__(self):
        super().__init__("update_checker", "Проверяет обновления")
    
    def execute(self, _):
        try:
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", 
                                   shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            if count and int(count) > 0:
                return f"⚠️ Доступно {count} обновлений"
            return "✅ Система обновлена"
        except:
            return "❌ Не удалось проверить обновления"

class AgentUpgrader(MicroAgent):
    def __init__(self):
        super().__init__("upgrader", "Устанавливает обновления")
    
    def execute(self, _):
        try:
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", 
                                   shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            if count and int(count) > 0:
                print("⚠️ Обновления найдены. Начинаю установку...")
                result = subprocess.run("sudo pacman -Syu --noconfirm", 
                                       shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    return "✅ Система успешно обновлена!"
                else:
                    return f"❌ Ошибка: {result.stderr}"
            else:
                return "✅ Обновлений не найдено"
        except Exception as e:
            return f"❌ Ошибка: {e}"

class AgentLLM(MicroAgent):
    def __init__(self):
        super().__init__("llm", "Отвечает через LLM")
    
    def execute(self, prompt):
        try:
            safe_prompt = prompt.replace('"', '\\"').replace("'", "\\'")
            cmd = f'ollama run qwen2.5-coder:7b "{safe_prompt}"'
            print("🧠 Думаю...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "⏱️ Превышено время (15 сек). Попробуйте проще."
        except Exception as e:
            return f"❌ Ошибка: {e}"

class AuraOrchestrator:
    def __init__(self):
        self.agents = {
            'noise_filter': AgentNoiseFilter(),
            'text_parser': AgentTextParser(),
            'word_joiner': AgentWordJoiner(),
            'intent': AgentIntentRecognizer(),
            'shell': AgentCommandExecutor(),
            'time': AgentTimeGetter(),
            'updates': AgentUpdateChecker(),
            'upgrader': AgentUpgrader(),
            'llm': AgentLLM(),
        }
    
    def process(self, user_input):
        print(f"\n👤 Вы: {user_input}")
        
        cleaned = self.agents['noise_filter'].execute(user_input)
        words = self.agents['text_parser'].execute(cleaned)
        sentence = self.agents['word_joiner'].execute(words)
        intent = self.agents['intent'].execute(sentence)
        
        print(f"🧠 Намерение: {intent}")
        
        if intent == 'time':
            response = self.agents['time'].execute(None)
        elif intent == 'update':
            response = self.agents['updates'].execute(None)
        elif intent == 'upgrade':
            response = self.agents['upgrader'].execute(None)
        elif intent == 'shell':
            cmd_match = re.search(r'(?:выполни|запусти|команду?)\s+(.+)', sentence, re.IGNORECASE)
            if cmd_match:
                response = self.agents['shell'].execute(cmd_match.group(1).strip())
            else:
                response = "Не понял команду. Скажи: 'выполни date'"
        elif intent == 'help':
            response = """🦾 Я умею:
- ⌚ Показывать время
- 📦 Проверять обновления
- 💻 Выполнять команды
- 💬 Общаться через LLM"""
        else:
            response = self.agents['llm'].execute(sentence)
        
        print(f"🤖 Аура: {response}")
        return response

def main():
    aura = AuraOrchestrator()
    print("\n" + "="*60)
    print("🦾 АУРА - Фрактальный мульти-агент")
    print("="*60)
    print("Введите 'exit' для выхода\n")
    
    while True:
        try:
            user_input = input("👤 Вы: ").strip()
            if user_input.lower() in ['exit', 'quit', 'выход']:
                print("🦾 Аура: До свидания! 👋")
                break
            if user_input:
                aura.process(user_input)
        except KeyboardInterrupt:
            print("\n🦾 Аура: До свидания! 👋")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
