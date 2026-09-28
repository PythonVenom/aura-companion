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
import json
import subprocess
from pathlib import Path
import sys
import time

# Слух и голос — из старой папки agents/ (проверенные, работают)
from aura.agents.listener import AgentListener
from aura.agents.speaker import AgentSpeaker
from aura.agents.barge_in import AgentBargeIn

# Новая модульная сборка
from aura.bootstrap import build_orchestrator
from aura.status import set_status, clear_status
from aura import settings
from aura.heartbeat import Heartbeat
from aura.dialog_fsm import get_state as fsm_get, clear_state as fsm_clear, set_state as fsm_set
from aura.dialogue_manager import DialogueManager, SCENARIOS
from aura.agents.proactive import default_engine


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
        self.barge_in = AgentBargeIn()
        self.heartbeat = Heartbeat()
        self.orch = build_orchestrator()
        self.running = True

        # Достаём агентов, которых будем дёргать вручную
        self.journal = _get_agent(self.orch, "journal")
        self.rag_memory = _get_agent(self.orch, "rag_memory")
        self.audio_router = _get_agent(self.orch, "audio_router")
        self.vk_music = _get_agent(self.orch, "vk_music")
        self.registry = _get_agent(self.orch, "registry")
        self.ducker = _get_agent(self.orch, "music_ducker")
        self.media_pause = _get_agent(self.orch, "media_pause")

        # Dialogue Manager (ADR-013)
        self.dm = DialogueManager(
            SCENARIOS,
            get_agent=lambda n: _get_agent(self.orch, n),
        )

        # Proactive Engine (ADR-014)
        self.proactive = default_engine(get_agent=lambda n: _get_agent(self.orch, n))

    PAUSE_FLAG = Path("/tmp/aura_pause.flag")

    def _is_paused(self) -> bool:
        """Проверить файл-флаг паузы (hotkey)."""
        return self.PAUSE_FLAG.exists()

    def _set_barge_speaking(self, value: bool) -> None:
        """Активировать/деактивировать VAD barge-in. Best-effort."""
        if not self.barge_in:
            return
        try:
            self.barge_in.set_aura_speaking(value)
        except Exception as e:
            print(f"⚠️ BargeIn set_speaking: {e}")

    def _on_barge_in(self) -> None:
        """Callback при перебивании: остановить речь Ауры."""
        print("🛑 Перебиваю Ауру (barge-in)...")
        try:
            self.speaker.stop_speaking()
        except Exception as e:
            print(f"⚠️ BargeIn stop: {e}")

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

    def _duck_on(self) -> None:
        """Пауза музыки перед речью. Best-effort.

        Ducking (pactl set-sink-input-volume) не работает на Firefox/PipeWire —
        stream пересоздаётся. Пауза через MPRIS работает везде.
        """
        if not self.media_pause:
            return
        try:
            self.media_pause.pause()
        except Exception as e:
            print(f"⚠️ Pause: {e}")

    def _duck_off(self) -> None:
        """Возобновить музыку после речи. Best-effort."""
        if not self.media_pause:
            return
        try:
            self.media_pause.resume()
        except Exception as e:
            print(f"⚠️ Resume: {e}")

    def _say_with_duck(self, text: str) -> None:
        """Сказать короткое сообщение с паузой музыки (блокирующе).

        Ждём is_speaking, а не aplay_process: say() ставит флаг
        синхронно, а aplay_process создаётся в потоке позже
        (после синтеза piper). Иначе resume срабатывает мгновенно.
        """
        print(f"🔊 Скажу: {text[:80]}")
        self._duck_on()
        self._set_barge_speaking(True)
        self.speaker.say(text)
        while self.speaker.is_speaking:
            time.sleep(0.05)
        self._set_barge_speaking(False)
        self._duck_off()

    @classmethod
    def _activation_words(cls):
        """Слова активации из settings + базовые."""
        base = (
            "аура", "ауру", "ауры", "ауре", "ауро",
            "ара", "аро", "ару",
            "ура", "уру",
            "алла", "алло", "ала", "ало", "олла",
            "аула", "ауло", "aura",
        )
        try:
            custom = settings.get_activation_words()
            return tuple(custom) + base
        except Exception:
            return base

    ACTIVATION = (
        "аура", "ауру", "ауры", "ауре", "ауро",
        "ара", "аро", "ару",
        "ура", "уру",
        "алла", "алло", "ала", "ало", "олла",
        "аула", "ауло",
        "aura",
    )

    @classmethod
    def _is_activated(cls, heard: str) -> bool:
        text = heard.lower()
        return any(a in text for a in cls._activation_words())

    @classmethod
    def _strip_activation(cls, heard: str) -> str:
        result = heard.lower()
        for a in cls.ACTIVATION:
            result = result.replace(a, "")
        return " ".join(result.split()).strip(".,!? ")

    def _handle_dialog(self) -> bool:
        """DialogueManager активен — слушаем без активации (ADR-013)."""
        if not self.dm.is_active():
            return False
        set_status("listening")
        heard = self.listener.listen(timeout=5)
        if not heard:
            return True
        print(f"💬 DM: {heard}")
        # Bug 6: в awaiting_confirm — сначала пробуем «да/нет/отправ»,
        # потом уже проверяем активацию. ASR часто добавляет «аура»
        # рефлекторно в конце («да отправ шаура»).
        if getattr(self.dm.state, "awaiting_confirm", False):
            resp = self.dm.process(heard)
            if resp:
                print(f"🤖 {resp}")
                self._say_with_duck(resp)
            return True
        # Вне подтверждения — активация сбрасывает DM.
        if self._is_activated(heard):
            print("🔔 Активация — сброс DM")
            self.dm.reset()
            return False
        resp = self.dm.process(heard)
        if resp:
            print(f"🤖 {resp}")
            self._say_with_duck(resp)
        return True

    def _handle_fsm(self) -> bool:
        """Обработать FSM-состояние диалога (ADR-012).

        Возвращает True если состояние активно и цикл должен continue.
        """
        fsm = fsm_get()
        state = fsm.get("state", "idle")
        if state == "idle":
            return False

        chat = fsm.get("chat", "")
        # Слушаем БЕЗ активации «Аура».
        try:
            heard = self.listener.listen(timeout=5)
        except Exception as e:
            print(f"⚠️ FSM listen error: {e}")
            return True
        if not heard:
            return True

        text = heard.lower().strip()
        print(f"💬 FSM[{state}]: {heard}")

        # В pending_read сначала проверяем «да/нет» (Bug 1 fix).
        # T-one часто добавляет «аура» рефлекторно — не считаем это сбросом.
        if state == "pending_read":
            if any(w in text for w in ("да", "зачитай", "читай", "конечно", "давай")):
                msg_text = fsm.get("text", "")
                chat_from_fsm = fsm.get("chat", "")
                if msg_text:
                    self._say_with_duck(f"Сообщение: {msg_text}")
                else:
                    self._say_with_duck("Сообщение пустое")
                # Bug 15: сохраняем chat → awaiting_reply для голосового ответа
                if chat_from_fsm:
                    fsm_set("awaiting_reply", chat=chat_from_fsm)
                else:
                    fsm_clear()
                return True
            if any(w in text for w in ("нет", "не надо", "потом", "позже", "отмена", "стоп", "отменить")):
                fsm_clear()
                self._say_with_duck("Хорошо")
                return True
            # Если «аура» — сброс, новая команда.
            if "аура" in text or "aura" in text:
                print("🔔 Активация — сброс FSM")
                fsm_clear()
                return False
            # Другое — напомнить.
            self._say_with_duck("Зачитать?")
            return True

        # Bug 15: awaiting_reply — контекст ответа в чат
        if state == "awaiting_reply":
            # «ответь», «напиши», «скажи» + текст
            for kw in ("ответь ей", "ответь ему", "ответь", "напиши ей", "напиши ему", "напиши", "скажи ей", "скажи ему", "скажи"):
                if kw in text:
                    idx = text.index(kw) + len(kw)
                    reply_text = heard[idx:].strip(":.,!? ")
                    if not reply_text:
                        self._say_with_duck("Что ответить?")
                        return True
                    messenger = _get_agent(self.orch, "messenger")
                    if messenger and chat:
                        resp = messenger.send_message(chat, reply_text)
                        self._say_with_duck(resp)
                        fsm_set("ask_confirm", chat=chat)
                    else:
                        self._say_with_duck("Не могу отправить")
                        fsm_clear()
                    return True
            # Отказ
            if any(w in text for w in ("нет", "не надо", "отмена", "отменить", "стоп", "пока")):
                fsm_clear()
                self._say_with_duck("Хорошо")
                return True
            # Новая активация
            if "аура" in text or "aura" in text:
                print("🔔 Активация — сброс FSM")
                fsm_clear()
                return False
            # Не распознали
            self._say_with_duck("Ответить или нет?")
            return True

        # Новая «Аура ...» — сброс.
        if "аура" in text or "aura" in text:
            print("🔔 Активация — сброс FSM")
            fsm_clear()
            return False

        # Отмена.
        if any(w in text for w in ("отмена", "отменить", "стоп")):
            fsm_clear()
            self._say_with_duck("Отменила")
            return True

        if state == "awaiting_command":
            # Команда после активации без «Аура».
            print(f"📝 Команда (после активации): {heard}")
            fsm_clear()
            # Проверка DM-сценария (ADR-013).
            scenario = self.dm.detect(heard)
            if scenario:
                self.dm.start(scenario)
                resp = self.dm.process(heard)
                if resp:
                    print(f"🤖 {resp}")
                    self._say_with_duck(resp)
                return True
            try:
                import asyncio as _asyncio
                response = _asyncio.run(self.orch.process(heard))
                print(f"🤖 {response}")
                self._say_with_duck(response)
            except Exception as e:
                print(f"⚠️ Ошибка обработки: {e}")
                self._say_with_duck("Не расслышала")
            return True

        if state == "ask_text":
            # Всё что сказано — текст сообщения.
            messenger = _get_agent(self.orch, "messenger")
            if not messenger:
                fsm_clear()
                return True
            resp = messenger.send_message(chat, heard)
            fsm_set("ask_confirm", chat=chat)
            self._say_with_duck(resp)
            return True

        if state == "ask_confirm":
            if any(w in text for w in ("да", "отправ", "ок", "yes")):
                messenger = _get_agent(self.orch, "messenger")
                if messenger:
                    resp = messenger.finalize_send()
                    self._say_with_duck(resp)
                fsm_clear()
                return True
            if any(w in text for w in ("нет", "no")):
                messenger = _get_agent(self.orch, "messenger")
                if messenger:
                    messenger.clear_input()
                fsm_clear()
                self._say_with_duck("Отменила")
                return True
            # Другое — напомним.
            self._say_with_duck("Скажи да или нет")
            return True

        return False

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

        set_status("idle")
        self.heartbeat.start()

        # === BARGE-IN: включён (ADR-009 + aura-aec.service) ===
        if self.barge_in and self.barge_in.ready:
            if self.barge_in.start(on_speech=self._on_barge_in):
                print("✅ BargeIn запущен (перебивание работает)")

        while self.running:
            try:
                self.heartbeat.beat()

                # === ПАУЗА (hotkey) ===
                if self._is_paused():
                    set_status("paused")
                    time.sleep(0.2)
                    continue

                # === АУДИО-МАРШРУТИЗАЦИЯ (раз в 5 сек) ===
                if self.audio_router:
                    try:
                        _profile, audio_msg = self.audio_router.check_route()
                        if audio_msg:
                            print(f"🔊 {audio_msg}")
                            self._say_with_duck(audio_msg)
                    except Exception as e:
                        print(f"⚠️ AudioRouter: {e}")

                # === АНТИ-ЭХО: не слушаем, пока говорим ===
                if self.speaker.is_speaking:
                    time.sleep(0.1)
                    continue

                # === DIALOG FSM (ADR-012) ===
                # === PROACTIVE (ADR-014) ===
                proactive_msg = self.proactive.check()
                if proactive_msg:
                    print(f"💡 Proactive: {proactive_msg}")
                    self._say_with_duck(proactive_msg)
                    continue

                if self._handle_fsm():
                    continue

                if self._handle_dialog():
                    continue

                # Слушаем (timeout 5 секунд)
                set_status("listening")
                heard = self.listener.listen(timeout=5)

                if not heard:
                    time.sleep(0.1)
                    continue

                if not self._is_activated(heard):
                    time.sleep(0.1)
                    continue

                print("🔔 Активация!")
                cmd = self._strip_activation(heard).strip()
                if not cmd:
                    fsm_set("awaiting_command")
                    time.sleep(0.3)
                    continue

                if self.registry:
                    try:
                        self.registry.log("command", {"command": cmd})
                    except Exception as e:
                        print(f"⚠️ Registry не записал: {e}")

                print(f"📝 Команда: {cmd}")

                # === DIALOGUE MANAGER (ADR-013) ===
                self.speaker.active = True
                set_status("thinking", cmd)
                scenario = self.dm.detect(cmd)
                if scenario:
                    self.dm.start(scenario)
                    response = self.dm.process(cmd) or "Не расслышала"
                else:
                    response = asyncio.run(self.orch.process(cmd))
                # Пишем последний диалог для виджета.
                try:
                    Path("/tmp/aura_last_dialog.json").write_text(
                        json.dumps({"user": cmd, "aura": response}, ensure_ascii=False),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                print(f"🤖 {response}")
                set_status("speaking", response)
                self._duck_on()
                self._set_barge_speaking(True)
                # ADR-048: silent=True — не озвучивать
                if not self.orch.last_silent():
                    self.speaker.say(response)

                # === RAG-ПАМЯТЬ И ЖУРНАЛ (после ответа) ===
                if self.registry:
                    try:
                        self.registry.log("dialog", {"user": cmd, "aura": response})
                    except Exception as e:
                        print(f"⚠️ Registry не записал диалог: {e}")

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

                # Ждём окончания речи — по is_speaking, не aplay_process
                while self.speaker.is_speaking:
                    time.sleep(0.05)
                self._set_barge_speaking(False)
                self._duck_off()

                # Пауза между командами
                if "\n" in response:
                    time.sleep(1.5)
                else:
                    time.sleep(0.5)
                self.speaker.active = False
                set_status("idle")

                time.sleep(0.1)

            except KeyboardInterrupt:
                # Обработка первого Ctrl+C: чистим и выходим.
                # Второй Ctrl+C во время очистки игнорируем — иначе traceback.
                try:
                    print("\n🦾 Аура: До свидания! 👋")
                    if self.barge_in:
                        self.barge_in.stop()
                    self.heartbeat.stop()
                    clear_status()
                except KeyboardInterrupt:
                    pass
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(0.5)


def main() -> int:
    aura = AuraOrchestrator()
    try:
        aura.run()
    except KeyboardInterrupt:
        # Второй Ctrl+C (или Ctrl+C вне цикла) — выходим чисто.
        print()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
