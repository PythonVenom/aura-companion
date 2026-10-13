"""aura chat — интерактивный чат с Аурой.

Один REPL: вводишь команду → оркестратор → ответ голосом + текстом.

F-102: возвращаем меню, которое было в другой сессии.
"""
from __future__ import annotations

import asyncio
import contextlib
import re
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
def _split_sentences(buffer: str) -> list[str]:
    """#103: разбить буфер на предложения (.!?). Остаток остаётся."""
    parts = re.split(r"(?<=[.!?])\s+", buffer)
    if not parts:
        return []
    # Последний элемент — незавершённое предложение (если нет .!?)
    if parts and not re.search(r"[.!?]\s*$", parts[-1]):
        return parts[:-1]
    return parts


async def _stream_and_speak(orch, text: str, speaker) -> str:
    """#103: streaming ответа LLM + озвучка по предложениям.

    Perceived latency: 1.2с → 0.3с (первое предложение говорится
    пока модель дописывает остаток).
    """
    brain = getattr(orch, "brain", None)
    if brain is None or not hasattr(brain, "stream"):
        # Fallback: старый путь — НЕ озвучиваем тут
        return await orch.process(text), False

    buffer = ""
    spoken = ""
    full = []
    spoke_any = False

    def _flush(force: bool = False) -> None:
        nonlocal buffer, spoken, spoke_any
        sentences = _split_sentences(buffer)
        if force and buffer.strip():
            sentences = [buffer.strip()]
            buffer = ""
        for s in sentences:
            if s.strip():
                spoken += (" " if spoken else "") + s.strip()
                if speaker is not None:
                    with contextlib.suppress(Exception):
                        speaker.say(s.strip())
                        spoke_any = True
        # Оставляем незавершённое
        if not force and sentences:
            buffer = buffer[len("".join(sentences)):].lstrip()

    try:
        loop = asyncio.get_event_loop()
        for chunk in brain.stream(text):
            buffer += chunk
            full.append(chunk)
            _flush(force=False)
            # Даём speaker'у шанс проиграть (не блокируем)
            await asyncio.sleep(0)
        _flush(force=True)
    except Exception as e:
        return f"❌ {e}", False

    return "".join(full), spoke_any


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

            spoke = False
            if agent is not None:
                resp = await agent.handle(req)
                text = getattr(resp, "text", None) or str(resp)
            else:
                # #103: streaming через brain + озвучка по предложениям
                text, spoke = await _stream_and_speak(orch, raw, speaker)

            print(f"🤖 {text}")

            # Озвучить (если стриминг уже не озвучил)
            if speaker is not None and text and not spoke:
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
