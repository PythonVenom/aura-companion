#!/usr/bin/env python3
"""
АУРА — новая точка входа (модульная архитектура).

Переиспользует слух (AgentListener) и голос (AgentSpeaker) из старой папки agents/.
Роутинг команд — через aura.bootstrap.build_orchestrator().

Запускается только если AURA_USE_ORCHESTRATOR=1 (см. run_aura.sh).
Старый aura_core.py остаётся fallback.

По науке:
- Голос/слух не переизобретаем — берём проверенные классы
- Роутинг — через Orchestrator (модульный)
- Опасные действия (power, window_control, app_launcher) — как в монолите
- Легко откатить: убрать флаг в run_aura.sh

Паритет с монолитом (AuraCore.run):
- audio_router.check_route — маршрутизация звука
- journal.log_dialog — запись диалога
- rag_memory.remember — запись в RAG-память
- journal.get_last_session — показ прошлой сессии при старте
- VK-токен — проверка при старте
- barge-in — перебивание Ауры

Ещё НЕ покрыто (отдельные задачи):
- upgrader.waiting_for_confirmation — диалог да/нет (upgrader не мигрирован)
- tool_router + brain — LLM-роутинг (не мигрированы)
"""

import asyncio
import subprocess
import sys
import time

# Слух и голос — из старой папки agents/ (проверенные, работают)
from aura.agents.listener import AgentListener
from aura.agents.speaker import AgentSpeaker

# Новая модульная сборка
from aura.bootstrap import build_orchestrator


def _get_agent(orch, name):
    """
    Найти агента по имени через публичный __iter__.

    Не лезем в приватное поле registry._agents — используем
    публичный итератор AgentRegistry.

    Возвращает агента или None.
    """
    for agent in orch.registry:
        if agent.name == name:
            return agent
    return None


class AuraOrchestrator:
    """
    Новая Аура: слух + голос (старые) + Orchestrator (новый).
    """

    def __init__(self) -> None:
        self.listener = AgentListener()
        self.speaker = AgentSpeaker()
        self.orch = build_orchestrator()
        self.running = True

        # Достаём агентов, которых будем дёргать вручную
        self.journal = _get_agent(self.orch, "journal")
        self.rag_memory = _get_agent(self.orch, "rag_memory")
        self.audio_router = _get_agent(self.orch, "audio_router")
        self.vk_music = _get_agent(self.orch, "vk_music")

    def _print_last_session(self) -> None:
        """Показать последнюю сессию журнала при старте."""
        if not self.journal:
            return
        try:
            session = self.journal.get_last_session()
            if session and not session["is_today"]:
                print(f"\n📔 Последний раз ты был {session['date']} в {session['time']}")
                if session["pending_count"] > 0:
                    print(f"📋 Осталось задач: {session['pending_count']}")
                    for task in session["pending"]:
                        print(f"   • [ ] {task}")
                print()
        except Exception as e:
            print(f"⚠️ Журнал: {e}")

    def _print_vk_status(self) -> None:
        """Проверка VK-токена при старте."""
        if not self.vk_music:
            return
        if getattr(self.vk_music, "token", None):
            print("✅ VK Music готов (токен загружен)")
        else:
            print("⚠️ VK Music: токен не найден, проверьте vk_token.txt")

    def run(self) -> None:
        """Главный цикл — паритет с AuraCore.run."""
        print("\n" + "=" * 60)
        print("🦾 АУРА — ORCHESTRATOR v0.9")
        print("🔴 Скажи 'Аура' для активации")
        print(f"📦 Агентов в Orchestrator: {len(self.orch)}")
        print("=" * 60)
        print(f"\n✅ Загружено: {self.orch.registry.list_names()}\n")

        # При старте — показать прошлую сессию и проверить VK
        self._print_last_session()
        self._print_vk_status()

        self.listener.active = True
        self.speaker.active = True

        while self.running:
            try:
                # === АУДИО-МАРШРУТИЗАЦИЯ (раз в 5 сек) ===
                if self.audio_router:
                    try:
                        _profile, audio_msg = self.audio_router.check_route()
                        if audio_msg:
                            print(f"🔊 {audio_msg}")
                            self.speaker.say(audio_msg)
                    except Exception as e:
                        print(f"⚠️ AudioRouter: {e}")

                # === АНТИ-ЭХО: не слушаем, пока говорим ===
                if self.speaker.is_speaking:
                    time.sleep(0.1)
                    continue

                # Слушаем (timeout 5 секунд)
                heard = self.listener.listen(timeout=5)

                if not heard:
                    time.sleep(0.1)
                    continue

                if 'аура' not in heard.lower() and 'aura' not in heard.lower():
                    time.sleep(0.1)
                    continue

                print("🔔 Активация!")
                cmd = heard.replace('аура', '').replace('aura', '').strip()
                cmd = cmd.replace('Аура', '').replace('Aura', '').strip()

                # Понижаем громкость во время обработки (как в монолите)
                try:
                    subprocess.run(
                        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '30%'],
                        check=False,
                    )
                except Exception:
                    pass

                if not cmd:
                    time.sleep(0.3)
                    continue

                # === BARGE-IN: если Аура говорит, а мы слышим команду — перебиваем ===
                if self.speaker.aplay_process and self.speaker.aplay_process.poll() is None:
                    print("🛑 Перебиваю Ауру...")
                    self.speaker.stop_speaking()
                    # Даём время аудио-системе вернуться в норму
                    time.sleep(0.2)

                print(f"📝 Команда: {cmd}")

                # === ГЛАВНОЕ ОТЛИЧИЕ: process через Orchestrator ===
                self.speaker.active = True
                response = asyncio.run(self.orch.process(cmd))
                print(f"🤖 {response}")
                self.speaker.say(response)

                # === RAG-ПАМЯТЬ И ЖУРНАЛ (после ответа) ===
                if self.rag_memory:
                    try:
                        result = self.rag_memory.remember(cmd, response)
                        print(f"🧠 {result}")
                    except Exception as e:
                        print(f"⚠️ RAG не сохранил: {e}")

                if self.journal:
                    try:
                        result = self.journal.log_dialog(cmd, response)
                        print(f"📔 {result}")
                    except Exception as e:
                        print(f"⚠️ Журнал не сохранил: {e}")

                # Ждём окончания речи
                if self.speaker.aplay_process:
                    self.speaker.aplay_process.wait()

                # Пауза между командами
                if "\n" in response:
                    time.sleep(1.5)
                else:
                    time.sleep(0.5)
                self.speaker.active = False

                # Возвращаем громкость
                try:
                    subprocess.run(
                        ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '100%'],
                        check=False,
                    )
                except Exception:
                    pass

                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🦾 Аура: До свидания! 👋")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(0.5)


def main() -> int:
    aura = AuraOrchestrator()
    aura.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
