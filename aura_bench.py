import asyncio
import time
from aura.bootstrap import build_orchestrator

TASKS = [
    "Сколько сейчас времени?",
    "Прочитай файл README.md и скажи, что там в первом абзаце",
    "Сколько пользователей в таблице users в базе test.db?",
    "Создай файл bench_test.txt и запиши туда 'Benchmark OK'",
    "Найди в интернете последние новости про искусственный интеллект"
]

async def main():
    print("========================================")
    print("🧪 ЗАПУСК AURABENCH (5 ЗАДАЧ)")
    print("========================================\n")
    
    orch = build_orchestrator()
    if orch.mcp_manager:
        await orch.mcp_manager.load_all()

    success_count = 0
    total_time = 0.0

    for i, task in enumerate(TASKS, 1):
        print(f"\n--- Задача {i}/5: {task} ---")
        start_time = time.time()
        
        try:
            # Для задач с записью файлов (HITL) автоматически подтверждаем
            res = await orch.process(task)
            if "требуется подтверждение" in str(res):
                print("⚠️ HITL: Автоматическое подтверждение для теста...")
                res = await orch.process("Подтверждаю")
                
            elapsed = time.time() - start_time
            total_time += elapsed
            
            if "❌" not in str(res) and "Ошибка" not in str(res):
                success_count += 1
                print(f"✅ УСПЕХ ({elapsed:.2f} сек): {str(res)[:100]}...")
            else:
                print(f"❌ ПРОВАЛ ({elapsed:.2f} сек): {str(res)[:100]}...")
                
        except Exception as e:
            print(f"💥 КРАШ: {type(e).__name__}: {e}")

    if orch.mcp_manager:
        await orch.mcp_manager.close_all()

    print("\n========================================")
    print(f"📊 ИТОГ: {success_count}/{len(TASKS)} успешно.")
    print(f"📈 SUCCESS RATE: {(success_count/len(TASKS))*100:.1f}%")
    print(f"⏱ СРЕДНЕЕ ВРЕМЯ: {total_time/len(TASKS):.2f} сек.")
    print("========================================")

asyncio.run(main())
