"""aura chat — интерактивный чат с Аурой.

Один REPL: вводишь команду → оркестратор → ответ голосом + текстом.

F-102: возвращаем меню, которое было в другой сессии.
"""
from __future__ import annotations

import asyncio
import contextlib
import re
import sys

from aura.agents.music_ducker import AgentMusicDucker
from aura.indicators import is_silent

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


async def _stream_and_speak(orch, text: str, speaker, barge_in=None) -> tuple[str, bool]:
    """#103 + Bug 33a: streaming + barge-in совместимость.

    Perceived latency: 1.2с → 0.3с (первое предложение говорится
    пока модель дописывает остаток).
    """
    brain = getattr(orch, "brain", None)
    if brain is None or not hasattr(brain, "stream"):
        # Fallback: старый путь — НЕ озвучиваем тут
        return await orch.process(text), False

    # Bug 33a: включить VAD barge-in на время речи
    if barge_in is not None:
        try:
            barge_in.clear_buffer()
            barge_in.set_aura_speaking(True)
        except Exception:
            pass

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
        for chunk in brain.stream(text):
            buffer += chunk
            full.append(chunk)
            _flush(force=False)
            # Даём speaker'у шанс проиграть (не блокируем)
            await asyncio.sleep(0)
        _flush(force=True)
    except Exception as e:
        return f"❌ {e}", False
    finally:
        # Bug 33a: выключить barge-in
        if barge_in is not None:
            with contextlib.suppress(Exception):
                barge_in.set_aura_speaking(False)

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

    # Bug 33a: barge_in + stop_command («Аура стоп»)
    barge_in = None
    try:
        from aura.agents.barge_in import AgentBargeIn
        from aura.core.stop_command import recognize_stop
        barge_in = AgentBargeIn()
        if barge_in.ready:
            def _on_barge_in():
                if speaker is None or barge_in is None:
                    return
                try:
                    pcm = barge_in.get_recent_pcm()
                    if recognize_stop(pcm):
                        speaker.stop_speaking()
                        barge_in.clear_buffer()
                        print("🛑 Стоп по голосу")
                except Exception as e:
                    print(f"⚠️ barge-in: {e}")
            barge_in.start(on_speech=_on_barge_in)
            print("🎙️ Barge-in активен (Bug 33a)")
    except Exception as e:
        print(f"⚠️ Barge-in не подключён: {e}")

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
                text, spoke = await _stream_and_speak(orch, raw, speaker, barge_in)

            print(f"🤖 {text}")

            # Озвучить (если стриминг уже не озвучил)
            if speaker is not None and text and not spoke:
                _ducker = None
                try:
                    # AURA_DUCK_V1: приглушить музыку/видео пока Aura говорит
                    _ducker = AgentMusicDucker()
                    _ducker.duck()
                    if barge_in is not None:
                        barge_in.clear_buffer()
                        barge_in.set_aura_speaking(True)
                    speaker.say(text)
                    speaker.wait(timeout=30)
                except Exception as e:
                    print(f"⚠️ speaker: {e}")
                finally:
                    if barge_in is not None:
                        barge_in.set_aura_speaking(False)
                    if _ducker is not None:
                        with contextlib.suppress(Exception):
                            _ducker.un_duck()

        except Exception as e:
            print(f"❌ Ошибка: {e}")

    if barge_in is not None:
        with contextlib.suppress(Exception):
            barge_in.stop()
    print("🦾 До связи.")
    return 0


def main() -> int:
    """Точка входа. При старте — POST-диагностика (boot-report)."""
    import os
    # AURA_SKIP_BOOT_REPORT=1 — пропустить (для тестов/CI)
    if os.environ.get("AURA_SKIP_BOOT_REPORT", "0") != "1":
        try:
            from aura.core.boot_report import run_boot_report
            report = run_boot_report()
            print()
            print(report.to_text())
            print()
            if report.status != "ok":
                print("⚠️ Есть проблемы. Запусти: python -m aura.cli boot-report")
                print()
        except Exception as e:
            print(f"⚠️ Boot report не собрался: {e}")
    if is_silent():
        print("🔇 Режим тишины активен. AURA не будет озвучивать ответы.")
    try:
        return asyncio.run(_main_loop())
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
