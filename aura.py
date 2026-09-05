#!/usr/bin/env python3
# ===================================================
# АУРА — ГОЛОСОВОЙ АССИСТЕНТ (faster-whisper)
# ===================================================

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
import numpy as np
import pyaudio
from faster_whisper import WhisperModel

# ===================================================
# 1. НАСТРОЙКИ
# ===================================================
LOG_FILE = "/home/pythonvenom/aura_project/logs/aura.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

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

def log_msg(msg):
    print(msg)
    logging.info(msg)

# ===================================================
# 2. ПАМЯТЬ
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
log_msg(f"🧠 Загружено {len(memory.get('факты', {}))} фактов")

# ===================================================
# 3. ГОЛОС
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
                time.sleep(0.05)
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
# 4. УПРАВЛЕНИЕ БРАУЗЕРОМ
# ===================================================
def browser_open():
    subprocess.Popen(["firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    return "Открываю браузер"

def browser_focus():
    try:
        subprocess.run(["xdotool", "search", "--class", "firefox", "windowactivate"], check=False)
        time.sleep(0.3)
        return True
    except:
        return False

def browser_search(query):
    if not browser_focus():
        return "Браузер не найден"
    time.sleep(0.3)
    subprocess.run(["xdotool", "key", "ctrl+l"], check=False)
    time.sleep(0.2)
    subprocess.run(["xdotool", "type", query], check=False)
    time.sleep(0.2)
    subprocess.run(["xdotool", "key", "Return"], check=False)
    return f"Ищу: {query}"

def browser_go_to(url):
    return browser_search(url)

def browser_next_tab():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "ctrl+Page_Down"], check=False)
    return "Следующая вкладка"

def browser_prev_tab():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "ctrl+Page_Up"], check=False)
    return "Предыдущая вкладка"

def browser_close_tab():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "ctrl+w"], check=False)
    return "Закрываю вкладку"

def browser_new_tab():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "ctrl+t"], check=False)
    return "Новая вкладка"

def browser_fullscreen():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "F11"], check=False)
    return "Полноэкранный режим"

def browser_exit_fullscreen():
    if not browser_focus():
        return "Браузер не найден"
    subprocess.run(["xdotool", "key", "F11"], check=False)
    return "Выход из полноэкранного режима"

def browser_close():
    subprocess.run(["pkill", "firefox"], check=False)
    return "Закрываю браузер"

# ===================================================
# 5. ВРЕМЯ И ПОГОДА
# ===================================================
def get_time_with_geo():
    now = datetime.datetime.now()
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    tz = datetime.datetime.now().astimezone().tzinfo
    return f"Сейчас {now.strftime('%H:%M')}, {days[now.weekday()]} {now.strftime('%d')} {months[now.month-1]} {now.strftime('%Y')} года. Часовой пояс: {tz}"

def get_weather():
    try:
        rq = requests.get(f"https://wttr.in/{CITY}?format=%t+%w", timeout=5)
        if rq.status_code == 200:
            return f"В {CITY} сейчас {rq.text.strip()}"
    except:
        pass
    return "Погода неизвестна"

# ===================================================
# 6. МУЗЫКА
# ===================================================
def find_music():
    global MUSIC_LIST
    if MUSIC_LIST:
        return MUSIC_LIST
    music_path = "/home/pythonvenom/Музыка/**/*.mp3"
    files = glob.glob(music_path, recursive=True)
    if files:
        MUSIC_LIST = files
        log_msg(f"🎵 Найдено {len(MUSIC_LIST)} MP3")
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
# 7. ПРИЛОЖЕНИЯ
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
# 8. РАСПОЗНАВАНИЕ (faster-whisper)
# ===================================================
def transcribe_audio(audio_data):
    global model
    audio_float = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    segments, info = model.transcribe(audio_float, language='ru')
    text = ''.join([segment.text for segment in segments])
    return text.strip()

# ===================================================
# 9. ОБРАБОТЧИК КОМАНД
# ===================================================
def handle_command(text):
    global STOP_SPEAKING
    text_lower = text.lower()
    
    if "стоп" in text_lower or "замолчи" in text_lower:
        STOP_SPEAKING = True
        return "Останавливаюсь"
    
    if "выключись" in text_lower:
        speak("До свидания, Создатель!")
        os._exit(0)
    if "перезагрузись" in text_lower:
        speak("Перезагружаюсь")
        os.execv(sys.executable, ['python'] + sys.argv)
        os._exit(0)
    
    # БРАУЗЕР
    if "открой браузер" in text_lower or "запусти браузер" in text_lower:
        return browser_open()
    if "закрой браузер" in text_lower:
        return browser_close()
    if "найди" in text_lower or "поиск" in text_lower:
        query = text.replace("найди", "").replace("поиск", "").strip()
        return browser_search(query) if query else "Что искать?"
    if "открой сайт" in text_lower or "перейди на" in text_lower:
        url = text.replace("открой сайт", "").replace("перейди на", "").strip()
        return browser_go_to(url) if url else "Какой сайт?"
    if "следующая вкладка" in text_lower:
        return browser_next_tab()
    if "предыдущая вкладка" in text_lower:
        return browser_prev_tab()
    if "закрой вкладку" in text_lower:
        return browser_close_tab()
    if "новая вкладка" in text_lower:
        return browser_new_tab()
    if "на весь экран" in text_lower or "разверни" in text_lower:
        return browser_fullscreen()
    if "сверни с экрана" in text_lower or "выйти из полного" in text_lower:
        return browser_exit_fullscreen()
    
    # ВРЕМЯ И ПОГОДА
    if "время" in text_lower or ("сколько" in text_lower and "врем" in text_lower):
        return get_time_with_geo()
    if "погод" in text_lower:
        return get_weather()
    
    # МУЗЫКА
    if "включи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return play_music()
    if "выключи" in text_lower and ("музык" in text_lower or "песн" in text_lower):
        return stop_music()
    
    # ПАМЯТЬ
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
    
    # ПРИЛОЖЕНИЯ
    if "открой" in text_lower:
        return open_app(text.replace("открой", "").strip())
    if "выполни" in text_lower:
        return execute_command(text.replace("выполни", "").strip())
    if "новый рабочий" in text_lower:
        return new_workspace()
    
    return None

# ===================================================
# 10. ГЛАВНЫЙ ЦИКЛ
# ===================================================
def main_loop():
    global STOP_SPEAKING, SPEAKING_COMPLETE, IS_PROCESSING, model
    
    # Загружаем модель faster-whisper
    log_msg("🧠 Загрузка faster-whisper...")
    model = WhisperModel('medium', device='cuda', compute_type='float32')
    log_msg("🧠 Модель загружена")
    
    r = sr.Recognizer()
    log_msg("🌟 АУРА ФИНАЛ запущена!")
    
    while True:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                r.energy_threshold = 300
                r.dynamic_energy_threshold = True
                log_msg("🎤 Слушаю...")
                audio = r.listen(source, timeout=1, phrase_time_limit=4)
                
                audio_data = audio.get_wav_data()
                text = transcribe_audio(audio_data)
                
                if text:
                    log_msg(f"🎤 Распознано: '{text}'")
                    
                    if not SPEAKING_COMPLETE:
                        STOP_SPEAKING = True
                        time.sleep(0.2)
                        while not SPEAKING_COMPLETE:
                            time.sleep(0.05)
                        log_msg("🛑 Прервано!")
                    
                    response = handle_command(text)
                    if response:
                        log_msg(f"🌟 {response}")
                        speak_interruptible(response)
                    else:
                        try:
                            payload = {"model": MODEL, "prompt": text, "stream": False}
                            rq = requests.post(OLLAMA_URL, json=payload, timeout=10)
                            answer = rq.json()["response"]
                            log_msg(f"🌟 {answer}")
                            speak_interruptible(answer)
                        except Exception as e:
                            log_msg(f"⚠️ Ошибка LLM: {e}")
                            speak_interruptible("Не поняла команду")
        except sr.WaitTimeoutError:
            continue
        except Exception as e:
            log_msg(f"⚠️ Ошибка: {e}")
            continue

# ===================================================
# 11. ЗАПУСК
# ===================================================
log_msg("=" * 50)
log_msg("🌟 АУРА с faster-whisper")
log_msg("🌐 Управление браузером")
log_msg("🎵 Музыка")
log_msg("🧠 Память")
log_msg("🕐 Время и погода")
log_msg("=" * 50)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log_msg("\n👋 До свидания, Создатель!")
