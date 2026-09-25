# Архитектура Aura

**Дата:** 2026-09-25
**Статус:** живой.
**См. также:** `manifesto.md` (философия), `migration-roadmap.md` (план), `adr/` (решения).

Это — техническая архитектура. Как Aura устроена **сейчас**, а не какой должна стать.

---

## 1. Принцип: луковичная (гексагональная) архитектура

Aura построена по принципу **гексагональной архитектуры** (Alistair Cockburn, 2005). Ядро не знает о внешнем мире. Внешний мир подключается через **порты** (контракты) и **адаптеры** (реализации).

```
┌─────────────────────────────────────────┐
│        Внешний мир (ОС, сеть, LLM)      │
└─────────────────────────────────────────┘
                  ↕ (адаптеры)
┌─────────────────────────────────────────┐
│  agents/  platform/  bridge.py          │
│  (агенты, платформа, сеть)              │
└─────────────────────────────────────────┘
                  ↕ (порты)
┌─────────────────────────────────────────┐
│              core/                       │
│  protocol.py  registry.py                │
│  orchestrator.py                         │
└─────────────────────────────────────────┘
```

**Правила:**
- Ядро (`core/`) не импортирует `agents/`, `platform/`, `bridge.py`.
- Агенты не знают друг о друге — только через `registry`.
- Платформа знает про PipeWire/DBus/KWin — ядро не знает.
- Тесты подменяют `platform` фейком.

**Источник:** Cockburn, «Hexagonal Architecture», 2005.

---

## 2. Структура пакета

```
aura_project/
├── aura/                        # основной пакет
│   ├── core/                    # ЯДРО
│   │   ├── protocol.py          # BaseAgent, AgentRequest, AgentResponse
│   │   ├── registry.py          # реестр агентов
│   │   ├── orchestrator.py      # маршрутизация запросов
│   │   └── bridge.py            # клиент Firefox bridge (length-prefix)
│   ├── agents/                  # АГЕНТЫ (26)
│   │   ├── time, power, vault, music_ducker, media_pause
│   │   ├── audio_pult, audio_router, listener, speaker, barge_in
│   │   ├── journal, rag_memory, registry, functions, updates, security
│   │   ├── vision, focus_switch, window_manager, context_memory
│   │   ├── text_editor, browser_tabs, vk_music, messenger
│   │   ├── app_launcher, window_control, screen_reader
│   │   ├── media_search, internet
│   │   └── brain, tool_router    # LLM-сервисы (не BaseAgent)
│   ├── platform/                # абстракция над ОС
│   │   └── base.py
│   ├── memory/                  # состояние, RAG
│   ├── bootstrap.py             # сборка оркестратора
│   ├── heartbeat.py             # watchdog главного цикла
│   ├── status.py                # /tmp/aura_status.json для виджета
│   └── __init__.py
├── aura_main.py                 # точка входа (главный цикл)
├── tests/                       # 645 тестов
├── docs/                        # документация
│   ├── adr/                     # ADR 001–011
│   ├── manifesto.md
│   ├── architecture.md          ← этот файл
│   ├── migration-roadmap.md
│   └── ...
├── firefox_extension/           # WebExtension + content scripts
├── contrib/                     # вспомогательное
│   ├── plasmoid-aura-status/    # KDE виджет
│   ├── backup_configs.sh
│   ├── restore_configs.sh
│   └── toggle_aura_pause.sh
├── install.sh                   # установка одной командой
├── run_aura.sh                  # запуск (без хардкода путей)
├── pyproject.toml
└── venv/
```

---

## 3. Ядро (`aura/core/`)

### protocol.py — контракты

```python
class AgentStatus(Enum):
    OK, NOT_HANDLED, ERROR

@dataclass
class AgentRequest:
    text: str

@dataclass
class AgentResponse:
    status, text, data, agent_name

class BaseAgent:
    name: str
    MODULE_NAME: str          # ADR-011
    MODULE_DESCRIPTION: str
    MODULE_REQUIRES: tuple
    MODULE_ALWAYS: bool

    def can_handle(request) -> bool
    async def handle(request) -> AgentResponse
```

**Правило:** агент не импортирует другие агенты. Только `BaseAgent` из `protocol`.

### registry.py — реестр

Линейный список агентов. Метод `find(request)` возвращает **первого**, у кого `can_handle == True`.

**Правило:** порядок регистрации важен. Специфичное — раньше общего. (См. ADR-011, урок `«найди вкладку X»` улетало в vk_music.)

### orchestrator.py — маршрутизация

Три уровня (ADR-005):

```
process(text):
    1. registry.find(request)       ← быстро, детерминированно
       если найден → handle
    2. tool_router.route(text)      ← LLM с tool-calling
    3. brain.ask(text)              ← LLM-фолбэк
```

**Правило:** 95% команд идут через реестр. LLM — только для сложных фраз.

### bridge.py — клиент Firefox

Протокол: **4 байта LE длины + JSON**. Каждый вызов — новый UNIX socket.

```python
def send_command(cmd, timeout=5.0) -> dict | None
def error_text(result) -> str
```

**Используется:** `browser_tabs`, `messenger` (DRY).

---

## 4. Агенты (`aura/agents/`)

### Категории

| Категория | Агенты |
|---|---|
| **Ядро** | time, power, vault, journal, rag_memory, registry, functions, updates, security |
| **Аудио** | audio_pult, audio_router, listener, speaker, barge_in (откл.), music_ducker, media_pause |
| **Firefox** | browser_tabs, messenger |
| **Windows** | window_manager, window_control, focus_switch, app_launcher |
| **Media** | media_search, vk_music |
| **Vision** | vision, screen_reader, mouse, text_editor |
| **Internet** | internet |
| **LLM-сервисы** | brain, tool_router |
| **Заготовки** | context_memory, media_pult, parallel_universe, task_manager |

### Модульная система (ADR-011)

Каждый агент имеет `MODULE_*` атрибуты. `bootstrap.py` читает `~/.config/aura/modules.toml` и регистрирует только включённые.

**Default:** модуль включён. Пользователь **явно выключает**.

**Пример:** `[modules]\nvk_music = false\nvision = false` → 24 агента вместо 26.

---

## 5. Голосовой цикл

```
микрофон
   ↓
listener (T-one, sherpa-onnx, streaming)
   ↓
heard → «Аура»? → cmd
   ↓
orchestrator.process(cmd)
   ↓
response (str)
   ↓
speaker.say(response) (piper + paplay)
   ↓
колонки
```

### Анти-эхо (AEC)

`echo-cancel-source` (PipeWire) как default source. AEC вычитает эхо из микрофона. **RMS: 1770 → 10** при играющей музыке.

**См.:** ADR-007.

### Ducking

`media_pause` — MPRIS pause/resume на время речи Ауры. Работает для VLC, Firefox (YouTube), mpv, Spotify.

**См.:** ADR-009 (barge-in отложен из-за WirePlumber).

### Barge-in

Код готов (`barge_in.py`), gate добавлен, **отключён** в `aura_main.py` из-за ADR-009.

---

## 6. Firefox bridge

**Два компонента:**

1. **WebExtension** (`firefox_extension/`):
   - `manifest.json` (MV2)
   - `background.js` — 15+ actions
   - `content_max.js` — content script для Макса

2. **Native messaging host** (`aura_firefox_host.py`):
   - Слушает Unix socket `/tmp/aura_firefox.sock`
   - Проксирует сообщения через stdin/stdout в Firefox

**Поток:**

```
aura_main.py → bridge.send_command()
   ↓ (Unix socket)
aura_firefox_host.py
   ↓ (stdin)
background.js (Firefox)
   ↓ (tabs.sendMessage)
content_max.js (web.max.ru)
```

**Пример:** «какие чаты в максе» → `messenger` → `max_list_chats` → 20 чатов.

---

## 7. KDE интеграция

### Виджет `org.aura.status`

QML-плазмоид. Читает `/tmp/aura_status.json` через `Plasma5Support.DataSource` (executable engine). Показывает:
- Кружок статуса (idle/listening/thinking/speaking/paused/error).
- Tooltip.
- Развёрнутую карточку с последним диалогом.

**Установка:** `contrib/plasmoid-aura-status/`.

### Hotkey паузы

`contrib/toggle_aura_pause.sh` + `.desktop`-файл. Привязка — через GUI KDE (Shortcuts → Custom Shortcuts). `CapsLock+F8`.

**Не использовать** `kwriteconfig6` в `kglobalshortcutsrc` — ломает клавиатуру.

---

## 8. Bootstrap и модули

### bootstrap.py

```python
def build_orchestrator() -> Orchestrator:
    orch = Orchestrator(tool_router=..., brain=...)
    modules_config = load_modules_config()
    _try_register(orch, AgentTime, modules_config)
    _try_register(orch, AgentPower, modules_config)
    # ... 26 агентов
    return orch
```

**Порядок регистрации важен.** Специфичное раньше (messenger до vk_music).

### modules.toml

```toml
[modules]
vk_music = false
vision = false
```

`MODULE_ALWAYS = True` — 15 критичных агентов (нельзя выключить).

---

## 9. Heartbeat (watchdog)

`aura/heartbeat.py` — daemon-поток. Проверяет `last_beat_ts`. Если `now - last > 180 сек` → `os._exit(1)`. Systemd `Restart=on-failure` поднимает.

**Что делает:** если `listener.listen()` зависнет, или LLM заблокируется — Аура перезапустится через 3 минуты.

---

## 10. Тесты

**645 тестов** в `tests/`. Покрытие:
- Каждый агент — свой тест.
- Опасные (`power`, `pactl`, `playerctl`) — mock.
- Интеграционные — `test_bootstrap.py`.
- Модульная система — `test_modules.py`.

**Инструмент:** pytest + pytest-asyncio.

**Правило:** тесты до коммита.

---

## 11. Стек

| Слой | Технология |
|---|---|
| **ОС** | Arch Linux, KDE Plasma 6 |
| **Язык** | Python 3.12 |
| **Асинхрон** | asyncio |
| **LLM** | Ollama (qwen2.5:7b), tool-calling |
| **RAG** | ChromaDB + Ollama-эмбеддинги |
| **ASR** | T-one (sherpa-onnx, streaming) |
| **TTS** | Piper (ru_RU-irina-medium) |
| **Аудио** | PipeWire + WirePlumber |
| **Браузер** | Firefox WebExtension + native messaging |
| **UI** | KDE Plasma 6 (QML) |
| **Медиа** | MPRIS (playerctl) |
| **Тесты** | pytest |

**Целевое железо:** AMD Strix Halo (Ryzen AI Max+ 395).
**Текущее:** MSI, i7 8-го, GTX 1070 8 ГБ, 32 ГБ RAM.

---

## 12. Связь с другими документами

| Документ | О чём |
|---|---|
| `manifesto.md` | Философия, принципы, видение |
| `architecture.md` | Техническая архитектура (этот файл) |
| `migration-roadmap.md` | План миграции, фазы |
| `adr/001–011` | Принятые решения |
| `JOURNAL.md` | Хроника работы |
| `context-for-new-chat.md` | Полный контекст для новых чатов |
| `ideas.md` | Идеи на будущее |
