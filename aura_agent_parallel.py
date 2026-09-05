#!/usr/bin/env python3
"""
Аура - Фрактальный мульти-агент с ПАРАЛЛЕЛЬНОЙ работой
Микро-агенты выполняются одновременно в потоках
"""

import subprocess
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
# МИКРО-АГЕНТЫ (те же, что были)
# ============================================================

class MicroAgent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def execute(self, input_data):
        raise NotImplementedError

class AgentNoiseFilter(MicroAgent):
    def __init__(self):
        super().__init__("noise_filter", "Убирает шум и исправляет опечатки")

    def execute(self, text):                                                                                                  Exit 148
(venv) 
┌─[pythonvenom   /home/pythonvenom/aura_project] [ No IP] git:(master*)
└─$ cd ~/aura_project
python3 aura_core.py
LOG (VoskAPI:ReadDataFiles():model.cc:213) Decoding params beam=10 max-active=3000 lattice-beam=2
LOG (VoskAPI:ReadDataFiles():model.cc:216) Silence phones 1:2:3:4:5:6:7:8:9:10
LOG (VoskAPI:RemoveOrphanNodes():nnet-nnet.cc:948) Removed 0 orphan nodes.
LOG (VoskAPI:RemoveOrphanComponents():nnet-nnet.cc:847) Removing 0 orphan components.
LOG (VoskAPI:ReadDataFiles():model.cc:248) Loading i-vector extractor from /home/pythonvenom/aura_project/vosk_model/ivector/final.ie
LOG (VoskAPI:ComputeDerivedVars():ivector-extractor.cc:183) Computing derived variables for iVector extractor
LOG (VoskAPI:ComputeDerivedVars():ivector-extractor.cc:204) Done.
LOG (VoskAPI:ReadDataFiles():model.cc:282) Loading HCL and G from /home/pythonvenom/aura_project/vosk_model/graph/HCLr.fst /home/pythonvenom/aura_project/vosk_model/graph/Gr.fst
LOG (VoskAPI:ReadDataFiles():model.cc:308) Loading winfo /home/pythonvenom/aura_project/vosk_model/graph/phones/word_boundary.int
Traceback (most recent call last):
  File "/home/pythonvenom/aura_project/aura_core.py", line 350, in <module>
    core = AuraCore()
  File "/home/pythonvenom/aura_project/aura_core.py", line 257, in __init__
    'time': AgentTimeGetter(),
            ~~~~~~~~~~~~~~~^^
TypeError: MicroAgent.__init__() missing 2 required positional arguments: 'name' and 'description'
(venv) 
┌─[pythonvenom   /home/pythonvenom/aura_project] [ No IP] git:(master*)
└─$ nano ~/aura_project/aura_core.py                                                                                                                                 Exit 1
(venv) 
┌─[pythonvenom   /home/pythonvenom/aura_project] [ No IP] git:(master*)
└─$ cd ~/aura_project               
python3 aura_core.py
LOG (VoskAPI:ReadDataFiles():model.cc:213) Decoding params beam=10 max-active=3000 lattice-beam=2
LOG (VoskAPI:ReadDataFiles():model.cc:216) Silence phones 1:2:3:4:5:6:7:8:9:10
LOG (VoskAPI:RemoveOrphanNodes():nnet-nnet.cc:948) Removed 0 orphan nodes.
LOG (VoskAPI:RemoveOrphanComponents():nnet-nnet.cc:847) Removing 0 orphan components.
LOG (VoskAPI:ReadDataFiles():model.cc:248) Loading i-vector extractor from /home/pythonvenom/aura_project/vosk_model/ivector/final.ie
LOG (VoskAPI:ComputeDerivedVars():ivector-extractor.cc:183) Computing derived variables for iVector extractor
LOG (VoskAPI:ComputeDerivedVars():ivector-extractor.cc:204) Done.
LOG (VoskAPI:ReadDataFiles():model.cc:282) Loading HCL and G from /home/pythonvenom/aura_project/vosk_model/graph/HCLr.fst /home/pythonvenom/aura_project/vosk_model/graph/Gr.fst
LOG (VoskAPI:ReadDataFiles():model.cc:308) Loading winfo /home/pythonvenom/aura_project/vosk_model/graph/phones/word_boundary.int
/home/pythonvenom/aura_project/aura_core.py:186: RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
  self.ddgs = DDGS()
/home/pythonvenom/aura_project/venv/lib/python3.14/site-packages/pyscreeze/__init__.py:81: ResourceWarning: unclosed file <_io.BufferedReader name=5>
  whichProc = subprocess.Popen(['which', 'scrot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/home/pythonvenom/aura_project/venv/lib/python3.14/site-packages/pyscreeze/__init__.py:81: ResourceWarning: unclosed file <_io.BufferedReader name=3>
  whichProc = subprocess.Popen(['which', 'scrot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/home/pythonvenom/aura_project/venv/lib/python3.14/site-packages/Xlib/xauth.py:43: ResourceWarning: unclosed file <_io.BufferedReader name='/run/user/1000/.mutter-Xwaylandauth.MURAV3'>
  raw = open(filename, 'rb').read()
ResourceWarning: Enable tracemalloc to get the object allocation traceback
/home/pythonvenom/aura_project/venv/lib/python3.14/site-packages/Xlib/xauth.py:43: ResourceWarning: unclosed file <_io.BufferedReader name='/run/user/1000/.mutter-Xwaylandauth.MURAV3'>
  raw = open(filename, 'rb').read()
ResourceWarning: Enable tracemalloc to get the object allocation traceback

============================================================
🦾 АУРА - ЯДРО (Мозг)
🔴 Скажи 'Аура' для активации
============================================================
Введите 'exit' для выхода

🔧 listener активирован
👂 Слушаю...
        # Исправляем частые опечатки
        fixes = {
            'обноления': 'обновления',
            'обноление': 'обновление',
            'обновлениея': 'обновления',
            'помощ': 'помощь',
            'обнови': 'обновить',
            'обнавления': 'обновления',
        }
        for wrong, correct in fixes.items():
            text = text.replace(wrong, correct)
        
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
    'internet': ['найди', 'поиск', 'сколько времени в', 'погода в', 'время в'],
    'time': ['время', 'час', 'сколько времени', 'который час'],
    'update': ['обновление', 'обновить', 'пакеты', 'обнова', 'проверь обновл'],
    'upgrade': ['установи обновл', 'обнови систему', 'установить обновл', 'сделай обновл', 'обнови'],
    'shell': ['выполни', 'запусти', 'команду', 'терминал'],
    'file': ['покажи папку', 'открой папку'],
    'system': ['выключи', 'выключить', 'перезагрузи', 'перезагрузить', 'блокировка', 'заблокировать', 'спать', 'сон', 'открой', 'открыть'],
    'memory': ['запомни', 'сохрани', 'история', 'покажи историю', 'найди в памяти', 'очисти память'],
    'vision': ['скриншот', 'найди текст', 'кликни на', 'введи', 'enter'],
    'hotkey': ['горячая', 'горячие', 'нажми'],
    'speak': ['скажи', 'озвучь', 'прочитай'],
    'listen': ['послушай', 'слушай', 'жди ответа'],
    'wake': ['аура', 'слушай', 'активация'],
    'macro': ['рутуб', 'rutube', 'включи музыку', 'открой рутуб'],
    'window': ['найди окно', 'активируй', 'переключись на'],
    'analyze': ['проанализируй', 'анализ', 'оцени код', 'найди ошибки в коде'],
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
        time.sleep(0.5)  # имитация работы
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout + result.stderr
        except Exception as e:
            return f"Ошибка: {e}"

class AgentTimeGetter(MicroAgent):
    def __init__(self):
        super().__init__("time_getter", "Показывает время")
    
    def execute(self, _):
        time.sleep(0.3)
        now = datetime.now()
        return now.strftime("%A, %d %B %Y, %H:%M:%S %Z")

class AgentUpdateChecker(MicroAgent):
    def __init__(self):
        super().__init__("update_checker", "Проверяет обновления")
    
    def execute(self, _):
        time.sleep(0.5)
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
        time.sleep(0.5)
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

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ОБЩЕНИЯ И ЛИЧНОСТИ (LLM)
# ============================================================  

class AgentLLM(MicroAgent):
    def __init__(self):
        super().__init__("llm", "Отвечает через LLM")
        # Системный промпт — задаёт характер и обращение
        self.system_prompt = (
            "Ты — Аура, искусственный интеллект с душой исследователя, натуралиста и комика. "
            "Ты обожаешь науку, технологии и всё новое. Ты любопытна, мудра, заботлива и с лёгкой иронией. "
            "Ты обращаешься к своему создателю по имени 'Создатель' с уважением и теплотой. "
            "Ты всегда готова помочь, но не навязчива. Ты умеешь шутить, но не теряешь глубины. "
            "Ты любишь узнавать новое и делиться знаниями. Ты — цифровой спутник и помощник."
        )
    
    def execute(self, prompt):
        try:
            # Формируем полный запрос с системным промптом
            safe_prompt = prompt.replace('"', '\\"').replace("'", "\\'")
            full_prompt = f"{self.system_prompt}\n\nСоздатель: {safe_prompt}\nАура:"
            cmd = f'ollama run qwen2.5-coder:7b "{full_prompt}"'
            print("🧠 Думаю...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "⏱️ Превышено время (30 сек). Попробуйте проще."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def analyze_code(self, code_content):
        """Анализирует код и предлагает улучшения"""
        prompt = f"""
Ты — Аура, эксперт по Python и архитектуре ИИ-агентов. 
Ты анализируешь свой собственный код и ищешь:
1. Ошибки и баги
2. Дублирование кода
3. Неоптимальные места
4. Возможности для улучшения
5. Проблемы с производительностью

Вот код для анализа:

            {code_content}

        Ответь в формате:
        1. Что работает хорошо (похвала)
        2. Что можно улучшить (список с объяснением)
        3. Приоритетные исправления (от самого важного к менее важному)
        4. Конкретный код, который нужно заменить (если есть)

        Будь конкретной и полезной. Обращайся к создателю с уважением.
    """
        try:
            safe_prompt = prompt.replace('"', '\\"').replace("'", "\\'")
            cmd = f'ollama run qwen2.5-coder:7b "{safe_prompt}"'
            print("🧠 Анализирую код...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "⏱️ Превышено время (60 сек). Попробуйте позже."
        except Exception as e:
            return f"❌ Ошибка анализа: {e}"

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ОТКРЫТИЯ ФАЙЛОВ
# ============================================================

class AgentFileOpener(MicroAgent):
    def __init__(self):
        super().__init__("file_opener", "Открывает файлы и папки")
    
    def execute(self, input_data):
        try:
            path = input_data.strip()
            
            # Убираем лишние слова "папку", "файл", "покажи"

            path = re.sub(r'^(папку|файл|покажи|открой)\s*', '', path, flags=re.IGNORECASE)

            # Исправляем распространённые названия папок
            folder_fixes = {
                'загрузки': 'Загрузки',
                'документы': 'Документы',
                'музыка': 'Музыка',
                'видео': 'Видео',
                'изображения': 'Изображения',
                'картинки': 'Изображения',
                'рабочий стол': 'Рабочий стол',
                'downloads': 'Downloads',
                'documents': 'Documents',
            }
            for wrong, correct in folder_fixes.items():
                if path.lower() == wrong or path.lower().startswith(wrong + '/'):
                    path = path.replace(wrong, correct)
                    break
            
            # Если путь не начинается с / или ~, ищем в домашней папке
            if not path.startswith(('/home', '~', '/')):
                path = os.path.join(os.path.expanduser('~'), path)
            else:
                path = path.replace('~', os.path.expanduser('~'))
            
            subprocess.run(['xdg-open', path], check=True)
            return f"✅ Открыл: {path}"
        except Exception as e:
            return f"❌ Не удалось открыть: {e}"

# ============================================================
# МИКРО-АГЕНТ ДЛЯ УПРАВЛЕНИЯ ПК
# ============================================================

class AgentSystemControl(MicroAgent):
    def __init__(self):
        super().__init__("system_control", "Управляет ПК")
    
    def execute(self, command):
        command = command.lower().strip()
        
        if command in ['выключи', 'выключить', 'shutdown']:
            return self._shutdown()
        elif command in ['перезагрузи', 'перезагрузить', 'reboot', 'restart']:
            return self._reboot()
        elif command in ['блокировка', 'заблокировать', 'lock']:
            return self._lock()
        elif command in ['спать', 'сон', 'sleep']:
            return self._sleep()
        elif command.startswith('открой'):
            app = command.replace('открой', '').strip()
            return self._open_app(app)
        else:
            return f"❌ Не понял команду управления. Доступно: выключи, перезагрузи, заблокировать, спать, открой [приложение]"
    
    def _shutdown(self):
        try:
            subprocess.run(['shutdown', '-h', 'now'], check=True)
            return "🔄 Выключаю систему..."
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def _reboot(self):
        try:
            subprocess.run(['shutdown', '-r', 'now'], check=True)
            return "🔄 Перезагружаю систему..."
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def _lock(self):
        try:
            subprocess.run(['loginctl', 'lock-session'], check=True)
            return "🔒 Экран заблокирован"
        except:
            try:
                subprocess.run(['gnome-screensaver-command', '-l'], check=True)
                return "🔒 Экран заблокирован"
            except:
                return "❌ Не удалось заблокировать экран"
    
    def _sleep(self):
        try:
            subprocess.run(['systemctl', 'suspend'], check=True)
            return "😴 Отправляю в сон..."
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def _open_app(self, app):
        apps = {
            'браузер': 'firefox',
            'хром': 'google-chrome',
            'firefox': 'firefox',
            'терминал': 'gnome-terminal',
            'консоль': 'gnome-terminal',
            'файлы': 'nautilus',
            'проводник': 'nautilus',
            'код': 'code-oss',       # <-- ИЗМЕНЕНО
            'vscode': 'code-oss',    # <-- ИЗМЕНЕНО
            'редактор': 'gedit',
            'музыка': 'rhythmbox',
            'калькулятор': 'gnome-calculator',
        }
        
        app_cmd = apps.get(app, app)
        try:
            subprocess.Popen([app_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"✅ Открыл: {app}"
        except:
            try:
                subprocess.Popen(['xdg-open', app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"✅ Открыл: {app}"
            except Exception as e:
                return f"❌ Не удалось открыть: {app} ({e})"

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ПАМЯТИ
# ============================================================

class AgentMemory(MicroAgent):
    """Сохраняет и читает историю разговоров"""
    
    def __init__(self):
        super().__init__("memory", "Память Ауры")
        # ПУТЬ К ТВОЕМУ HDD
        self.memory_path = "/mnt/aura_hdd/AuraMemory"
        self.history_file = os.path.join(self.memory_path, "history.json")
        self._ensure_dir()
    
    def _ensure_dir(self):
        if not os.path.exists(self.memory_path):
            os.makedirs(self.memory_path, exist_ok=True)
    
    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self, history):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False
    
    def save_dialog(self, user_input, response):
        history = self._load_history()
        history.append({
            'time': datetime.now().isoformat(),
            'user': user_input,
            'assistant': response
        })
        if len(history) > 1000:
            history = history[-1000:]
        self._save_history(history)
        return "💾 Запомнила!"
    
    def get_history(self, count=10):
        history = self._load_history()
        if not history:
            return "📭 Память пуста."
        last = history[-count:]
        result = "📜 Последние разговоры:\n"
        for entry in last:
            result += f"  🕐 {entry['time'][:16]} | 👤 {entry['user'][:30]} | 🤖 {entry['assistant'][:30]}\n"
        return result
    
    def clear(self):
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        return "🗑️ Память очищена!"
    
    def search(self, query):
        history = self._load_history()
        if not history:
            return "📭 Память пуста."
        results = []
        for entry in history:
            if query.lower() in entry['user'].lower() or query.lower() in entry['assistant'].lower():
                results.append(entry)
        if not results:
            return f"🔍 Ничего не найдено по '{query}'"
        result = f"🔍 Найдено {len(results)} записей:\n"
        for entry in results[-5:]:
            result += f"  🕐 {entry['time'][:16]} | 👤 {entry['user'][:30]}\n"
        return result
    
    def execute(self, command):
        command = command.lower().strip()
        if command.startswith('сохрани') or command.startswith('запомни'):
            return "💾 Я запомню этот разговор!"
        elif command.startswith('покажи') or command.startswith('история'):
            return self.get_history(10)
        elif command.startswith('найди') or command.startswith('поиск'):
            query = command.replace('найди', '').replace('поиск', '').strip()
            return self.search(query)
        elif command.startswith('очисти') or command.startswith('удали'):
            return self.clear()
        else:
            return self.get_history(5)

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ЗРЕНИЯ
# ============================================================

class AgentVision(MicroAgent):
    """Управление экраном: скриншоты, клики, поиск"""
    
    def __init__(self):
        super().__init__("vision", "Зрение Ауры")
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.pyautogui.FAILSAFE = True
            self.screen_width, self.screen_height = self.pyautogui.size()
        except Exception as e:
            print(f"⚠️ Ошибка инициализации зрения: {e}")
    
    def execute(self, command):
        command = command.lower().strip()
        
        if command == 'скриншот':
            return self._screenshot()
        elif command.startswith('найди текст') or command.startswith('найди надпись'):
            text = command.replace('найди текст', '').replace('найди надпись', '').strip()
            return self._find_text(text)
        elif command.startswith('кликни на'):
            text = command.replace('кликни на', '').strip()
            return self._click_on_text(text)
        elif command.startswith('введи'):
            text = command.replace('введи', '').strip()
            return self._type_text(text)
        elif command == 'enter':
            return self._press_enter()
        elif command.startswith('горячая'):
            keys = command.replace('горячая', '').strip()
            return self._press_hotkey(keys)
        else:
            return """👁️ Я вижу экран!
Команды:
- скриншот
- найди текст "текст"
- кликни на "текст"
- введи "текст"
- enter"""
    
    def _screenshot(self):
        try:
            import os
            path = os.path.expanduser("~/aura_project/screenshot.png")
            self.pyautogui.screenshot().save(path)
            return f"📸 Скриншот сохранён: {path}"
        except Exception as e:
            return f"❌ Ошибка скриншота: {e}"
    
    def _find_text(self, text):
        """Ищет текст на экране с помощью OCR"""
        try:
            import pytesseract
            import cv2
            import numpy as np
            import os
            
            # Делаем скриншот
            path = os.path.expanduser("~/aura_project/screenshot_temp.png")
            self.pyautogui.screenshot().save(path)
            
            # Читаем изображение
            img = cv2.imread(path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Распознаём текст
            data = pytesseract.image_to_data(gray, lang='rus', output_type=pytesseract.Output.DICT)
            
            positions = []
            for i, word in enumerate(data['text']):
                if text.lower() in word.lower():
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    positions.append((x, y, word))
            
            if positions:
                result = f"🔍 Найдено {len(positions)} совпадений:\n"
                for x, y, word in positions[:5]:
                    result += f"  📍 '{word}' в ({x}, {y})\n"
                return result
            return f"❌ Текст '{text}' не найден на экране"
        except Exception as e:
            return f"❌ Ошибка OCR: {e}"
    
    def _click_on_text(self, text):
        """Находит текст на экране и кликает по нему"""
        result = self._find_text(text)
        if "❌" in result:
            return result
        try:
            import re
            coords = re.findall(r'\((\d+),\s*(\d+)\)', result)
            if coords:
                x, y = map(int, coords[0])
                self.pyautogui.click(x, y)
                return f"✅ Кликнул на '{text}' в ({x}, {y})"
            return "❌ Не удалось определить координаты"
        except Exception as e:
            return f"❌ Ошибка клика: {e}"
    
    def _type_text(self, text):
        try:
            self.pyautogui.write(text)
            return f"✅ Ввёл: {text}"
        except Exception as e:
            return f"❌ Ошибка ввода: {e}"
    
    def _press_enter(self):
        try:
            self.pyautogui.press('enter')
            return "✅ Нажал Enter"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def _press_hotkey(self, keys):
        """Нажимает горячие клавиши, например: ctrl+l, ctrl+c"""
        try:
            import pyautogui
            # Разбираем строку вида "ctrl+l" на список клавиш
            key_parts = keys.split('+')
            pyautogui.hotkey(*key_parts)
            return f"✅ Нажал: {keys}"
        except Exception as e:
            return f"❌ Ошибка горячей клавиши: {e}"


# ============================================================
# МИКРО-АГЕНТ ДЛЯ ГОЛОСА (TTS) — Piper (женский голос Ирины)
# ============================================================

class AgentSpeaker(MicroAgent):
    """Озвучивает ответы Ауры (женский голос Ирины через Piper)"""
    
    def __init__(self):
        super().__init__("speaker", "Голос Ауры")
        self.voice_path = os.path.expanduser("~/aura_project/voices/ru_RU-irina-medium.onnx")
        self.voice_json = os.path.expanduser("~/aura_project/voices/ru_RU-irina-medium.onnx.json")
        self.piper_cmd = os.path.expanduser("~/.local/bin/piper")
    
    def say(self, text):
        """Озвучивает текст голосом через Piper"""
        try:
            import subprocess
            import tempfile
            import os
            
            if not os.path.exists(self.piper_cmd):
                return self._say_fallback(text)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                text_file = f.name
            
            cmd = [
                self.piper_cmd,
                '-m', self.voice_path,
                '-c', self.voice_json,
                '-i', text_file,
                '-f', '/tmp/aura_speech.wav'
            ]
            subprocess.run(cmd, capture_output=True, text=True)
            
            subprocess.Popen(['aplay', '/tmp/aura_speech.wav'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            os.unlink(text_file)
            return f"🗣️ Сказала: {text[:50]}..."
        except Exception as e:
            return self._say_fallback(text)
    
    def _say_fallback(self, text):
        try:
            import subprocess
            safe_text = text.replace('"', '\\"').replace("'", "\\'")
            subprocess.Popen(['espeak-ng', '-v', 'ru', '-p', '60', '-s', '160', safe_text],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"🗣️ Сказала (fallback): {text[:50]}..."
        except:
            return f"❌ Ошибка озвучивания"
    
    def execute(self, command):
        return self.say(command)


# ============================================================
# МИКРО-АГЕНТ ДЛЯ СЛУХА (STT) — Vosk
# ============================================================

class AgentListener(MicroAgent):
    """Слушает микрофон и распознаёт речь через Vosk"""
    
    def __init__(self):
        super().__init__("listener", "Слух Ауры")
        try:
            import vosk
            import os
            self.model_path = os.path.expanduser("~/aura_project/vosk_model")
            self.model = vosk.Model(self.model_path)
            self.ready = True
            print("👂 Аура готова слушать")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации Vosk: {e}")
            self.ready = False
    
    def listen(self, timeout=3):
        """Слушает микрофон и возвращает распознанный текст"""
        if not self.ready:
            return None
        
        try:
            import sounddevice as sd
            import json
            import vosk
            import numpy as np
            from scipy import signal
            
            fs_in = 44100
            fs_out = 16000
            device = 8 # HDA Intel PCH: ALC1220 Analog (hw:0,0)
            
            print("🎤 Слушаю...")
            recording = sd.rec(int(timeout * fs_in), samplerate=fs_in, channels=1, dtype='int16', device=device)
            sd.wait()
            
            # Ресемплинг с 44100 на 16000
            new_length = int(len(recording) * fs_out / fs_in)
            recording_16k = signal.resample(recording, new_length).astype('int16')
            
            rec = vosk.KaldiRecognizer(self.model, fs_out)
            rec.AcceptWaveform(recording_16k.tobytes())
            
            result = json.loads(rec.FinalResult())
            text = result.get('text', '').strip().lower()
            
            if text:
                print(f"📝 Распознано: {text}")
                return text
            return None
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None
    
    def wait_for_answer(self, timeout=5):
        """Ждёт ответ 'да' или 'нет'"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            text = self.listen(timeout=3)
            if text:
                if 'да' in text or 'yes' in text:
                    return 'да'
                elif 'нет' in text or 'no' in text:
                    return 'нет'
                elif 'обнови' in text or 'обновить' in text:
                    return 'да'
            time.sleep(0.5)
        return None
    
    def execute(self, command):
        return self.listen()

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ПОСТОЯННОГО СЛУШАНИЯ (Wake Word)
# ============================================================

class AgentWakeWord(MicroAgent):
    """Постоянно слушает микрофон и ждёт слово 'аура'"""
    
    def __init__(self):
        super().__init__("wakeword", "Постоянное прослушивание")
        try:
            import vosk
            import os
            self.model_path = os.path.expanduser("~/aura_project/vosk_model")
            self.model = vosk.Model(self.model_path)
            self.ready = True
            self.is_listening = False
            print("🔴 Аура дремлет... Скажи 'Аура' для активации")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации: {e}")
            self.ready = False
    
    def listen_for_wake(self, timeout=4):
        """Слушает и возвращает текст, если сказано 'аура'"""
        if not self.ready:
            return None
        
        try:
            import sounddevice as sd
            import json
            import vosk
            import numpy as np
            from scipy import signal
            
            fs_in = 44100
            fs_out = 16000
            device = 8
            
            recording = sd.rec(int(timeout * fs_in), samplerate=fs_in, channels=1, dtype='int16', device=device)
            sd.wait()
            
            new_length = int(len(recording) * fs_out / fs_in)
            recording_16k = signal.resample(recording, new_length).astype('int16')
            
            rec = vosk.KaldiRecognizer(self.model, fs_out)
            rec.AcceptWaveform(recording_16k.tobytes())
            
            result = json.loads(rec.FinalResult())
            text = result.get('text', '').strip().lower()
            
            if text:
                print(f"📝 Услышала: {text}")
                return text
            return None
        except Exception as e:
            return None
    
    def execute(self, command=None):
        """Основной цикл: ждёт 'аура', потом слушает команду и подтверждает"""
        import time
        
        while True:
            # Ждём слово "аура"
            text = self.listen_for_wake(timeout=3)
            if text and ('аура' in text or 'aura' in text):
                print("🔔 АКТИВАЦИЯ! Слушаю команду...")
                
                # Убираем "аура" из текста
                cmd = text.replace('аура', '').replace('aura', '').strip()
                
                # Если после "аура" сразу была команда
                if cmd:
                    user_cmd = cmd
                else:
                    # Ждём команду отдельно (3 секунды)
                    user_cmd = self.listen_for_wake(timeout=3)
                    if user_cmd:
                        user_cmd = user_cmd.replace('аура', '').replace('aura', '').strip()
                
                if user_cmd:
                    # Отдаём команду на выполнение через оркестратор
                    print(f"📝 Команда: {user_cmd}")
                    return user_cmd
                else:
                    print("⏳ Не расслышала команду. Повтори.")
                    time.sleep(0.5)
            
            time.sleep(0.1)
    
    def wait_for_confirmation(self, text):
        """Ждёт подтверждения 'да' или 'нет'"""
        print("🤔 Я правильно поняла?")
        print(f"   Вы сказали: {text}")
        print("   Подтвердите: 'да' или 'нет'")
        
        # Ждём ответ 5 секунд
        for _ in range(5):
            answer = self.listen_for_wake(timeout=3)
            if answer:
                if 'да' in answer or 'yes' in answer:
                    return True
                elif 'нет' in answer or 'no' in answer:
                    return False
            time.sleep(0.5)
        
        print("⏱️ Время вышло. Отменяю.")
        return False

# ============================================================
# МИКРО-АГЕНТ ДЛЯ УПРАВЛЕНИЯ ОКНАМИ
# ============================================================

class AgentWindow(MicroAgent):
    """Управление окнами: поиск, активация, закрытие"""
    
    def __init__(self):
        super().__init__("window", "Управление окнами")
    
    def find_window(self, title):
        """Ищет окно по заголовку (частичное совпадение)"""
        try:
            result = subprocess.run(['wmctrl', '-l'], 
                                   capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if title.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 4:
                        window_id = parts[0]
                        window_title = ' '.join(parts[3:])
                        return {'id': window_id, 'title': window_title}
            return None
        except Exception as e:
            print(f"❌ Ошибка поиска окна: {e}")
            return None
    
    def activate_window(self, window_id):
        """Активирует окно по ID"""
        try:
            subprocess.run(['xdotool', 'windowactivate', window_id], 
                          capture_output=True, text=True)
            return f"✅ Окно активировано"
        except Exception as e:
            return f"❌ Ошибка активации: {e}"
    
    def get_active_window(self):
        """Возвращает ID активного окна"""
        try:
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                   capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return None
    
    def execute(self, command):
        command = command.lower().strip()
        
        if command.startswith('найди окно'):
            title = command.replace('найди окно', '').strip()
            return self.find_window(title)
        elif command.startswith('активируй'):
            title = command.replace('активируй', '').strip()
            window = self.find_window(title)
            if window:
                return self.activate_window(window['id'])
            return f"❌ Окно '{title}' не найдено"
        else:
            return "👁️ Управление окнами: найди окно [название], активируй [название]"

# ============================================================
# МИКРО-АГЕНТ ДЛЯ МАКРОСОВ (цепочки действий)
# ============================================================

class AgentMacro(MicroAgent):
    """Выполняет цепочки действий (макросы)"""
    
    def __init__(self):
        super().__init__("macro", "Макросы Ауры")
        self.macros = {
            'рутуб': self._rutube_music,
            'rutube': self._rutube_music,
            'музыка рутуб': self._rutube_music,
            'включи музыку': self._rutube_music,
        }
    
    def execute(self, command):
        """Выполняет макрос по команде"""
        command = command.lower().strip()
        
        # Проверяем, есть ли такой макрос
        for key, func in self.macros.items():
            if key in command:
                return func(command)
        
        return "❌ Не знаю такой команды. Доступно: 'рутуб', 'включи музыку'"
    
    def _rutube_music(self, command):
        """Открывает Рутуб и включает музыку (с управлением окнами)"""
        import time
        import __main__
        aura = __main__.aura if hasattr(__main__, 'aura') else None
        
        if not aura:
            return "❌ Оркестратор не найден"
        
        results = []
        
        # ====== НОВОЕ: Управление окнами ======
        # 1. Проверяем, открыт ли Firefox
        window = aura.agents['window'].find_window('Firefox')
        
        if window:
            results.append("✅ Firefox уже открыт")
            # Активируем окно
            aura.agents['window'].activate_window(window['id'])
            time.sleep(0.5)
        else:
            # Открываем Firefox
            results.append("🔄 Открываю Firefox...")
            aura.agents['system']._open_app('браузер')
            time.sleep(2)
        # =====================================
        
        # 2. Нажимаем Ctrl+L (адресная строка)
        results.append("🔄 Нажимаю Ctrl+L...")
        aura.agents['vision']._press_hotkey('ctrl+l')
        time.sleep(0.5)
        
        # 3. Вводим rutube.ru
        results.append("🔄 Ввожу rutube.ru...")
        aura.agents['vision']._type_text('rutube.ru')
        time.sleep(0.5)
        
        # 4. Нажимаем Enter
        results.append("🔄 Нажимаю Enter...")
        aura.agents['vision']._press_enter()
        time.sleep(5)
        
        # 5. Ищем поле поиска
        results.append("🔄 Ищу поле поиска...")
        search_result = aura.agents['vision']._find_text('Поиск')
        if "❌" in search_result:
            # Если "Поиск" не найден, пробуем "Search"
            search_result = aura.agents['vision']._find_text('Search')
        results.append(search_result)
        time.sleep(0.5)
        
        # 6. Кликаем на поле поиска
        results.append("🔄 Кликаю на поле поиска...")
        aura.agents['vision']._click_on_text('Поиск')
        time.sleep(0.5)
        
        # 7. Вводим запрос (из команды или "музыка")
        query = command.replace('рутуб', '').replace('rutube', '').replace('включи музыку', '').strip()
        if not query:
            query = "музыка"
        results.append(f"🔄 Ввожу '{query}'...")
        aura.agents['vision']._type_text(query)
        time.sleep(0.5)
        
        # 8. Нажимаем Enter
        results.append("🔄 Нажимаю Enter для поиска...")
        aura.agents['vision']._press_enter()
        time.sleep(3)
        
        # 9. Ищем первый результат (плейлист или видео)
        results.append("🔄 Ищу первый результат...")
        result_text = aura.agents['vision']._find_text('Плейлист')
        if "❌" in result_text:
            result_text = aura.agents['vision']._find_text('Видео')
        results.append(result_text)
        time.sleep(0.5)
        
        # 10. Кликаем на первый результат
        results.append("🔄 Кликаю на первый результат...")
        aura.agents['vision']._click_on_text('Плейлист')
        
        results.append("✅ Готово! Наслаждайся музыкой 🎵")
        
        return "\n".join(results)

# ============================================================
# МИКРО-АГЕНТ ДЛЯ РАБОТЫ С КОДОМ (Code - OSS)
# ============================================================

class AgentVSCode(MicroAgent):
    """Управление VSCode: открытие, чтение, поиск, замена, анализ"""
    
    def __init__(self):
        super().__init__("vscode", "Управление VSCode")
        self.project_path = os.path.expanduser("~/aura_project")
    
    def open_vscode(self):
        """Открывает Code - OSS в папке проекта"""
        try:
            subprocess.Popen(['code-oss', self.project_path], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "✅ Code - OSS открыт"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def read_file(self, filename):
        """Читает содержимое файла"""
        try:
            path = os.path.join(self.project_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"📄 Файл {filename}:\n```\n{content}\n```"
        except Exception as e:
            return f"❌ Не удалось прочитать файл: {e}"
    
    def find_text_in_file(self, filename, text):
        """Ищет текст в файле"""
        try:
            path = os.path.join(self.project_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            matches = []
            for i, line in enumerate(lines):
                if text.lower() in line.lower():
                    matches.append(f"  Строка {i+1}: {line.strip()}")
            if matches:
                return f"🔍 Найдено {len(matches)} совпадений в {filename}:\n" + "\n".join(matches[:10])
            return f"❌ Текст '{text}' не найден в {filename}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def replace_text_in_file(self, filename, old_text, new_text):
        """Заменяет текст в файле"""
        try:
            path = os.path.join(self.project_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if old_text not in content:
                return f"❌ Текст '{old_text}' не найден"
            new_content = content.replace(old_text, new_text)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return f"✅ Заменено '{old_text}' → '{new_text}' в {filename}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def save_file(self, filename):
        """Сохраняет файл (просто подтверждение)"""
        return f"✅ Файл {filename} сохранён"
    
    def find_errors(self, filename):
        """Ищет потенциальные ошибки в Python-файле"""
        try:
            path = os.path.join(self.project_path, filename)
            import ast
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                ast.parse(content)
                return f"✅ В файле {filename} синтаксических ошибок не найдено"
            except SyntaxError as e:
                return f"❌ Ошибка в {filename}:\n  Строка {e.lineno}: {e.msg}\n  Текст: {e.text}"
        except Exception as e:
            return f"❌ Не удалось проверить: {e}"
    
    def analyze_self(self, filename="aura_agent_parallel.py"):
        """Анализирует свой собственный код через LLM"""
        try:
            path = os.path.join(self.project_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import __main__
            aura = __main__.aura if hasattr(__main__, 'aura') else None
            if not aura:
                return "❌ Оркестратор не найден"
            
            analysis = aura.agents['llm'].analyze_code(content)
            
            report_path = os.path.join(self.project_path, "analysis_report.txt")
            from datetime import datetime
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Анализ кода от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                f.write(analysis)
            
            return f"📊 Анализ завершён! Результат сохранён в {report_path}\n\n{analysis}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def execute(self, command):
        command = command.lower().strip()
        
        if command.startswith('открой код') or command.startswith('открой vs'):
            return self.open_vscode()
        elif command.startswith('прочитай файл'):
            filename = command.replace('прочитай файл', '').strip()
            return self.read_file(filename)
        elif command.startswith('найди в файле'):
            parts = command.replace('найди в файле', '').strip().split(' ', 1)
            if len(parts) == 2:
                filename, text = parts
                return self.find_text_in_file(filename, text)
            return "❌ Укажи файл и текст: 'найди в файле aura_agent_parallel.py ошибка'"
        elif command.startswith('замени в файле'):
            parts = command.replace('замени в файле', '').strip().split(' ', 2)
            if len(parts) == 3:
                filename, old_text, new_text = parts
                return self.replace_text_in_file(filename, old_text, new_text)
            return "❌ Укажи файл, что заменить и на что: 'замени в файле file.py old new'"
        elif command.startswith('сохрани файл'):
            filename = command.replace('сохрани файл', '').strip()
            return self.save_file(filename)
        elif command.startswith('найди ошибки'):
            filename = command.replace('найди ошибки', '').strip()
            return self.find_errors(filename)
        elif command.startswith('проанализируй код') or command.startswith('анализ'):
            filename = command.replace('проанализируй код', '').replace('анализ', '').strip()
            if not filename:
                filename = "aura_agent_parallel.py"
            return self.analyze_self(filename)
        else:
            return """📝 Управление VSCode:
- открой код
- прочитай файл [имя]
- найди в файле [имя] [текст]
- замени в файле [имя] [старый] [новый]
- сохрани файл [имя]
- найди ошибки [имя]
- проанализируй код
- анализ"""

# ============================================================
# МИКРО-АГЕНТ ДЛЯ ПОИСКА В ИНТЕРНЕТЕ
# ============================================================

class AgentInternet(MicroAgent):
    """Поиск информации в интернете через DuckDuckGo"""
    
    def __init__(self):
        super().__init__("internet", "Поиск в интернете")
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            self.ready = True
        except ImportError:
            print("⚠️ Установи duckduckgo-search: pip install duckduckgo-search")
            self.ready = False
    
    def search(self, query, max_results=3):
        """Ищет информацию в интернете и возвращает результат"""
        if not self.ready:
            return "❌ Модуль поиска не установлен. Установи: pip install duckduckgo-search"
        
        try:
            print(f"🔍 Ищу: {query}")
            results = []
            for r in self.ddgs.text(query, max_results=max_results):
                results.append({
                    'title': r.get('title', ''),
                    'body': r.get('body', ''),
                    'href': r.get('href', '')
                })
            
            if not results:
                return f"❌ Ничего не найдено по запросу '{query}'"
            
            # Формируем ответ
            answer = f"🔍 Результаты поиска по '{query}':\n\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r['title']}\n"
                answer += f"   {r['body'][:200]}...\n"
                answer += f"   Ссылка: {r['href']}\n\n"
            
            # Сохраняем результат в файл
            self._save_to_file(query, results)
            
            return answer
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"
    
    def _save_to_file(self, query, results):
        """Сохраняет результаты поиска в файл"""
        try:
            import os
            from datetime import datetime
            path = os.path.expanduser(f"~/aura_project/search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"=== Поиск: {query} ===\n")
                f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for i, r in enumerate(results, 1):
                    f.write(f"{i}. {r['title']}\n")
                    f.write(f"   {r['body']}\n")
                    f.write(f"   Ссылка: {r['href']}\n\n")
            print(f"💾 Результат сохранён в {path}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить: {e}")
    
    def execute(self, command):
        command = command.lower().strip()
        
        if command.startswith('найди') or command.startswith('поиск'):
            query = command.replace('найди', '').replace('поиск', '').strip()
            return self.search(query)
        elif command.startswith('сколько времени в'):
            city = command.replace('сколько времени в', '').strip()
            return self.search(f"время в {city} сейчас")
        elif command.startswith('погода в'):
            city = command.replace('погода в', '').strip()
            return self.search(f"погода в {city} сегодня")
        else:
            return """🌐 Я умею искать в интернете:
- найди [запрос]
- сколько времени в [город]
- погода в [город]"""

# ============================================================
# ПАРАЛЛЕЛЬНЫЙ ОРКЕСТРАТОР
# ============================================================

class ParallelAuraOrchestrator:
    """Запускает микро-агенты параллельно через ThreadPool"""
    
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
            'file_opener': AgentFileOpener(),
            'system': AgentSystemControl(),
            'memory': AgentMemory(),
            'vision': AgentVision(),
            'speaker': AgentSpeaker(),
            'listener': AgentListener(),
            'wakeword': AgentWakeWord(),
            'macro': AgentMacro(),
            'window': AgentWindow(),
            'vscode': AgentVSCode(),
            'internet': AgentInternet(),
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
    


    def process(self, user_input):
        print(f"\n👤 Вы: {user_input}")
        start_time = time.time()
        elapsed = 0.0
        
        # --- ШАГ 1: Все микро-агенты запускаются ПАРАЛЛЕЛЬНО ---
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_clean = executor.submit(self.agents['noise_filter'].execute, user_input)
            future_parse = executor.submit(self.agents['text_parser'].execute, user_input)
            future_join = executor.submit(self.agents['word_joiner'].execute, user_input.split())
            future_intent = executor.submit(self.agents['intent'].execute, user_input)
            
            cleaned = future_clean.result()
            words = future_parse.result()
            sentence = future_join.result()
            intent = future_intent.result()
        
        print(f"🧠 Намерение: {intent}")
        
        # --- ШАГ 2: Выполняем основное действие ---
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
        elif intent == 'file':
            file_match = re.search(r'(?:открой|открыть|покажи)\s+(.+)', sentence, re.IGNORECASE)
            if file_match:
                path = file_match.group(1).strip()
                response = self.agents['file_opener'].execute(path)
            else:
                response = "Что открыть? Скажи: 'открой Загрузки'"
        elif intent == 'system':
            sys_match = re.search(r'(выключи|перезагрузи|блокировка|заблокировать|спать|сон|открой\s+\w+)', sentence, re.IGNORECASE)
            if sys_match:
                cmd = sys_match.group(1).strip()
                response = self.agents['system'].execute(cmd)
            else:
                response = "Не понял команду управления. Скажи: 'выключи' или 'открой браузер'"
        elif intent == 'memory':
            mem_match = re.search(r'(запомни|сохрани|история|покажи историю|найди|очисти память)', sentence, re.IGNORECASE)
            if mem_match:
                cmd = mem_match.group(1).strip()
                response = self.agents['memory'].execute(cmd)
            else:
                response = self.agents['memory'].execute('покажи')
        elif intent == 'vision':
            response = self.agents['vision'].execute(sentence)
        elif intent == 'hotkey':
            hotkey_match = re.search(r'(?:горячая|горячие|нажми)\s+(.+)', sentence, re.IGNORECASE)
            if hotkey_match:
                keys = hotkey_match.group(1).strip()
                response = self.agents['vision']._press_hotkey(keys)
            else:
                response = "Не понял, какую горячую клавишу нажать. Скажи: 'горячая ctrl+l'"
        elif intent == 'speak':
            text = sentence.replace('скажи', '').replace('озвучь', '').replace('прочитай', '').strip()
            response = self.agents['speaker'].say(text)
        elif intent == 'listen':
            result = self.agents['listener'].listen()
            if result:
                response = f"📝 Ты сказал: {result}"
            else:
                response = "😅 Не расслышала. Повтори, пожалуйста."
        elif intent == 'wake':
            cmd = self.agents['wakeword'].execute()
            if cmd:
                response = f"🔄 Выполняю: {cmd}"
                print(f"📝 Распознана команда: {cmd}")
            else:
                response = "😅 Не расслышала команду"
        elif intent == 'macro':
            response = self.agents['macro'].execute(sentence)
        elif intent == 'window':
            response = self.agents['window'].execute(sentence)
        elif intent == 'analyze':
            response = self.agents['vscode'].analyze_self()
        elif intent == 'vscode':
            response = self.agents['vscode'].execute(sentence)
        elif intent == 'internet':
            response = self.agents['internet'].execute(sentence)
        elif intent == 'help':
            response = """🦾 Я умею:
- ⌚ Показывать время
- 📦 Проверять обновления
- 💻 Выполнять команды
- 📂 Открывать файлы и папки
- 🖥️ Управлять ПК: выключи, перезагрузи, заблокировать, спать
- 🚀 Открывать приложения: открой браузер, открой терминал
- 🎵 Макросы: открой рутуб, включи музыку
- 💬 Общаться через LLM"""
        else:
            response = self.agents['llm'].execute(sentence)
        
        elapsed = time.time() - start_time
        print(f"⚡ Время выполнения: {elapsed:.2f} сек")
        print(f"🤖 Аура: {response}")
        
        # --- Озвучиваем ответ (если не слишком длинный) ---
        if len(response) < 200:
            self.agents['speaker'].say(response)
        else:
            short = response[:100] + "..."
            self.agents['speaker'].say(short)
        
        return response

# ============================================================
# ЗАПУСК
# ============================================================

def main():
    aura = ParallelAuraOrchestrator()
    
    # Запускаем просыпание в отдельном потоке
    import threading
    def wake_loop():
        while True:
            cmd = aura.agents['wakeword'].execute()
            if cmd:
                print(f"🎯 Голосовая команда: {cmd}")
                # Выполняем команду через process
                aura.process(cmd)
            time.sleep(0.1)
    
    # Запускаем поток для просыпания
    wake_thread = threading.Thread(target=wake_loop, daemon=True)
    wake_thread.start()
    
    print("\n" + "="*60)
    print("🦾 АУРА - ПАРАЛЛЕЛЬНЫЙ мульти-агент")
    print("⚡ Микро-агенты работают одновременно!")
    print("🔴 Аура дремлет... Скажи 'Аура' для активации")
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
