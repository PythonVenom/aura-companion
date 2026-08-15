import logging
logging.basicConfig(filename="/home/pythonvenom/aura_project/logs/aura.log", level=logging.INFO, format="%(asctime)s - %(message)s")

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

# ===================================================
# НАСТРОЙКИ
# ===================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:7b"
CITY = "Moscow"
AUDIO_FILE = "/tmp/aura_command.wav"
WAKE_WORD = "аура"
IS_PROCESSING = False
COMMAND_QUEUE = queue.Queue()
MEMORY_FILE = "/home/pythonvenom/aura_memory.json"
MUSIC_PLAYING = False
MUSIC_PLAYER = None
MUSIC_LIST = []

print(f"🔍 CUDA доступна: {torch.cuda.is_available()}")
start_time = time.time()

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
print(f"🧠 Загружено {len(memory)} фактов")

# ===================================================
# МУЗЫКА
# ===================================================
def find_music():
    global MUSIC_LIST
    if MUSIC_LIST:
        return MUSIC_LIST
    paths = ["/home/pythonvenom/**/*.mp3", "/media/**/*.mp3", "/mnt/**/*.mp3"]
    for path in paths:
        files = glob.glob(path, recursive=True)
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
        return "Ошибка воспроизведения"

def stop_music():
    global MUSIC_PLAYING, MUSIC_PLAYER
    if MUSIC_PLAYER:
        MUSIC_PLAYER.stop()
        MUSIC_PLAYER = None
    MUSIC_PLAYING = False
    return "Музыка остановлена"

# ===================================================
# ОСТАЛЬНЫЕ ФУНКЦИИ
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

def open_app(app_name):
    apps = {
        "браузер": "firefox",
        "стим": "steam",
        "терминал": "gnome-terminal",
        "редактор": "gedit",
        "файлы": "nautilus"
    }
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
# ОБРАБОТКА КОМАНД
# ===================================================
def handle_command(text):
    global memory, MUSIC_PLAYING
    text_lower = text.lower()
    
    if "выключись" in text_lower:
        speak("До свидания, Создатель!")
        os._exit(0)
    
    if "перезагрузись" in text_lower:
        speak("Перезагружаюсь")
        os.execv(sys.executable, ['python'] + sys.argv)
        os._exit(0)
    
    if "время" in text_lower or ("сколько" in text_lower and "врем" in text_lower):
        return get_time()
    
    if "погод" in text_lower:
        return get_weather()
    
    if "включи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return play_music()
    if "выключи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return stop_music()
    
    if "открой" in text_lower:
        app = text.replace("открой", "").strip()
        return open_app(app)
    
    if "выполни" in text_lower:
        cmd = text.replace("выполни", "").strip()
        return execute_command(cmd)
    
    if "новый рабочий" in text_lower:
        return new_workspace()
    
    if "запомни" in text_lower:
        match = re.search(r'запомни\s+(.+?)\s*(?:—|-|:)?\s*(.+)', text)
        if match:
            topic, fact = match.group(1).strip(), match.group(2).strip()
            memory[topic] = fact
            save_memory(memory)
            return f"Запомнила: {topic} — {fact}"
        return "Скажите: 'запомни [тема] — [факт]'"
    
    if "вспомни" in text_lower:
        query = text.replace("вспомни", "").strip()
        if not query:
            return "Что именно вспомнить?"
        found = [f"{k}: {v}" for k, v in memory.items() if query.lower() in k.lower()]
        if found:
            return f"Я помню: {', '.join(found[:3])}"
        return "Я не знаю об этом"
    
    return None

# ===================================================
# ПРОСТОЙ И НАДЁЖНЫЙ ЦИКЛ
# ===================================================
def main_loop():
    r = sr.Recognizer()
    model = None
    print("🎤 Слушаю... скажите 'АУРА'")
    
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                r.energy_threshold = 400
                print("🎤 Жду команду...")
                audio = r.listen(source, timeout=2, phrase_time_limit=3)
                
                # Загружаем модель только когда есть звук
                if model is None:
                    import whisper
                    model = whisper.load_model("tiny", device="cpu")
                    print("🧠 Модель загружена")
                
                # Распознаём
                audio_data = audio.get_wav_data()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(audio_data)
                    temp_file = f.name
                
                result = model.transcribe(temp_file, language="ru", fp16=False)
                text = result["text"].strip()
                os.remove(temp_file)
                
                print(f"💤 Слышу: '{text}'")
                
                if WAKE_WORD in text.lower():
                    speak("Слушаю, Создатель!")
                    # Слушаем команду
                    audio_cmd = r.listen(source, timeout=4, phrase_time_limit=6)
                    audio_data_cmd = audio_cmd.get_wav_data()
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                        f.write(audio_data_cmd)
                        temp_file_cmd = f.name
                    
                    result_cmd = model.transcribe(temp_file_cmd, language="ru", fp16=False)
                    command_text = result_cmd["text"].strip()
                    os.remove(temp_file_cmd)
                    
                    print(f"📝 Команда: '{command_text}'")
                    response = handle_command(command_text)
                    if response:
                        print(f"🌟 {response}")
                        speak(response)
                    else:
                        speak("Не поняла команду")
        except sr.WaitTimeoutError:
            continue
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

# ===================================================
# ЗАПУСК
# ===================================================
print("🌟 АУРА v3 запущена!")
print("=" * 50)
print("🔊 Скажите 'АУРА' для активации")
print("📱 'открой браузер' — запустить Firefox")
print("🕐 'сколько времени' — время")
print("🎵 'включи музыку' — играть MP3")
print("💻 'выполни neofetch' — команда в терминале")
print("=" * 50)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n👋 До свидания, Создатель!")
