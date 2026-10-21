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
import contextlib
import json
import queue as _queue
import sys
import time
from pathlib import Path

from aura import settings
from aura.agents.barge_in import AgentBargeIn

# Слух и голос — из старой папки agents/ (проверенные, работают)
from aura.agents.listener import AgentListener
from aura.agents.proactive import default_engine
from aura.agents.speaker import AgentSpeaker

# Новая модульная сборка
from aura.bootstrap import build_orchestrator
from aura.core import hands_free
from aura.core.chat_bridge import ChatBridge
from aura.core.chat_watcher import ChatWatcher
from aura.kernel.agents.system_control import handle_system_command
from aura.dialog_fsm import clear_state as fsm_clear
from aura.dialog_fsm import get_state as fsm_get
from aura.dialog_fsm import set_state as fsm_set
from aura.dialogue_manager import SCENARIOS, DialogueManager
from aura.heartbeat import Heartbeat
from aura.kernel.thread import KernelThread
from aura.status import clear_status, set_status


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

        # F-015: elder-care toggle на интеграционном слое (Beck 2002 TDD:
        # component не знает о settings; injection здесь).
        try:
            from aura import settings as _s
            if not _s.get("barge_in", True):
                self.barge_in.ready = False
                print("🔇 BargeIn отключён (settings.barge_in=False, elder-care)")
        except Exception:
            pass
        self._halted = False  # Bug 29: halt после barge-in
        # Bug 46: _ensure_aec отключён (pactl deadlock при переключении)
        # ADR-050: push-to-stop watcher (thread)
        import threading

        from scripts.aura_stop_watcher import watch as _watch_stop
        threading.Thread(
            target=_watch_stop, args=(self.speaker,), daemon=True, name="aura-stop"
        ).start()
        print("✅ Push-to-stop: /tmp/aura.stop watcher запущен")
        self.heartbeat = Heartbeat()
        self.orch = build_orchestrator()

        # F-067: автозапуск ONE-SHOT (спустить воздух)
        try:
            from aura.system.oneshot import run_oneshot
            r = run_oneshot(dry_run=False, restart_daemon=False, verbose=False)
            if r.ruff_fixed > 0:
                print(f"🩹 ONE-SHOT: починил {r.ruff_fixed} ошибок")
            if r.is_clean():
                print("🩹 ONE-SHOT: система чиста")
        except Exception as e:
            print(f"⚠️ ONE-SHOT не запустился: {e}")

        # F-065: глубокая проверка при старте
        try:
            from aura.system.deep_check import run_deep_check
            report = run_deep_check()
            if report.all_ok:
                print(f"🛸 Глубокая проверка: {report.total} систем в норме")
            else:
                print(f"⚠️ Глубокая проверка: "
                      f"{report.ok_count}/{report.total} в норме")
                for r in report.failures()[:5]:
                    print(f"   🔴 {r.name}: {r.detail}")
        except Exception as e:
            print(f"⚠️ Deep check не запустился: {e}")

        # F-037: самопроверка при старте (говорит голосом)
        try:
            import asyncio as _aio

            from aura.agents.self_check import AgentSelfCheck
            _check = AgentSelfCheck()
            _report = _aio.run(_check.handle(
                __import__("aura.core.protocol", fromlist=["AgentRequest"])
                .AgentRequest(text="проверь себя")
            ))
            print(f"🛸 Самопроверка: {_report.text}")
        except Exception as _e:
            print(f"⚠️ Самопроверка не удалась: {_e}")

        # Capability-профиль (Saltzer & Schroeder 1975, least privilege).
        # Borderlands-style: base_class + trees + class_mods.
        try:
            from aura import settings
            from aura.core.capabilities import Profile, set_current
            prof_name = settings.get("capability_profile", "elder")
            # Разбор: "elder-medical" → base=elder, trees=[medical]
            parts = prof_name.split("-")
            base_class = parts[0]
            trees = tuple(parts[1:]) if len(parts) > 1 else ()
            print("🔥 [INIT] set_current(Profile)...", flush=True)
            print("🔥 [INIT] set_current(Profile)...", flush=True)
            set_current(Profile(
                name=prof_name,
                base_class=base_class,
                trees=trees,
            ))
            import logging
            logging.getLogger("aura").info(
                "Capability profile: %s (caps=%d)",
                prof_name, len(Profile(name=prof_name,
                                       base_class=base_class,
                                       trees=trees).capabilities()),
            )
        except Exception as e:
            import logging
            logging.getLogger("aura").warning(
                "Capability profile setup failed: %s — fail-open", e,
            )
        self.running = True
        print("🔥 [INIT] ChatBridge()...", flush=True)
        print("🔥 [INIT] ChatBridge()...", flush=True)
        self.chat_bridge = ChatBridge()
        print("🔥 [INIT] ChatBridge создан!", flush=True)
        print("🔥 [INIT] ChatBridge создан!", flush=True)
        self.chat_queue: _queue.Queue = _queue.Queue()
        print("🔥 [INIT] ChatWatcher()...", flush=True)
        print("🔥 [INIT] ChatWatcher()...", flush=True)
        self.chat_watcher = ChatWatcher(self.chat_bridge, self.chat_queue)
        print("🔥 [INIT] ChatWatcher создан!", flush=True)
        print("🔥 [INIT] ChatWatcher создан!", flush=True)

        # Достаём агентов, которых будем дёргать вручную
        print("🔥 [INIT] journal...", flush=True)
        print("🔥 [INIT] journal...", flush=True)
        print("🔥 [INIT] journal...", flush=True)
        self.journal = _get_agent(self.orch, "journal")
        print("🔥 [INIT] rag_memory...", flush=True)
        self.rag_memory = _get_agent(self.orch, "rag_memory")
        print("🔥 [INIT] audio_router...", flush=True)
        self.audio_router = _get_agent(self.orch, "audio_router")
        print("🔥 [INIT] vk_music...", flush=True)
        self.vk_music = _get_agent(self.orch, "vk_music")
        print("🔥 [INIT] registry...", flush=True)
        self.registry = _get_agent(self.orch, "registry")
        print("🔥 [INIT] ducker...", flush=True)
        self.ducker = _get_agent(self.orch, "music_ducker")
        print("🔥 [INIT] media_pause...", flush=True)
        self.media_pause = _get_agent(self.orch, "media_pause")

        # Dialogue Manager (ADR-013)
        print("🔥 [INIT] DialogueManager...", flush=True)
        self.dm = DialogueManager(
            SCENARIOS,
            get_agent=lambda n: _get_agent(self.orch, n),
        )

        # Proactive Engine (ADR-014)
        print("🔥 [INIT] proactive...", flush=True)
        self.proactive = default_engine(get_agent=lambda n: _get_agent(self.orch, n))

        # C-0.6: KernelThread — async kernel параллельно sync Orchestrator
        self.kernel_thread: KernelThread | None = None
        print("🔥 [INIT] __init__ завершен!", flush=True)

    PAUSE_FLAG = Path.home() / ".cache/aura/aura_pause.flag"
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
        """Callback при перебивании: остановить речь Ауры + пометить halt.

        Bug 33: если уже halted (Аура остановлена) — не логировать и не звать stop.
        """
        if self._halted:
            return  # уже остановлена — игнор повторных срабатываний
        print("🛑 Перебиваю Ауру (barge-in)...")
        self._halted = True  # Bug 29: следующая реплика — halt
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

    def _ensure_aec(self) -> None:
        """Bug 40: force AEC. Throttle 30 сек — не дёргать OSD.

        Aura говорила в alsa_output → эхо попадало в микрофон → barge-in ловил
        саму Ауру. WirePlumber периодически откатывает sink обратно.
        """
        import time as _t
        now = _t.time()
        # Bug 43: throttle 3 сек — если Аура говорит дольше, AEC может откатиться
        if now - getattr(self, "_aec_last_check", 0) < 3:
            return
        self._aec_last_check = now
        try:
            import subprocess
            # Bug 44: НЕ трогаем sink (echo-cancel-sink даёт троение, см. Bug 10).
            # Достаточно source: echo-cancel-source вычитает из sink_master=alsa_output.
            r = subprocess.run(
                ["pactl", "get-default-source"],
                capture_output=True, text=True, timeout=8,
            )
            if "echo-cancel" not in r.stdout:
                subprocess.run(
                    ["pactl", "set-default-source", "echo-cancel-source"],
                    check=False, timeout=8,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                print("🎙️ AEC: source → echo-cancel-source")
        except Exception as e:
            print(f"⚠️ AEC force: {e}")

    def _duck_on(self) -> None:
        """Приглушить музыку перед речью (не пауза, -20dB). Bug 38.

        Ducking через pactl set-sink-input-volume. Media_pause fallback
        если ducker не готов.
        """
        if self.ducker is not None:
            try:
                self.ducker.duck()
                return
            except Exception as e:
                print(f"⚠️ Duck: {e}")
        # Fallback — полная пауза
        if self.media_pause:
            try:
                self.media_pause.pause()
            except Exception as e:
                print(f"⚠️ Pause: {e}")

    def _duck_off(self) -> None:
        """Восстановить громкость после речи. Bug 38."""
        if self.ducker is not None:
            try:
                self.ducker.un_duck()
                return
            except Exception as e:
                print(f"⚠️ UnDuck: {e}")
        if self.media_pause:
            try:
                self.media_pause.resume()
            except Exception as e:
                print(f"⚠️ Resume: {e}")

    def _say_with_duck(self, text: str) -> None:
        """F-067-fix: duck → say → un_duck.

        Ducking защищён try/except — если упадёт,
        voice всё равно пойдёт (Bug 38 + F-066).
        """
        if not text:
            return
        print(f"🔊 Скажу: {text[:80]}")

        # Ducking — приглушаем музыку (не блокирует)
        ducked = False
        try:
            if hasattr(self, "ducker") and self.ducker is not None:
                self.ducker.duck()
                ducked = True
        except Exception as e:
            print(f"⚠️ duck: {e}")

        try:
            if self.speaker is not None:
                self.speaker.say(text)
                self.speaker.wait()
        except Exception as e:
            print(f"⚠️ speaker: {e}")

        # Un-duck — вернуть музыку
        if ducked:
            try:
                self.ducker.un_duck()
            except Exception as e:
                print(f"⚠️ un_duck: {e}")

    @classmethod
    def _activation_words(cls):
        """Слова активации из settings + базовые."""
        base = (
            "аура", "ауру", "ауры", "ауре", "ауро",
        "лаура", "ура", "ора", "ау", "ауу", "аурум",
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

    # AURA_WHITELIST_V1 — фразы, работающие без "аура" (для elder care)
    WHITELIST_NO_WAKE = (
        "сколько времени", "который час",
        "какой день", "какое число", "какой сегодня",
        "какая погода", "погода на",
        "мне плохо", "помогите", "вызови скорую", "вызов скорой",
        "sos", "тревога", "упал", "упала",
        "пора пить", "напомни про лекарств",
    )

    @classmethod
    def _is_activated(cls, heard: str) -> bool:
        """Wake-word через fuzzy (Levenshtein 1965).

        F-021d: «Аура» → «алло», «аула», «алла» — всё ловится.
        «ураган», «арахис», «пауза» — НЕ ловятся.
        Elder-care whitelist — приоритет.
        """
        try:
            from aura.wake_detector import is_wake_word
            return is_wake_word(heard)
        except Exception:
            # Fallback: старая логика
            text = heard.lower()
            if any(a in text for a in cls._activation_words()):
                return True
            return any(w in text for w in cls.WHITELIST_NO_WAKE)

    @classmethod
    def _strip_activation(cls, heard: str) -> str:
        """Убрать wake-word через fuzzy (F-021d)."""
        try:
            from aura.wake_detector import strip_wake_word
            return strip_wake_word(heard)
        except Exception:
            result = heard.lower()
            for a in cls.ACTIVATION:
                result = result.replace(a, "")
            return " ".join(result.split()).strip(".,!? ")

    def _handle_dialog(self) -> bool:
        """DialogueManager активен — слушаем без активации (ADR-013)."""
        if not self.dm.is_active():
            return False
        set_status("listening")
        heard = self.listener.listen(timeout=1)  # Bug 34
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
            heard = self.listener.listen(timeout=1)  # Bug 34
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
            # FIX: новая активация «аура» — СНАЧАЛА сброс FSM
            # FIX: новая активация «аура» — СНАЧАЛА сбрасываем FSM
            if "аура" in text or "aura" in text:
                print("🔔 Активация — сброс FSM (awaiting_reply)")
                fsm_clear()
                return False
            # Отказ
            if any(w in text for w in ("нет", "не надо", "отмена", "отменить", "стоп", "пока")):
                fsm_clear()
                self._say_with_duck("Хорошо")
                return True
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
        if state != "awaiting_command" and ("аура" in text or "aura" in text):
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
                # F-066: сначала агент, потом LLM
                response = None
                try:
                    from aura.core.protocol import AgentRequest as _AR
                    _req = _AR(text=heard)
                    _agent = self.orch.registry.find(_req)
                    if _agent is not None:
                        print(f'🎯 Агент: {_agent.name}')
                        _resp = asyncio.run(_agent.handle(_req))
                        response = getattr(_resp, 'text', None) or str(_resp)
                except Exception as _e:
                    print(f'⚠️ agent route: {_e}')
                if not response:
                    response = asyncio.run(self.orch.process(heard))
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

    def _drain_chat_queue(self) -> None:
        # CHAT_DEDUP v2 (Bug 74): окно 30 сек + ограничение размера словаря
        import time as _t
        if not hasattr(self, "_chat_dedup"):
            self._chat_dedup = {}
        _DEDUP_SEC = 30.0
        """Обработать сообщения из чата (ChatBridge → orchestrator → history)."""
        while True:
            try:
                msg = self.chat_queue.get_nowait()
            except _queue.Empty:
                return
            user_text = (msg or {}).get("user", "").strip()
            print(f"🔍 [DRAIN] Получено сообщение: {user_text!r}", flush=True)
            if not user_text:
                continue
            _now = _t.time()
            _last = self._chat_dedup.get(user_text, 0)
            if _now - _last < _DEDUP_SEC:
                # тихо пропускаем — не спамим в консоль
                continue
            self._chat_dedup[user_text] = _now
            # чистим старые ключи, чтобы dict не рос бесконечно
            if len(self._chat_dedup) > 100:
                _cutoff = _now - _DEDUP_SEC
                self._chat_dedup = {
                    k: v for k, v in self._chat_dedup.items() if v > _cutoff
                }
            # СТОП-КРАН
            if any(w in user_text.lower() for w in ['стоп', 'остановись', 'замолчи', 'хватит']):
                self.chat_bridge.append_history(user_text, "Останавливаюсь. Жду следующей команды.")
                continue

            # ДРЕВО УМЕНИЙ (Diablo Style)
            if any(w in user_text.lower() for w in ['что ты умеешь', 'твои навыки', 'древо умений']):
                import subprocess
                tree = subprocess.run(['bash', '/home/pythonvenom/.config/quickshell/scripts/skills_tree.sh'], capture_output=True, text=True)
                self.chat_bridge.append_history(user_text, tree.stdout)
                continue

            # МЕНТОР ОС: проверяем системные команды (выключить/ребут/сон)
            sys_cmd = handle_system_command(user_text)
            if sys_cmd:
                response = sys_cmd
                try:
                    self.chat_bridge.append_history(user_text, response)
                except Exception as e:
                    print(f'⚠️ chat history (sys): {e}', flush=True)
                continue

            try:
                response = asyncio.run(self.orch.process(user_text))
            except Exception as e:
                response = f"❌ {e}"
            try:
                self.chat_bridge.append_history(user_text, response)
            except Exception as e:
                print(f"⚠️ chat history: {e}", flush=True)
            if self.speaker is not None:
                self.speaker.say(response)

    def run(self) -> None:
        print("🔥🔥🔥 [RUN] Метод run() ВЫЗВАН!", flush=True)
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
        self.chat_watcher.start()

        # === BARGE-IN: включён (ADR-009 + aura-aec.service) ===
        if self.barge_in and self.barge_in.ready:
            if self.barge_in.start(on_speech=self._on_barge_in):
                print("✅ BargeIn запущен (перебивание работает)")

        while self.running:
            try:
                print("🔄 [LOOP] tick", flush=True)
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
                # === PROACTIVE (ADR-014) — Bug 39: ОТКЛЮЧЁН до фикса ===
                # proactive_msg = self.proactive.check()
                # if proactive_msg:
                #     print(f"💡 Proactive: {proactive_msg}")
                #     self._say_with_duck(proactive_msg)
                #     continue

                if self._handle_fsm():
                    continue

                if self._handle_dialog():
                    continue

                # === ЧАТ: text-based IPC ===
                print("📖 [LOOP] reading INBOX...", flush=True)
                for msg in self.chat_bridge.read_new():
                    self.chat_queue.put(msg)
                self._drain_chat_queue()

                # Слушаем (timeout 8 секунд)
                print("🎤 [LOOP] listening...", flush=True)
                set_status("listening")
                # Bug 40: AEC force перед слушанием (микрофон = echo-cancel-source)
                # self._ensure_aec()  # DISABLED: echo-cancel душит микрофон
                # Bug 38: приглушаем музыку ПОКА слушаем (интеллектуальный duck)
                self._duck_on()
                # Bug 73: timeout 2 вместо 8 — ChatBridge голодал до 8 сек
                heard = self.listener.listen(timeout=1)
                print(f"🎤 heard={heard!r}")
                if not heard:
                    self._duck_off()
                    # === ЧАТ: второй drain после listen (Bug 73) ===
                    self._drain_chat_queue()
                    time.sleep(0.05)
                    continue

                if not heard:
                    time.sleep(0.1)
                    continue

                # === ЧАТ: drain после успешного listen ===
                self._drain_chat_queue()

                if not self._is_activated(heard):
                    # Hands-Free: пропустить без активации
                    if not hands_free.is_active():
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

                # === Bug 29: HALT/RESUME после barge-in ===
                _STOP = ("стоп", "замолчи", "хватит", "тихо", "останови",
                         "остановись", "молчи", "заткнись")
                _RESUME = ("продолжай", "дальше", "продолжи")
                _low = cmd.lower()
                if len(_low) < 40 and any(w in _low for w in _STOP):
                    self._halted = False
                    print("🤫 Halt (молчу)")
                    continue  # молча — не в LLM
                if any(w in _low for w in _RESUME):
                    self._halted = False
                    self._say_with_duck("Продолжаю.")
                    continue
                if self._halted:
                    self._halted = False  # сброс, идём в LLM нормально

                # === DIALOGUE MANAGER (ADR-013) ===
                self.speaker.active = True
                set_status("thinking", cmd)
                scenario = self.dm.detect(cmd)
                if scenario:
                    self.dm.start(scenario)
                    response = self.dm.process(cmd) or "Не расслышала"
                else:
                    # F-066: сначала агент, потом LLM
                    response = None
                    try:
                        from aura.core.protocol import AgentRequest as _AR2
                        _req2 = _AR2(text=cmd)
                        _ag2 = self.orch.registry.find(_req2)
                        if _ag2 is not None:
                            print(f'🎯 Агент: {_ag2.name}')
                            _r2 = asyncio.run(_ag2.handle(_req2))
                            response = getattr(_r2, 'text', None) or str(_r2)
                    except Exception as _e2:
                        print(f'⚠️ agent route: {_e2}')
                    if not response:
                        response = asyncio.run(self.orch.process(cmd))
                # Пишем последний диалог для виджета.
                with contextlib.suppress(Exception):
                    (Path.home() / ".cache/aura/aura_last_dialog.json").write_text(
                        json.dumps({"user": cmd, "aura": response}, ensure_ascii=False),
                        encoding="utf-8",
                    )
                print(f"🤖 {response}")
                set_status("speaking", response)
                # F-066-fix: прямой вызов speaker без ducking и mute.
                # Старый блок (duck_on + listener.pause + last_silent)
                # блокировал голос в демоне.
                self._say_with_duck(response)

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

                # Ждём окончания речи — по is_speaking И aplay_process
                # >>> AURA_HANG_FIX_V2
                # Не форсируем, пока paplay играет (длинные ответы 20-30с).
                # Форсируем только если is_speaking=True, а aplay мёртв (hang).
                _speak_deadline = time.monotonic() + 30.0
                while time.monotonic() < _speak_deadline:
                    if not self.speaker.is_speaking:
                        break
                    _ap = getattr(self.speaker, 'aplay_process', None)
                    if _ap is not None and _ap.poll() is None:
                        # paplay жив → реально играем, продлеваем дедлайн
                        _speak_deadline = time.monotonic() + 30.0
                    time.sleep(0.05)
                if self.speaker.is_speaking:
                    _ap = getattr(self.speaker, 'aplay_process', None)
                    if _ap is None or _ap.poll() is not None:
                        print('⚠️ speaker.is_speaking завис (aplay мёртв) — форсирую')
                        self.speaker.is_speaking = False
                        if _ap is not None:
                            try:
                                _ap.kill()
                            except Exception:
                                pass
                self._set_barge_speaking(False)
                self._duck_off()
                # >>> AURA_ECHO_FIX_V2
                # Cooldown + снять mic mute
                time.sleep(1.5)
                try:
                    self.listener.resume()
                except Exception as _e:
                    print(f'⚠️ echo-resume: {_e}')

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


# >>> AURA_DAEMON_V1
def _daemon_background(aura, stop_event) -> None:
    """Фоновый цикл демона: wake() + hyperjump."""
    from aura.cockpit.hyperjump import count_modules, current_commit, did_hyperjump
    from aura.cockpit.wake import wake
    from aura.lore.persona import speak_line

    last_commit = current_commit()
    last_wake = time.monotonic()
    print(f"[daemon] старт, координаты {last_commit}", flush=True)

    while not stop_event.is_set():
        try:
            current = current_commit()
            if did_hyperjump(last_commit, current):
                print(f"[daemon] гиперпрыжок {last_commit} → {current}", flush=True)
                aura.speaker.say(speak_line("hyperjump", modules=count_modules()))
                aura.speaker.wait()
                last_commit = current

            now = time.monotonic()
            if now - last_wake >= 1800:
                print("[daemon] wake()", flush=True)
                wake()
                last_wake = now
        except Exception as e:
            print(f"[daemon] ошибка: {e}", flush=True)
        stop_event.wait(60)


def main() -> int:
    print("🔥 [MAIN] Старт main()", flush=True)
    daemon_mode = "--daemon" in _sys.argv
    print(f"🔥 [MAIN] daemon_mode={daemon_mode}", flush=True)
    print("🔥 [MAIN] Создаем AuraOrchestrator...", flush=True)
    aura = AuraOrchestrator()
    print("🔥 [MAIN] AuraOrchestrator создан!", flush=True)
    stop_event = None

    # C-0.6: запуск async kernel в daemon-потоке (Graceful Degradation)
    print("🔥 [MAIN] Создаем KernelThread...", flush=True)
    kernel_thread = KernelThread()
    print("🔥 [MAIN] Запускаем KernelThread...", flush=True)
    if kernel_thread.start(timeout=10):
        print("[main] kernel thread запущен (async kernel alive)", flush=True)
        aura.kernel_thread = kernel_thread
    else:
        print("[main] kernel thread не стартовал — работаем без него", flush=True)

    if daemon_mode:
        import threading as _th
        stop_event = _th.Event()
        t = _th.Thread(target=_daemon_background, args=(aura, stop_event),
                       daemon=True, name="aura-daemon")
        t.start()
        print("[main] демон запущен в фоне", flush=True)
        print("[main] вызываем aura.run()", flush=True)
    try:
        aura.run()
    except KeyboardInterrupt:
        print()
        return 0
    finally:
        if stop_event is not None:
            stop_event.set()
        if aura.kernel_thread is not None:
            aura.kernel_thread.stop(timeout=5)
            print("[main] kernel thread остановлен", flush=True)
    return 0


# >>> AURA_SIGTERM_FIX_V1
# Graceful shutdown: systemctl --user stop → SIGTERM → корректный выход.
import signal as _signal
import sys as _sys


def _aura_sigterm_handler(_signum, _frame):
    with contextlib.suppress(Exception):
        print("\n🦾 Аура: SIGTERM, graceful shutdown...", flush=True)
    _sys.exit(0)


for _sig in (_signal.SIGTERM, _signal.SIGINT):
    with contextlib.suppress(Exception):
        _signal.signal(_sig, _aura_sigterm_handler)

if __name__ == "__main__":
    sys.exit(main())
