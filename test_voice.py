import time
from aura.agents.speaker import AgentSpeaker

print("--- ТЕСТ НЕЙРОГОЛОСА (MMS-TTS) ---")
s = AgentSpeaker()
print("1. Speaker создан. Отправляю текст...")
s.say("Капитан, это проверка нейроголоса MMS-TTS. Один, два, три, четыре, пять.")
print("2. Ждем 30 секунд (загрузка нейросети + генерация)...")

# Ждем 30 секунд, чтобы модель успела загрузиться
time.sleep(30)

print("3. Тест завершен.")
