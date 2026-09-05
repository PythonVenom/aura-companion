#!/usr/bin/env python3
import threading
import time
import queue

# Импортируем агенты
from agents.listener import TEXT_QUEUE
from agents.speaker import SPEECH_QUEUE, speaker_loop

# Очереди для общения между агентами
TEXT_QUEUE = queue.Queue()
SPEECH_QUEUE = queue.Queue()

def main():
    print("🌟 СИСТЕМА АУРА запущена!")
    print("=" * 50)
    print("Агенты:")
    print("  🎤 СЛУХ — распознаёт речь")
    print("  🧠 МАРШРУТИЗАТОР — анализирует")
    print("  🔊 ГОЛОС — говорит")
    print("=" * 50)
    
    # Запускаем агентов в отдельных потоках
    from agents.listener import listen
    from agents.router import router
    from agents.speaker import speaker_loop
    
    listener_thread = threading.Thread(target=listen, daemon=True)
    router_thread = threading.Thread(target=router, daemon=True)
    speaker_thread = threading.Thread(target=speaker_loop, daemon=True)
    
    listener_thread.start()
    router_thread.start()
    speaker_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Система АУРА остановлена")

if __name__ == "__main__":
    main()
