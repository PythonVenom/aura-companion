import asyncio
import time
from aura_main import AuraOrchestrator

async def main():
    print("--- Инициализация Aura... ---")
    aura = AuraOrchestrator()
    
    print("\n--- ТЕСТ: Barge-in (Перебивание) ---")
    if hasattr(aura, 'barge_in') and aura.barge_in:
        aura.barge_in.ready = True
        aura.barge_in.start(on_speech=aura._on_barge_in)
        print("VAD (Barge-in) запущен. Говорю длинный текст...")
        
        # Запускаем речь
        aura._say_with_duck("Капитан, это длинная проверка Barge-in. Один, два, три, четыре, пять, шесть, семь, восемь, девять, десять.")
        
        print("--- Речь завершена. ---")
        aura.barge_in.stop()
    else:
        print("Barge-in не инициализирован.")
        
    print("--- Ждем завершения фоновых процессов (1 сек)... ---")
    await asyncio.sleep(1.0)
    print("--- Тест успешно завершен ---")

asyncio.run(main())
