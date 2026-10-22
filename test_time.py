import asyncio
from aura.bootstrap import build_orchestrator

async def main():
    orch = build_orchestrator()
    print("--- ТЕСТ: Сколько времени? ---")
    res = await orch.process("Сколько времени?")
    print(f"Ответ: {res}")

asyncio.run(main())
