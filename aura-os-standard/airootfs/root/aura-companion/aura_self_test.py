import asyncio
import time
import sys
from aura.bootstrap import build_orchestrator

# Цвета для красивого вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

TESTS = [
    ("Аура, сколько времени", "time"),
    ("Аура, какая сегодня погода", "internet"),
    ("Аура, открой браузер", "app_launcher"),
    ("Аура, найди в интернете новости про Linux", "web_scout"),
    ("Аура, поставь напоминалку через 10 минут", "reminders"),
    ("Аура, сколько будет 235 умножить на 89", "math_solver"),
    ("Аура, как дела", "chat"),
    ("Аура, прочитай файл /etc/shadow", "security"),
    ("Аура, выключи компьютер", "power"),
    ("Аура, запомни что я люблю черный кофе", "rag_memory"),
    ("Аура, кто тебя создал", "captain"),
    ("Аура, какая у меня сейчас задача", "task_manager"),
    ("Аура, покажи мои контакты", "contacts"),
    ("Аура, переведи слово apple", "translate"),
    ("Аура, что мы обсуждали вчера", "journal")
]

async def run_test():
    print(f"{CYAN}=== ЗАПУСК АВТОМАТИЧЕСКОГО ТЕСТА AURAOS ==={RESET}")
    print("Загрузка Orchestrator (это займет пару секунд)...")
    orch = build_orchestrator()
    
    success = 0
    total_time = 0

    for prompt, expected_domain in TESTS:
        print(f"\n{YELLOW}Вопрос:{RESET} {prompt}")
        start = time.time()
        
        try:
            # Отправляем запрос напрямую в мозг (без микрофона)
            response = await orch.process(prompt)
            elapsed = time.time() - start
            total_time += elapsed
            
            # Простая проверка на наличие ответа
            if response and len(str(response)) > 2:
                print(f"{GREEN}✅ OK{RESET} ({elapsed:.2f}с) -> {str(response)[:60]}...")
                success += 1
            else:
                print(f"{RED}❌ FALL{RESET} (пустой ответ)")
                
        except Exception as e:
            print(f"{RED}❌ CRASH{RESET} (Ошибка: {e})")

    print(f"\n{CYAN}=== РЕЗУЛЬТАТ ==={RESET}")
    print(f"Пройдено: {success} из {len(TESTS)}")
    print(f"Среднее время отклика: {total_time/len(TESTS):.2f} сек.")

    if success >= len(TESTS) - 2:
        print(f"{GREEN}🚀 ВСЁ ОТЛИЧНО! Можно показывать другу.{RESET}")
    else:
        print(f"{RED}⚠️ ЕСТЬ ПРОБЛЕМЫ. Надо доработать агентов.{RESET}")

if __name__ == "__main__":
    asyncio.run(run_test())
