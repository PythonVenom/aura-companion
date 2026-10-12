"""aura chat — интерактивный чат с Аурой.

Один REPL: вводишь команду → оркестратор → ответ голосом + текстом.

F-102: возвращаем меню, которое было в другой сессии.
"""
from __future__ import annotations

import asyncio
import sys

# ─── Справка ────────────────────────────────────────────
HELP = """
🛸  AURA CHAT — что умеет:

  🎵 Музыка:      включи музыку / тише / громче / следующий / пауза / стоп
  🖥  Окна:        следующий рабочий стол / предыдущий / новый стол
  📺 Обзор:       обзор / что в фокусе / диагностика
  🌤  Погода:      погода / погода на завтра / погода на дачу
  🕐 Время:       сколько времени / какое число
  💊 Таблетки:    таблетки / напомни про таблетки
  📅 Календарь:   календарь / что в календаре
  🚨 SOS:         SOS / помоги / вызов скорой
  📝 Заметки:     заметка <текст>
  🔍 Поиск:       найди <текст> в интернете
  🧠 RAG:         что ты знаешь о <тема>

  ? или help  — эта справка
  exit / q    — выход

  Голос: Аура отвечает вслух если speaker активен
"""


# ─── Главный цикл ────────────────────────────────────────
async def _main_loop() -> int:
    from aura.bootstrap import build_orchestrator
    from aura.core.protocol import AgentRequest

    orch = build_orchestrator()
    print(f"🛸 AURA CHAT · агентов: {len(orch.registry)}")
    print("   ? — справка, exit — выход")
    print()

    # Голос — опционально
    speaker = None
    try:
        from aura.agents.speaker import AgentSpeaker
        speaker = AgentSpeaker()
        print("🔊 Speaker активен")
    except Exception as e:
        print(f"⚠️ Speaker недоступен: {e}")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        cmd = raw.lower()

        # Спецкоманды
        if cmd in ("exit", "quit", "q", "выход"):
            break
        if cmd in ("?", "help", "справка"):
            print(HELP)
            continue

        # Отдать оркестратору
        try:
            req = AgentRequest(text=raw)

            # Найти подходящий агент
            agent = orch.registry.find(req) if hasattr(orch.registry, "find") else None

            if agent is not None:
                resp = await agent.handle(req)
                text = getattr(resp, "text", None) or str(resp)
            else:
                # Общий путь — через оркестратор
                text = await orch.process(raw)

            print(f"🤖 {text}")

            # Озвучить
            if speaker is not None and text:
                try:
                    speaker.say(text)
                    speaker.wait(timeout=30)
                except Exception as e:
                    print(f"⚠️ speaker: {e}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    print("🦾 До связи.")
    return 0


def main() -> int:
    """Точка входа."""
    try:
        return asyncio.run(_main_loop())
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
