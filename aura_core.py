#!/usr/bin/env python3
"""
АУРА - ЯДРО (Мозг) v10.1 FINAL
70 МАШИНОК, VK MUSIC, БЕЗОПАСНОСТЬ, УМНЫЙ ДОМ, АВТОНОМНЫЙ РЕЖИМ
ВСЕ МАШИНКИ СОХРАНЕНЫ + ИСПРАВЛЕНИЯ WAYLAND
"""

import subprocess
import re
import time
import os
import json
import queue
import threading
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from agents.audio_router import AgentAudioRouter
from agents.time_getter import AgentTimeGetter
from agents.update_checker import AgentUpdateChecker
from agents.functions import AgentFunctions
from agents.health_monitor import AgentHealthMonitor
from agents.quantum import AgentQuantumComputer
from agents.master_key import AgentMasterKey
from agents.life_simulator import AgentLifeSimulator
from agents.mirror_world import AgentMirrorWorld
from agents.harmonizer import AgentHarmonizer
from agents.dream_architect import AgentDreamArchitect
from agents.emotional_mirror import AgentEmotionalMirror
from agents.energy_core import AgentEnergyCore
from agents.info_vortex import AgentInfoVortex
from agents.reality_generator import AgentRealityGenerator
from agents.cosmic_navigator import AgentCosmicNavigator
from agents.time_keeper import AgentTimeKeeper
from agents.infinite_code import AgentInfiniteCode
from agents.consciousness_vortex import AgentConsciousnessVortex
from agents.future_interface import AgentFutureInterface
from agents.global_impulse import AgentGlobalImpulse
from agents.prime_code import AgentPrimeCode
from agents.ghost import AgentGhost
from agents.exoskeleton import AgentExoskeleton
from agents.planet_control import AgentPlanetControl
from agents.time_loop import AgentTimeLoop
from agents.digital_twin import AgentDigitalTwin
from agents.media_center import AgentMediaCenter
from agents.task_manager import AgentTaskManager
from agents.vault import AgentVault
from agents.task_executor import AgentTaskExecutor
from agents.smart_home import AgentSmartHome
from agents.media_pult import AgentMediaPult
from agents.interrupt import AgentInterrupt
from agents.context_memory import AgentContextMemory
from agents.parallel_universe import AgentParallelUniverse
from agents.music_ducker import AgentMusicDucker
from agents.auto_task import AgentAutoTask
from agents.update_watcher import AgentUpdateWatcher
from agents.smart_browser import AgentSmartBrowser
from agents.browser_controller import AgentBrowserController
from agents.journal_browser import AgentJournalBrowser
from agents.focus_switch import AgentFocusSwitch
from agents.app_controller import AgentAppController
from agents.router import AgentRouter
from agents.mouse import AgentMouse
from agents.internet import AgentInternet
from agents.vision import AgentVision
from agents.system_control import AgentSystemControl
from agents.memory_registry import AgentMemoryRegistry
from agents.code_helper import AgentCodeHelper
from agents.code_autopilot import AgentCodeAutopilot
from agents.self_update import AgentSelfUpdate
from agents.auto_reboot import AgentAutoReboot
from agents.hybrid_core import AgentHybridCore
from agents.survivor import AgentSurvivor
from agents.grid import AgentGrid
from agents.post_apocalypse import AgentPostApocalypse
from agents.brain import AgentBrain
from agents.offline_first import AgentOfflineFirst
from agents.security import AgentSecurity
from agents.upgrader import AgentUpgrader
from agents.update_notifier import AgentUpdateNotifier
from agents.context import AgentContext
from agents.weather import AgentWeather
from agents.window_manager import AgentWindowManager
from agents.audio_pult import AgentAudioPult
from agents.text_editor import AgentTextEditor
from agents.vk_music import AgentVKMusic
from agents.listener import AgentListener
from agents.speaker import AgentSpeaker
from agents.rag_memory import AgentRAGMemory
from agents.journal import AgentJournal
from agents.screen_reader import AgentScreenReader
from agents.tool_router import AgentToolRouter
from agents.app_launcher import AgentAppLauncher
from agents.window_control import AgentWindowControl
from agents.browser_tabs import AgentBrowserTabs
from agents.power import AgentPower
from agents.media_search import AgentMediaSearch
from agents.barge_in import AgentBargeIn

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
# ПРОВЕРКА СЕССИИ (Wayland / X11)
# ============================================================

IS_WAYLAND = os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'
print(f"🖥️ Сессия: {'Wayland' if IS_WAYLAND else 'X11'}")

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    print("⚠️ Установите: pip install requests")

# ============================================================
# УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ДЛЯ КЛАВИШ
# ============================================================

def send_key(key):
    """Отправка клавиши - X11 и Wayland"""
    try:
        if IS_WAYLAND:
            key_map = {
                'space': '57',
                'Return': '28',
            }
            code = key_map.get(key, key)
            subprocess.run(['ydotool', 'key', code], capture_output=True, timeout=2)
        else:
            subprocess.run(['xdotool', 'key', key], capture_output=True, timeout=2)
        return True
    except:
        return False

def send_text(text):
    """Отправка текста - X11 и Wayland"""
    try:
        if IS_WAYLAND:
            subprocess.run(['ydotool', 'type', text], capture_output=True, timeout=5)
        else:
            subprocess.run(['xdotool', 'type', '--delay', '30', text], capture_output=True, timeout=5)
        return True
    except:
        return False

# ============================================================
# БАЗОВЫЙ КЛАСС МИКРО-АГЕНТА
# ============================================================

class MicroAgent:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.active = False
    
    def activate(self):
        self.active = True
        print(f"🔧 {self.name} активирован")
    
    def deactivate(self):
        self.active = False
        print(f"🔧 {self.name} деактивирован")
    
    def execute(self, input_data):
        raise NotImplementedError

# ============================================================
# ЯДРО (ОРКЕСТРАТОР)
# ============================================================

class AuraCore:
    def __init__(self):
        self.agents = {
            'listener': AgentListener(),
            'speaker': AgentSpeaker(),
            'time': AgentTimeGetter(),
            'updates': AgentUpdateChecker(),
            'upgrader': AgentUpgrader(),
            'internet': AgentInternet(),
            'vision': AgentVision(),
            'system': AgentSystemControl(),
            'functions': AgentFunctions(),
            'registry': AgentMemoryRegistry(),
            'context': AgentContext(),
            'weather': AgentWeather(),
            'window_manager': AgentWindowManager(),
            'audio_pult': AgentAudioPult(),
            'text_editor': AgentTextEditor(),
            'code_helper': AgentCodeHelper(),
            'code_autopilot': AgentCodeAutopilot(),
            'ghost': AgentGhost(),
            'exoskeleton': AgentExoskeleton(),
            'planet': AgentPlanetControl(),
            'time_loop': AgentTimeLoop(),
            'digital_twin': AgentDigitalTwin(),
            'media': AgentMediaCenter(),
            'health': AgentHealthMonitor(),
            'quantum': AgentQuantumComputer(),
            'master_key': AgentMasterKey(),
            'life': AgentLifeSimulator(),
            'mirror': AgentMirrorWorld(),
            'harmonizer': AgentHarmonizer(),
            'dream': AgentDreamArchitect(),
            'emotion': AgentEmotionalMirror(),
            'energy': AgentEnergyCore(),
            'vortex': AgentInfoVortex(),
            'reality': AgentRealityGenerator(),
            'cosmic': AgentCosmicNavigator(),
            'keeper': AgentTimeKeeper(),
            'infinite': AgentInfiniteCode(),
            'conscious': AgentConsciousnessVortex(),
            'future_ui': AgentFutureInterface(),
            'global': AgentGlobalImpulse(),
            'prime': AgentPrimeCode(),
            'vault': AgentVault(),
            'task_manager': AgentTaskManager(),
            'task_executor': AgentTaskExecutor(),
            'self_update': AgentSelfUpdate(),
            'auto_reboot': AgentAutoReboot(),
            'brain': AgentBrain(),
            'hybrid_core': AgentHybridCore(),
            'offline_first': AgentOfflineFirst(),
            'survivor': AgentSurvivor(),
            'grid': AgentGrid(),
            'post_apocalypse': AgentPostApocalypse(),
            'smart_home': AgentSmartHome(),
            'media_pult': AgentMediaPult(),
            'interrupt': AgentInterrupt(),
            'context_memory': AgentContextMemory(),
            'parallel_universe': AgentParallelUniverse(),
            'focus_switch': AgentFocusSwitch(),
            'app_controller': AgentAppController(),
            'music_ducker': AgentMusicDucker(),
            'router': AgentRouter(),
            'auto_task': AgentAutoTask(),
            'update_watcher': AgentUpdateWatcher(),
            'smart_browser': AgentSmartBrowser(),
            'browser_controller': AgentBrowserController(),
            'mouse': AgentMouse(),
            'journal_browser': AgentJournalBrowser(),
            'vk_music': AgentVKMusic(),
            'security': AgentSecurity(),
            'rag_memory': AgentRAGMemory(),
            'audio_router': AgentAudioRouter(),
            'journal': AgentJournal(),
            'screen_reader': AgentScreenReader(),
            'tool_router': AgentToolRouter(),
            'app_launcher': AgentAppLauncher(),
            'window_control': AgentWindowControl(),
            'browser_tabs': AgentBrowserTabs(),
            'power': AgentPower(),
            'media_search': AgentMediaSearch(),
            'barge_in': AgentBargeIn(),
        }

        # Регистрация инструментов для ToolRouter
        self.agents['tool_router'].register(
            "get_time", "Получить текущее время", {},
            lambda: self.agents['time'].execute(None)
        )
        self.agents['tool_router'].register(
            "get_weather", "Получить погоду в городе. Если город не указан — Москва",
            {"city": "string"},
            lambda city="Москва": self.agents['internet'].search(f"погода {city}")
        )
        self.agents['tool_router'].register(
            "search_web", "Поиск информации в интернете", {"query": "string"},
            lambda query: self.agents['internet'].search(query)
        )
        self.agents['tool_router'].register(
            "get_updates", "Проверить обновления системы", {},
            lambda: self.agents['updates'].execute(None)
        )
        self.agents['tool_router'].register(
            "list_windows", "Показать список открытых окон", {},
            lambda: self.agents['screen_reader'].get_windows()
        )
        self.agents['tool_router'].register(
            "read_screen", "Прочитать текст на экране через OCR", {},
            lambda: self.agents['screen_reader'].read_screen()
        )
        self.agents['tool_router'].register(
            "open_app", "Открыть приложение по имени (Telegram, Firefox, Steam)",
            {"name": "string"},
            lambda name: self.agents['app_launcher'].open_app(name)
        )
        self.agents['tool_router'].register(
            "close_app", "Закрыть приложение по имени", {"name": "string"},
            lambda name: self.agents['app_launcher'].close_app(name)
        )
        self.agents['tool_router'].register(
            "list_apps", "Показать список установленных приложений (можно с фильтром)",
            {"filter": "string"},
            lambda filter="": self.agents['app_launcher'].list_apps(filter)
        )
        self.agents['tool_router'].register(
            "focus_window", "Переключиться на открытое окно по имени (Firefox, Telegram, Code)",
            {"query": "string"},
            lambda query: self.agents['window_control'].focus_window(query)
        )
        self.agents['tool_router'].register(
            "close_window", "Закрыть окно по имени (не приложение, а именно окно)",
            {"query": "string"},
            lambda query: self.agents['window_control'].close_window(query)
        )
        self.agents['tool_router'].register(
            "fullscreen", "Развернуть активное окно на весь экран", {},
            lambda: self.agents['window_control'].fullscreen()
        )
        self.agents['tool_router'].register(
            "minimize_all", "Свернуть все окна (показать рабочий стол)", {},
            lambda: self.agents['window_control'].minimize_all()
        )
        self.agents['tool_router'].register(
            "list_windows_full", "Показать полный список открытых окон", {},
            lambda: self.agents['window_control'].list_windows()
        )
        self.agents['tool_router'].register(
            "list_tabs", "Показать список вкладок Firefox", {},
            lambda: self.agents['browser_tabs'].list_tabs()
        )
        self.agents['tool_router'].register(
            "focus_tab", "Переключиться на вкладку Firefox по имени",
            {"query": "string"},
            lambda query: self.agents['browser_tabs'].focus_tab(query)
        )
        self.agents['tool_router'].register(
            "close_tab", "Закрыть вкладку Firefox по имени", {"query": "string"},
            lambda query: self.agents['browser_tabs'].close_tab(query)
        )
        self.agents['tool_router'].register(
            "open_tab", "Открыть новую вкладку в Firefox по URL", {"url": "string"},
            lambda url: self.agents['browser_tabs'].open_tab(url)
        )
        self.agents['tool_router'].register(
            "search_in_firefox", "Открыть новую вкладку с поиском в Google",
            {"query": "string"},
            lambda query: self.agents['browser_tabs'].search(query)
        )
        self.agents['tool_router'].register(
            "power_off", "Выключить компьютер", {},
            lambda: self.agents['power'].shutdown()
        )
        self.agents['tool_router'].register(
            "reboot", "Перезагрузить компьютер", {},
            lambda: self.agents['power'].reboot()
        )
        self.agents['tool_router'].register(
            "suspend", "Уйти в спящий режим", {},
            lambda: self.agents['power'].suspend()
        )
        self.agents['tool_router'].register(
            "lock_screen", "Заблокировать экран", {},
            lambda: self.agents['power'].lock()
        )
        self.agents['tool_router'].register(
            "logout", "Выйти из системы", {},
            lambda: self.agents['power'].logout()
        )
        self.agents['tool_router'].register(
            "set_volume", "Установить громкость (0-100)", {"level": "integer"},
            lambda level: self.agents['audio_pult']._set_volume(int(level))
        )
        self.agents['tool_router'].register(
            "mute", "Выключить звук", {},
            lambda: self.agents['audio_pult']._mute()
        )
        self.agents['tool_router'].register(
            "unmute", "Включить звук", {},
            lambda: self.agents['audio_pult']._unmute()
        )
        self.agents['tool_router'].register(
            "play_movie", "Включить фильм по названию", {"query": "string"},
            lambda query: self.agents['media_search'].play_media(query, "movie")
        )
        self.agents['tool_router'].register(
            "play_music", "Включить песню или трек по названию", {"query": "string"},
            lambda query: self.agents['media_search'].play_media(query, "music")
        )
        self.agents['tool_router'].register(
            "list_movies", "Показать список доступных фильмов", {},
            lambda: self.agents['media_search'].list_movies()
        )
        self.agents['tool_router'].register(
            "list_music", "Показать список доступной музыки", {},
            lambda: self.agents['media_search'].list_music()
        )
        self.agents['tool_router'].register(
            "stop_media", "Остановить воспроизведение медиа", {},
            lambda: self.agents['media_search'].stop_media()
        )
        self.agents['tool_router'].register(
            "play_vk_music", "Включить музыку ВКонтакте (рекомендации)", {},
            lambda: self.agents['vk_music'].play()
        )
        self.agents['tool_router'].register(
            "search_vk_music", "Найти трек в VK по названию", {"query": "string"},
            lambda query: self.agents['vk_music'].search_track(query)
        )
        self.agents['tool_router'].register(
            "volume_up", "Сделать громче", {},
            lambda: self.agents['audio_pult']._change_volume_by(10)
        )
        self.agents['tool_router'].register(
            "volume_down", "Сделать тише", {},
            lambda: self.agents['audio_pult']._change_volume_by(-10)
        )
        self.agents['tool_router'].register(
            "open_vk", "Открыть ВКонтакте", {},
            lambda: self.agents['browser_tabs'].open_tab("https://vk.com/")
        )
        self.agents['tool_router'].register(
            "open_youtube", "Открыть YouTube", {},
            lambda: self.agents['browser_tabs'].open_tab("https://www.youtube.com/")
        )
        self.agents['tool_router'].register(
            "open_rutube", "Открыть Rutube", {},
            lambda: self.agents['browser_tabs'].open_tab("https://rutube.ru/")
        )
        self.agents['tool_router'].register(
            "open_telegram_web", "Открыть Telegram Web", {},
            lambda: self.agents['browser_tabs'].open_tab("https://web.telegram.org/")
        )
        self.agents['tool_router'].register(
            "list_functions", "Показать список функций Ауры", {},
            lambda: self.agents['functions'].execute(None)
        )
        self.agents['tool_router'].register(
            "journal_status", "Показать что делал сегодня и что осталось", {},
            lambda: self.agents['journal'].execute("что я делал")
        )
        self.agents['tool_router'].register(
            "journal_add_task", "Добавить задачу в журнал", {"task": "string"},
            lambda task: self.agents['journal'].add_task(task)
        )
        self.agents['tool_router'].register(
            "journal_pending", "Показать невыполненные задачи", {},
            lambda: self.agents['journal'].show_pending()
        )
        self.agents['tool_router'].register(
            "rag_search", "Поиск по прошлым диалогам", {"query": "string"},
            lambda query: self.agents['rag_memory'].search(query)
        )
        self.agents['tool_router'].register(
            "rag_stats", "Статистика RAG-памяти", {},
            lambda: self.agents['rag_memory'].get_stats()
        )

        self.running = True
        self.last_notification_time = time.time()

        # Показать последнюю сессию
        try:
            session = self.agents['journal'].get_last_session()
            if session and not session['is_today']:
                print(f"\n📔 Последний раз ты был {session['date']} в {session['time']}")
                if session['pending_count'] > 0:
                    print(f"📋 Осталось задач: {session['pending_count']}")
                    for task in session['pending'][:5]:
                        print(f"   • [ ] {task}")
                print()
        except Exception as e:
            print(f"⚠️ Журнал: {e}")

        # Активируем основные агенты
        self.agents['listener'].active = True
        self.agents['speaker'].active = True

        # Проверка VK при старте
        if self.agents['vk_music'].token:
            print("✅ VK Music готов (токен загружен)")
        else:
            print("⚠️ VK Music: токен не найден, проверьте vk_token.txt")

    def process(self, text):
        text_lower = text.lower().strip()

        try:
            self.agents['registry'].log("command", {"command": text})
        except:
            pass

        # ===== TOOL ROUTER (LLM сама решает) =====
        try:
            tool_result = self.agents['tool_router'].route(text)
            if tool_result:
                t = tool_result.get('type')
                response = tool_result.get('response', '')
                if t in ['tool', 'text'] and response and len(response) > 2:
                    return response
        except Exception as e:
            print(f"⚠️ ToolRouter: {e}")

        # ===== FALLBACK — AgentBrain =====
        try:
            return self.agents['brain'].execute(text)
        except Exception as e:
            return f"❌ Не расслышала: {e}"

    def run(self):
        print("\n" + "="*60)
        print("🦾 АУРА - ЯДРО v10.1 FINAL")
        print("🔴 Скажи 'Аура' для активации")
        print("📦 VK Music | 🛡️ Security | 🏠 Smart Home | 🤖 Auto")
        print("="*60)
        print(f"\n✅ {len(self.agents)} агентов загружены!\n")

        self.agents['listener'].active = True
        self.agents['speaker'].active = True

        while self.running:
            try:
                self.agents['audio_router'].check_and_route()

                # === АНТИ-ЭХО: не слушаем, пока говорим ===
                if self.agents['speaker'].is_speaking:
                    time.sleep(0.1)
                    continue

                heard = self.agents['listener'].listen(timeout=5)

                if heard:
                    if 'аура' not in heard.lower() and 'aura' not in heard.lower():
                        continue

                    print("🔔 Активация!")
                    cmd = heard.replace('аура', '').replace('aura', '').strip()

                    try:
                        subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '30%'], check=False)
                    except:
                        pass

                    if self.agents['upgrader'].waiting_for_confirmation:
                        if 'да' in cmd:
                            self.agents['upgrader'].waiting_for_confirmation = False
                            response = self.agents['upgrader'].confirm()
                        elif 'нет' in cmd or 'отмена' in cmd:
                            self.agents['upgrader'].waiting_for_confirmation = False
                            response = "⏹️ Обновление отменено."
                        else:
                            if self.agents['upgrader'].increment_attempts():
                                self.agents['upgrader'].waiting_for_confirmation = False
                                response = "⏱️ Время вышло. Обновление отменено."
                            else:
                                response = "Повторите: скажите 'да' или 'нет'."
                        print(f"🤖 {response}")
                        self.agents['speaker'].say(response)
                        continue

                    if self.agents['speaker'].aplay_process and self.agents['speaker'].aplay_process.poll() is None:
                        print("🛑 Перебиваю Ауру...")
                        self.agents['speaker'].stop_speaking()
                        continue

                    if cmd:
                        print(f"📝 Команда: {cmd}")
                        self.agents['speaker'].active = True
                        response = self.process(cmd)
                        print(f"🤖 {response}")
                        self.agents['speaker'].say(response)

                        try:
                            self.agents['rag_memory'].remember(cmd, response)
                        except Exception as e:
                            print(f"⚠️ RAG не сохранил: {e}")
                        try:
                            self.agents['journal'].log_dialog(cmd, response)
                        except Exception as e:
                            print(f"⚠️ Журнал не сохранил: {e}")

                        if self.agents['speaker'].aplay_process:
                            self.agents['speaker'].aplay_process.wait()

                        if "\n" in response:
                            time.sleep(1.5)
                        else:
                            time.sleep(0.5)
                        self.agents['speaker'].active = False

                        try:
                            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '100%'], check=False)
                        except:
                            pass
                    else:
                        print("⏳ Не расслышала команду")
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🦾 Аура: До свидания! 👋")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(0.5)

# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    aura = AuraCore()
    core = aura
    aura.run()