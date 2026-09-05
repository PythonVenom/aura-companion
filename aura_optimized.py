#!/usr/bin/env python3
import speech_recognition as sr
import subprocess
import requests
import json
from gtts import gTTS
import os
import tempfile
import time
import threading
import queue
import pygame
import torch
import datetime
import re
import glob
import logging

# ===================================================
# НАСТРОЙКИ
# ===================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
CITY = "Moscow"
AUDIO_FILE = "/tmp/aura_command.wav"
MEMORY_FILE = "/home/pythonvenom/aura_project/knowledge/memory.json"
CONVERSATIONS_FILE = "/home/pythonvenom/aura_project/knowledge/conversations.log"
MUSIC_PLAYING = False
MUSIC_PLAYER = None
MUSIC_LIST = []
STOP_SPEAKING = False
SPEAKING_COMPLETE = True
IS_PROCESSING = False

# ===================================================
# ПАМЯТЬ
# ===================================================
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

memory = load_memory()
print(f"🧠 Загружено {len(memory.get('факты', {}))} фактов")

# ===================================================
# ГОЛОС
# ===================================================
def speak_interruptible(text):
    global STOP_SPEAKING, SPEAKING_COMPLETE
    STOP_SPEAKING = False
    SPEAKING_COMPLETE = False
    try:
        pygame.mixer.init()
        tts = gTTS(text, lang="ru", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            pygame.mixer.music.load(f.name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                if STOP_SPEAKING:
                    pygame.mixer.music.stop()
                    break
            os.unlink(f.name)
    except:
        pass
    finally:
        STOP_SPEAKING = False
        SPEAKING_COMPLETE = True

def speak(text):
    try:
        tts = gTTS(text, lang="ru", slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", f.name], check=False)
            os.unlink(f.name)
    except:
        pass

# ===================================================
# КОМАНДЫ (БЫСТРЫЕ, БЕЗ LLM)
# ===================================================
def get_time():
    now = datetime.datetime.now()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"Сейчас {now.strftime('%H:%M')}, {days[now.weekday()]} {now.strftime('%d')} {months[now.month-1]}"

def get_weather():
    try:
        r = requests.get(f"https://wttr.in/{CITY}?format=%t+%w", timeout=5)
        if r.status_code == 200:
            return f"В {CITY} сейчас {r.text.strip()}"
    except:
        pass
    return "Погода неизвестна"

def remember_fact(topic, fact):
    if "факты" not in memory:
        memory["факты"] = {}
    memory["факты"][topic] = fact
    save_memory(memory)
    return f"Запомнила: {topic} — {fact}"

def recall_fact(topic):
    facts = memory.get("факты", {})
    found = [f"{k}: {v}" for k, v in facts.items() if topic.lower() in k.lower()]
    if found:
        return f"Я помню: {', '.join(found[:3])}"
    return "Я не знаю об этом"

def get_stats():
    facts = memory.get("факты", {})
    return f"Я знаю {len(facts)} фактов"

# ===================================================
# МУЗЫКА
# ===================================================
def find_music():
    global MUSIC_LIST
    if MUSIC_LIST:
        return MUSIC_LIST
    music_path = "/home/pythonvenom/Музыка/**/*.mp3"
    files = glob.glob(music_path, recursive=True)
    if files:
        MUSIC_LIST = files
        print(f"🎵 Найдено {len(MUSIC_LIST)} MP3")
        return MUSIC_LIST
    return []

def play_music():
    global MUSIC_PLAYING, MUSIC_PLAYER
    if MUSIC_PLAYING:
        return "Музыка уже играет"
    files = find_music()
    if not files:
        return "MP3 не найдены"
    try:
        import vlc
        MUSIC_PLAYER = vlc.MediaPlayer(files[0])
        MUSIC_PLAYER.play()
        MUSIC_PLAYING = True
        return f"Играет: {os.path.basename(files[0])}"
    except:
        MUSIC_PLAYER = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", files[0]],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        MUSIC_PLAYING = True
        return f"Играет: {os.path.basename(files[0])}"

def stop_music():
    global MUSIC_PLAYING, MUSIC_PLAYER
    if MUSIC_PLAYER:
        if hasattr(MUSIC_PLAYER, 'stop'):
            MUSIC_PLAYER.stop()
        elif hasattr(MUSIC_PLAYER, 'kill'):
            MUSIC_PLAYER.kill()
        MUSIC_PLAYER = None
    MUSIC_PLAYING = False
    return "Музыка остановлена"

# ===================================================
# ПРИЛОЖЕНИЯ
# ===================================================
def open_app(app_name):
    apps = {"браузер": "firefox", "стим": "steam", "терминал": "gnome-terminal", "редактор": "gedit", "файлы": "nautilus"}
    app = apps.get(app_name.lower(), app_name)
    try:
        subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Открываю {app_name}"
    except:
        return f"Не удалось открыть {app_name}"

def execute_command(cmd):
    try:
        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"])
        return f"Выполняю: {cmd}"
    except:
        return f"Ошибка: {cmd}"

def new_workspace():
    try:
        subprocess.run(["wmctrl", "-n", "10"], check=False)
        return "Новый рабочий стол создан"
    except:
        return "Ошибка создания стола"

# ===================================================
# БЫСТРЫЙ ОБРАБОТЧИК (ДЕЛЕГИРОВАНИЕ)
# ===================================================
def handle_command_fast(text):
    text_lower = text.lower()
    
    # СТОП
    if "стоп" in text_lower or "замолчи" in text_lower:
        global STOP_SPEAKING
        STOP_SPEAKING = True
        return "Останавливаюсь"
    
    # Самоуправление
    if "выключись" in text_lower:
        speak("До свидания, Создатель!")
        os._exit(0)
    if "перезагрузись" in text_lower:
        speak("Перезагружаюсь")
        os.execv(sys.executable, ['python'] + sys.argv)
        os._exit(0)
    
    # Время и погода
    if "время" in text_lower or ("сколько" in text_lower and "врем" in text_lower):
        return get_time()
    if "погод" in text_lower:
        return get_weather()
    
    # Музыка
    if "включи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return play_music()
    if "выключи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return stop_music()
    
    # Память
    if "запомни" in text_lower:
        match = re.search(r'запомни\s+(.+?)\s*(?:—|-|:)?\s*(.+)', text)
        if match:
            return remember_fact(match.group(1).strip(), match.group(2).strip())
        return "Скажите: 'запомни [тема] — [факт]'"
    if "вспомни" in text_lower or "что ты знаешь о" in text_lower:
        query = text.replace("вспомни", "").replace("что ты знаешь о", "").strip()
        return recall_fact(query) if query else "Что именно вспомнить?"
    if "сколько фактов" in text_lower or "статистика" in text_lower:
        return get_stats()
    
    # Приложения
    if "открой" in text_lower:
        return open_app(text.replace("открой", "").strip())
    if "выполни" in text_lower:
        return execute_command(text.replace("выполни", "").strip())
    if "новый рабочий" in text_lower:
        return new_workspace()
    
    return None

# ===================================================
# ГЛАВНЫЙ ЦИКЛ С ПРОСЛУШИВАНИЕМ И ПРЕРЫВАНИЕМ
# ===================================================
def main_loop():
    global STOP_SPEAKING, SPEAKING_COMPLETE, IS_PROCESSING
    r = sr.Recognizer()
    model = None
    print("🎤 АУРА Optimized запущена!")
    
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                r.energy_threshold = 650
                r.dynamic_energy_threshold = False
                print("🎤 Слушаю...")
                audio = r.listen(source, timeout=1, phrase_time_limit=2)
                
                if model is None:
                    import whisper
                    model = whisper.load_model("tiny", device="cpu")
                    print("🧠 Модель загружена")
                
                audio_data = audio.get_wav_data()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(audio_data)
                    temp_file = f.name
                
                result = model.transcribe(temp_file, language="ru", fp16=False)
                text = result["text"].strip()
                os.remove(temp_file)
                
                print(f"💤 Слышу: '{text}'")
                
                # ПРЕРЫВАНИЕ: если АУРА говорит — останавливаем
                if not SPEAKING_COMPLETE:
                    STOP_SPEAKING = True
                    time.sleep(0.3)
                    while not SPEAKING_COMPLETE:
                        time.sleep(0.1)
                    print("🛑 Прервано!")
                
                # Проверяем пробуждение
                wake_variants = ["аура", "aura", "ау", "а урав", "аврора", "арав"]
                if any(variant in text.lower() for variant in wake_variants):
                    speak_interruptible("Слушаю!")
                    audio_cmd = r.listen(source, timeout=3, phrase_time_limit=5)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_cmd.get_wav_data())
                        temp_cmd = f.name
                    
                    result_cmd = model.transcribe(temp_cmd, language="ru", fp16=False)
                    command = result_cmd["text"].strip()
                    os.remove(temp_cmd)
                    
                    print(f"📝 Команда: '{command}'")
                    
                    # Быстрая обработка
                    response = handle_command_fast(command)
                    if response:
                        print(f"🌟 {response}")
                        speak_interruptible(response)
                    else:
                        # Сложные вопросы — в LLM
                        try:
                            payload = {"model": MODEL, "prompt": command, "stream": False}
                            r = requests.post(OLLAMA_URL, json=payload, timeout=10)
                            answer = r.json()["response"]
                            print(f"🌟 {answer}")
                            speak_interruptible(answer)
                        except:
                            speak_interruptible("Не поняла команду")
        except sr.WaitTimeoutError:
            continue
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

# ===================================================
# ЗАПУСК
# ===================================================
print("=" * 50)
print("🌟 АУРА Optimized — Быстрая и чёткая")
print("🔊 Скажите 'АУРА' для активации")
print("🛑 'стоп' или 'замолчи' — прервать")
print("📝 'запомни [тема] — [факт]' — запомнить")
print("🎵 'включи музыку' — играть MP3")
print("=" * 50)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n👋 До свидания, Создатель!")
