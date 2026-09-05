#!/usr/bin/env python3
"""
Аура - Ядро (мозг)
Управляет микро-агентами, включает их только когда нужно
"""

import subprocess
import re
import time
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Подавляем предупреждения
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
# БАЗОВЫЙ КЛАСС МИКРО-АГЕНТА
# ============================================================

class MicroAgent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.active = False
    
    def activate(self):
        self.active = True
        print(f"🔧 {self.name} активирован")
    
    def deactivate(self):
        self.active = False
        print(f"🔧 {self.name} деактивирован")
    
    def execute(self, input_data):
        raise NotImplementedError

# ============================================================
# МАШИНКА 1: СЛУХ
# ============================================================

class AgentListener(MicroAgent):
    def __init__(self):
        super().__init__("listener", "Слух Ауры")
        try:
            import vosk
            import sounddevice as sd
            import numpy as np
            self.sd = sd
            self.np = np
            self.model = vosk.Model(os.path.expanduser("~/aura_project/vosk_model"))
            self.ready = True
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            self.ready = False

    def listen(self, timeout=3):
        if not self.ready or not self.active:
            return None
        try:
            import vosk
            import json
            
            fs = 16000
            duration = timeout
            recording = self.sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            self.sd.wait()
            
            audio_data = recording.tobytes()
            
            rec = vosk.KaldiRecognizer(self.model, fs)
            rec.AcceptWaveform(audio_data)
            
            result = json.loads(rec.FinalResult())
            text = result.get('text', '').strip().lower()
            
            if text and len(text) > 2:
                return text
            return None
        except Exception as e:
            return None

    def execute(self, command):
        return self.listen()

# ============================================================
# МАШИНКА 2: ГОЛОС
# ============================================================

class AgentSpeaker(MicroAgent):
    def __init__(self):
        super().__init__("speaker", "Голос Ауры")
        self.voice_path = os.path.expanduser("~/aura_project/voices/ru_RU-irina-medium.onnx")
        self.piper_cmd = os.path.expanduser("~/.local/bin/piper")
    
    def say(self, text):
        if not self.active:
            return "🔇 Голос выключен"
        try:
            import tempfile
            if os.path.exists(self.piper_cmd):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(text)
                    text_file = f.name
                subprocess.run([self.piper_cmd, '-m', self.voice_path, '-i', text_file, '-f', '/tmp/aura_speech.wav'], capture_output=True)
                subprocess.Popen(['aplay', '/tmp/aura_speech.wav'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(text_file)
            else:
                subprocess.Popen(['espeak-ng', '-v', 'ru', '-p', '60', '-s', '160', text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"🗣️ Сказала: {text[:50]}..."
        except:
            return "❌ Ошибка озвучивания"
    
    def execute(self, command):
        return self.say(command)

# ============================================================
# МАШИНКА 3: ВРЕМЯ
# ============================================================

class AgentTimeGetter(MicroAgent):
    def __init__(self):
        super().__init__("time", "Показывает время")
    
    def execute(self, _):
        now = datetime.now()
        hours = now.strftime("%H").lstrip('0') or '0'
        minutes = now.strftime("%M")
        return f"{hours} часов {minutes} минут, Создатель"

# ============================================================
# МАШИНКА 4: ОБНОВЛЕНИЯ
# ============================================================

class AgentUpdateChecker(MicroAgent):
    def __init__(self):
        super().__init__("updates", "Проверяет обновления")
    
    def execute(self, _):
        try:
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            if count and int(count) > 0:
                return f"⚠️ Доступно {count} обновлений"
            return "✅ Система обновлена"
        except:
            return "❌ Не удалось проверить обновления"

class AgentUpgrader(MicroAgent):
    def __init__(self):
        super().__init__("upgrader", "Устанавливает обновления")
        self.waiting_for_confirmation = False
        self.confirmation_attempts = 0  # Счетчик попыток
    
    def execute(self, _):
        try:
            lock = '/var/lib/pacman/db.lck'
            if os.path.exists(lock):
                try: os.remove(lock)
                except: pass
            
            # Проверяем обновления
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            if not count or int(count) == 0:
                return "✅ Обновлений нет"
            
            speaker = self._get_speaker()
            if speaker:
                speaker.say(f"Доступно {count} обновлений. Для подтверждения скажи: да аура обнови")
            
            # Ставим флаг, что мы ждем ответа
            self.waiting_for_confirmation = True
            self.confirmation_attempts = 0  # Сбрасываем счетчик
            return "⚠️ Ожидание подтверждения..."
            
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def confirm(self):
        """Вызывается из ядра, если пользователь сказал 'да'"""
        try:
            lock = '/var/lib/pacman/db.lck'
            if os.path.exists(lock):
                try: os.remove(lock)
                except: pass
            
            speaker = self._get_speaker()
            if speaker:
                speaker.say("✅ Подтверждено. Начинаю обновление...")
            
            result = subprocess.run("sudo pacman -Syu --noconfirm", shell=True, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                return "✅ Система обновлена!"
            else:
                return f"❌ Ошибка: {result.stderr}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    def increment_attempts(self):
        """Увеличиваем счетчик попыток. Если больше 3 - выходим"""
        self.confirmation_attempts += 1
        if self.confirmation_attempts > 3:
            self.waiting_for_confirmation = False
            return True  # Нужно отменить
        return False
    
    def _get_speaker(self):
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('speaker')
        return None

# ============================================================
# МИКРО-АГЕНТ: АВТО-ОПОВЕЩЕНИЕ ОБ ОБНОВЛЕНИЯХ
# ============================================================

class AgentUpdateNotifier(MicroAgent):
    """Проверяет обновления, оповещает голосом и ждёт подтверждения"""
    
    def __init__(self):
        super().__init__("update_notifier", "Авто-оповещение об обновлениях")
        self.last_count = 0
        self.interval = 7200  # 2 часа
    
    def check(self):
        """Проверяет наличие обновлений"""
        try:
            result = subprocess.run("checkupdates 2>/dev/null | wc -l", 
                                   shell=True, capture_output=True, text=True)
            count = result.stdout.strip()
            return int(count) if count else 0
        except:
            return 0
    
    def notify(self):
        """Оповещает голосом и ждёт ответа"""
        count = self.check()
        if count == 0:
            return "✅ Обновлений нет"
        
        if count == self.last_count:
            return "ℹ️ Обновлений не прибавилось"
        
        self.last_count = count
        msg = f"Создатель, доступно {count} обновлений. Обновить?"
        
        # Говорим через Ауру (голос Ирины)
        speaker = self._get_speaker()
        if speaker:
            speaker.say(msg)
        
        # Ждём ответ "да" или "нет"
        listener = self._get_listener()
        if listener:
            answer = listener.listen(timeout=5)
            if answer and ('да' in answer or 'yes' in answer):
                return self._upgrade()
            elif answer and ('нет' in answer or 'no' in answer):
                return "⏹️ Обновление отменено."
            else:
                return "⏱️ Время вышло. Обновление отменено."
        
        return "⚠️ Аура не готова слушать"
    
    def _get_speaker(self):
        """Находит агента Speaker в глобальном оркестраторе"""
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('speaker')
        return None
    
    def _get_listener(self):
        """Находит агента Listener в глобальном оркестраторе"""
        import __main__
        aura = getattr(__main__, 'aura', None)
        if aura and hasattr(aura, 'agents'):
            return aura.agents.get('listener')
        return None
    
    def _upgrade(self):
        """Выполняет обновление"""
        try:
            lock = '/var/lib/pacman/db.lck'
            if os.path.exists(lock):
                try: os.remove(lock)
                except: pass
            
            result = subprocess.run("sudo pacman -Syu --noconfirm", 
                                   shell=True, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                return "✅ Система обновлена!"
            else:
                return f"❌ Ошибка: {result.stderr}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def execute(self, command=None):
        """Основной метод — вызывается из ядра"""
        return self.notify()

# ============================================================
# МАШИНКА 5: ИНТЕРНЕТ
# ============================================================

class AgentInternet(MicroAgent):
    def __init__(self):
        super().__init__("internet", "Поиск в интернете")
        try:
            from ddgs import DDGS
            self.ddgs = DDGS()
            self.ready = True
        except:
            self.ready = False
    
    def search(self, query):
        if not self.ready:
            return "❌ Модуль поиска не установлен"
        try:
            results = []
            for r in self.ddgs.text(query, max_results=3):
                results.append(r)
            if not results:
                return f"❌ Ничего не найдено по '{query}'"
            answer = f"🔍 Результаты по '{query}':\n"
            for i, r in enumerate(results, 1):
                answer += f"{i}. {r.get('title', '')}\n   {r.get('body', '')[:150]}...\n"
            return answer
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"
    
    def execute(self, command):
        query = command.replace('найди', '').replace('поиск', '').replace('сколько времени в', '').replace('погода в', '').strip()
        if not query:
            return "Что искать?"
        return self.search(query)

# ============================================================
# МАШИНКА 6: ЗРЕНИЕ
# ============================================================

class AgentVision(MicroAgent):
    def __init__(self):
        super().__init__("vision", "Зрение Ауры")
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.ready = True
        except:
            self.ready = False
    
    def screenshot(self):
        if not self.ready:
            return "❌ Зрение недоступно"
        try:
            path = os.path.expanduser("~/aura_project/screenshot.png")
            self.pyautogui.screenshot().save(path)
            return f"📸 Скриншот: {path}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
    
    def execute(self, command):
        if 'скриншот' in command:
            return self.screenshot()
        return "👁️ Я вижу экран"

# ============================================================
# МАШИНКА 7: ОТКРЫТИЕ ПРИЛОЖЕНИЙ
# ============================================================

class AgentSystemControl(MicroAgent):
    def __init__(self):
        super().__init__("system", "Управляет ПК")
    
    def execute(self, command):
        apps = {'браузер': 'firefox', 'терминал': 'gnome-terminal', 'код': 'code-oss'}
        for name, cmd in apps.items():
            if name in command:
                subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"{name}"
        return "❌ Не поняла"

# ============================================================
# МАШИНКА 7.5: СПИСОК ФУНКЦИЙ
# ============================================================

class AgentFunctions(MicroAgent):
    def __init__(self):
        super().__init__("functions", "Список функций")
    
    def execute(self, _):
        return ("Доступные функции:\n"
                "1. Время — скажи 'сколько времени'\n"
                "2. Обновления — скажи 'проверь обновления'\n"
                "3. Обновить систему — скажи 'обнови систему'\n"
                "4. Поиск в интернете — скажи 'найди [запрос]'\n"
                "5. Открыть приложение — скажи 'открой браузер'\n"
                "6. Скриншот — скажи 'сделай скриншот'\n"
                "7. Память и контекст — скажи 'покажи память' или 'анализ'")

# ============================================================
# МАШИНКА 8: РЕЕСТР ПАМЯТИ
# ============================================================

class AgentMemoryRegistry(MicroAgent):
    """Реестр памяти: диалоги, действия, система, буфер обмена"""
    
    def __init__(self):
        super().__init__("registry", "Реестр памяти")
        self.memory_file = os.path.expanduser("~/aura_project/memory_registry.json")
        self.session_data = self._load_or_create()
        self.last_event = None
        self.is_initialized = True
    
    def _load_or_create(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._new_session()
        return self._new_session()
    
    def _new_session(self):
        return {
            "session_id": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "start_time": datetime.now().isoformat(),
            "events": [],
            "summary": {
                "total_commands": 0,
                "most_used": {},
                "patterns": []
            }
        }
    
    def log(self, event_type, data):
        """Логирует событие (диалог, действие, система)"""
        event = {
            "time": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.session_data["events"].append(event)
        self._save()
        
        # Обновляем статистику
        if event_type == "command":
            self.session_data["summary"]["total_commands"] += 1
            cmd = data.get("command", "")
            if cmd:
                self.session_data["summary"]["most_used"][cmd] = self.session_data["summary"]["most_used"].get(cmd, 0) + 1
    
    def get_last(self, count=10):
        """Возвращает последние N событий"""
        return self.session_data["events"][-count:]
    
    def get_context(self):
        """Возвращает контекст для анализа"""
        last_events = self.get_last(20)
        context = {
            "last_command": None,
            "last_dialog": None,
            "last_action": None,
            "recent_commands": []
        }
        for e in last_events:
            if e["type"] == "command":
                context["last_command"] = e["data"].get("command")
                context["recent_commands"].append(e["data"].get("command"))
            elif e["type"] == "dialog":
                context["last_dialog"] = e["data"]
            elif e["type"] == "action":
                context["last_action"] = e["data"].get("action")
        return context
    
    def _save(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
    
    def execute(self, command):
        if "покажи память" in command:
            return json.dumps(self.get_context(), ensure_ascii=False, indent=2)[:500]
        return "📝 Реестр памяти работает"

# ============================================================
# МАШИНКА 9: КОНТЕКСТ И АНАЛИЗ
# ============================================================

class AgentContext(MicroAgent):
    """Анализирует контекст, находит паттерны, предугадывает действия"""
    
    def __init__(self):
        super().__init__("context", "Контекст и анализ")
        self.registry = None
    
    def _get_registry(self):
        if not self.registry:
            import __main__
            aura = getattr(__main__, 'aura', None)
            if aura and hasattr(aura, 'agents'):
                self.registry = aura.agents.get('registry')
        return self.registry
    
    def analyze(self):
        """Анализирует последние события и выявляет паттерны"""
        registry = self._get_registry()
        if not registry:
            return "⚠️ Реестр не найден"
        
        context = registry.get_context()
        commands = context.get("recent_commands", [])
        
        if len(commands) < 3:
            return "👀 Недостаточно данных для анализа"
        
        # Находим паттерны
        patterns = []
        if "браузер" in str(commands[-3:]) and "музык" in str(commands[-3:]):
            patterns.append("🔍 Паттерн: после браузера → музыка")
        if "врем" in str(commands[-3:]) and "врем" in str(commands[-5:]):
            patterns.append("🔄 Паттерн: частый запрос времени")
        
        if patterns:
            return "\n".join(patterns)
        return "📊 Паттернов не обнаружено"
    
    def execute(self, command):
        if "анализ" in command or "паттерн" in command:
            return self.analyze()
        return "🧠 Контекст: анализирую поведение"

# ============================================================
# ЯДРО (ОРКЕСТРАТОР)
# ============================================================

class AuraCore:
    def __init__(self):
        self.agents = {
            'listener': AgentListener(),
            'speaker': AgentSpeaker(),
            'time': AgentTimeGetter(),
            'updates': AgentUpdateChecker(),
            'upgrader': AgentUpgrader(),
            'internet': AgentInternet(),
            'vision': AgentVision(),
            'system': AgentSystemControl(),
            'functions': AgentFunctions(),
            'update_notifier': AgentUpdateNotifier(),
            'registry': AgentMemoryRegistry(),
            'context': AgentContext(),
        }
        self.running = True
        self.listening = False
        self.last_context_text = None
        self.last_context_response = None
        self.last_notification_time = time.time()
    
    def remember_context(self, text, response):
        self.last_context_text = text
        self.last_context_response = response

    def process(self, text):
        text_lower = text.lower()
        
        # Логируем команду
        if 'registry' in self.agents:
            self.agents['registry'].log("command", {"command": text})

        # Проверка на контекст (Повтори / Что я просил?)
        if ('что я просил' in text_lower or 'повтори' in text_lower):
            if self.last_context_response:
                return f"Ты просил: '{self.last_context_text}'. Я ответила: {self.last_context_response}"
            else:
                return "Я пока не помню, что ты просил."
        
        # Естественные вопросы
        if any(word in text_lower for word in ['время', 'врем', 'час', 'который час', 'сколько времени']):
            response = self.agents['time'].execute(None)
            self.remember_context(text, response)
            return response
        elif 'обновл' in text_lower:
            response = self.agents['updates'].execute(None)
            self.remember_context(text, response)
            return response
        elif 'обнови' in text_lower:
            response = self.agents['upgrader'].execute(None)
            self.remember_context(text, response)
            return response
        elif 'скриншот' in text_lower:
            response = self.agents['vision'].execute(text_lower)
            self.remember_context(text, response)
            return response
        elif 'найди' in text_lower or 'поиск' in text_lower:
            response = self.agents['internet'].execute(text_lower)
            self.remember_context(text, response)
            return response
        elif 'открой' in text_lower:
            response = self.agents['system'].execute(text_lower)
            self.remember_context(text, response)
            return response
        elif 'память' in text_lower or 'контекст' in text_lower:
            response = self.agents['registry'].execute(text_lower)
            self.remember_context(text, response)
            return response
        elif 'анализ' in text_lower or 'паттерн' in text_lower:
            response = self.agents['context'].execute(text_lower)
            self.remember_context(text, response)
            return response
        elif 'функци' in text_lower or 'возможност' in text_lower or 'умеешь' in text_lower:
            response = self.agents['functions'].execute(None)
            self.remember_context(text, response)
            return response
        else:
            return "Не расслышала, создатель, повторите"
    
    def run(self):
        print("\n" + "="*60)
        print("🦾 АУРА - ЯДРО (Мозг)")
        print("🔴 Скажи 'Аура' для активации")
        print("="*60)
        print("Введите 'exit' для выхода\n")
        
        self.agents['listener'].active = True
        self.agents['functions'] = AgentFunctions()
        
        while self.running:
            try:
                heard = self.agents['listener'].listen(timeout=3)

                # Авто-уведомление (раз в 5 минут)
                if time.time() - self.last_notification_time > 300:
                    self.agents['speaker'].active = True
                    res = self.agents['update_notifier'].execute()
                    if '⚠️' in res:
                        print(f"🤖 Уведомление: {res}")
                        self.agents['speaker'].say(res)
                    self.last_notification_time = time.time()
                    self.agents['speaker'].active = False
                
                if heard and ('аура' in heard or 'aura' in heard):
                    print("🔔 Активация!")
                    cmd = heard.replace('аура', '').replace('aura', '').strip()
                    
                    # ПРОВЕРКА: Ждем подтверждения обновления
                    if self.agents['upgrader'].waiting_for_confirmation:
                        if 'да' in cmd:
                            self.agents['upgrader'].waiting_for_confirmation = False
                            response = self.agents['upgrader'].confirm()
                            print(f"🤖 {response}")
                            self.agents['speaker'].say(response)
                        elif 'нет' in cmd or 'отмена' in cmd:
                            self.agents['upgrader'].waiting_for_confirmation = False
                            response = "⏹️ Обновление отменено."
                            print(f"🤖 {response}")
                            self.agents['speaker'].say(response)
                        else:
                            # Если 3 раза не поняла - выходим из режима ожидания
                            if self.agents['upgrader'].increment_attempts():
                                self.agents['upgrader'].waiting_for_confirmation = False
                                response = "⏱️ Время вышло. Обновление отменено."
                                print(f"🤖 {response}")
                                self.agents['speaker'].say(response)
                            else:
                                response = "Повторите: скажите 'да' или 'нет'."
                                print(f"🤖 {response}")
                                self.agents['speaker'].say(response)
                        continue # Возвращаемся в начало цикла, чтобы снова слушать

                    if cmd:
                        print(f"📝 Команда: {cmd}")
                        self.agents['speaker'].active = True
                        response = self.process(cmd)
                        print(f"🤖 {response}")
                        self.agents['speaker'].say(response)
                    else:
                        cmd2 = self.agents['listener'].listen(timeout=4)
                        if cmd2:
                            print(f"📝 Команда: {cmd2}")
                            self.agents['speaker'].active = True
                            response = self.process(cmd2)
                            print(f"🤖 {response}")
                            self.agents['speaker'].say(response)
                        else:
                            print("⏳ Не расслышала команду")
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n🦾 Аура: До свидания! 👋")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(0.5)

# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    core = AuraCore()
    core.run()