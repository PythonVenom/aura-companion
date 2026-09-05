#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# Путь к jarvis для отправки сообщений
JARVIS_SEND = "jarvis --send"

def check_updates():
    try:
        result = subprocess.run(["/home/pythonvenom/.openjarvis/check_updates.sh"], 
                                capture_output=True, text=True)
        count = result.stdout.strip()
        if count and int(count) > 0:
            return f"⚠️ Доступно {count} обновлений для системы. Обновить?"
        return None
    except:
        return None

def send_notification(msg):
    # Записываем сообщение в файл, который будет читать jarvis
    with open("/tmp/jarvis_notify.txt", "w") as f:
        f.write(msg)

if __name__ == "__main__":
    while True:
        msg = check_updates()
        if msg:
            send_notification(msg)
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")
        time.sleep(7200)  # Проверка каждые 2 часа
