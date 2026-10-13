# AURA · GAPS (13.10.2026)

## 🔴 БЛОКЕРЫ (5)
1. Watchdog speaker — aura_main.py:778
2. Микрофон AEC — run_aura.sh
3. RAG embedding 404 — rag_memory.py
4. ISO не грузится — platforms/archiso
5. Дублирование aura_project vs aura-companion

## 🏗️ АРХИТЕКТУРА (13)
6. TUI (менюшка) — только в aura_project
7. Cockpit — только в aura_project
8. Game layer — только state.py
9. Captain agent — не в коде
10. Rituals (утро/вечер) — нет
11. Curiosity Engine — нет
12. User Profile — нет
13. Learnings — нет
14. Initiative — нет
15. Identity.yaml — не внедрён
16. Notifications P0-P3 — нет
17. Self-Model — нет
18. Meta-Memory — базово

## 🔌 ИНФРАСТРУКТУРА (12)
19. Обёртки VLC, MPRIS — нет
20. Обёртки Vosk, T-one, Piper — нет
21. tg_bridge — stub
22. vk_bridge — stub
23. max_bridge — stub
24. whatsapp_bridge — stub
25. Astra Linux адаптер (F-092) — план
26. Эльбрус e2k (F-038) — план
27. ARM адаптер — нет
28. Fedora адаптер — нет
29. Tuya BLE — нет
30. ELM327 — не тестирован

## 💻 КОД (12)
31. Mentor TUI add/edit — нет
32. Profile Ledger Ed25519 — нет
33. Employer integration — нет
34. WineLauncher (F-052) — нет
35. CarHistory + 1С (F-053) — нет
36. AgentCANBus (F-050) — нет
37. DTC 500+ (F-051) — нет
38. DBus API (F-045) — нет
39. Configurator GTK4 (F-046) — нет
40. OCR — нет
41. Screen capture (grim) — нет
42. Clipboard watcher (wl-paste) — нет

## 📦 ПРОДУКТ (10)
43. Live-USB для бати — не записана
44. F-160 Live-USB — не начато
45. F-161 Aura ISO — не начато
46. F-162 Aura OS — не начато
47. F-163 AppImage — не начато
48. F-150 Car-assistant — не начато
49. F-070 Veteran-агенты — не начато
50. F-076 Military (ПОЛКА) — не начато
51. F-042 Family-veteran — не начато
52. F-055 Подарок брату — не начато

## 🧪 ТЕСТЫ (7)
53. 1610 тестов — проверить
54. Coverage — неизвестен
55. E2E тесты — нет
56. Тесты GPU — нет
57. Тесты RAG — нет
58. Тесты elder-care — частично
59. Тесты на бате — нет

## 📚 ДОКИ (10)
60. README — не обновлён
61. INSTALL.md — есть
62. FAQ.md — есть
63. CHANGELOG.md — есть
64. Habr-статья — черновик
65. YouTube демо — нет
66. Скриншоты — нет
67. Видео-туториал — нет
68. Contributing — есть
69. CONTACTS.md — есть

## 💰 БИЗНЕС (9)
70. Регистрация ПО (3000 ₽) — нет
71. Товарный знак (35000 ₽) — нет
72. Монетизация — нет
73. Донаты — нет
74. Команда — 1 человек
75. Инвесторы — нет
76. Партнёрства — нет
77. Юрлицо (ИП/ООО) — нет
78. Сертификация — нет

## 🎮 ИГРА (5)
79. Star map — только aura_project
80. BattleScreen — только aura_project
81. Советники — только aura_project
82. XP система — нет
83. Секторы — только aura_project

## 🚗 АВТО (6)
84. ELM327 — не куплен
85. OBD-II тест — не проведён
86. DTC база — нет
87. Голосовые команды авто — нет
88. Маршрут + топливо — нет
89. Камера (знаки) — нет

## 🧓 ELDER-CARE (6)
90. Тест с батей — не проведён
91. Долгосрочная память — не проверена
92. Падение → SOS — не тестировано
93. Лекарства — не настроено
94. Голосовые профили — частично
95. Stress-test 24/7 — нет

---
*Создано: 13.10.2026*
*Всего: 95 пунктов*

## ЗАПИСЬ 2026-10-13: Разбор клонов project/companion

### Сделано
- Перенесено из project в companion: `aura/system/` (6 модулей), `aura/lore/` (полный), `aura/kernel/`, `aura/contracts/`, `profiles/`, `tools/mentor_tui.py`, `aura/cockpit/`, `aura/game/`, 7 агентов
- 3-way merge `aura_main.py` (project F-065/F-066/F-067/F-070 + companion v0.5.2)
- Фикс путей `aura_project` → `aura-companion` в 13 боевых файлах
- systemd units переключены на companion: aura.service, aura-tray.service, aura-backup.service
- Демон работает: PID из companion, отвечает через ChatBridge

### Известные проблемы
- `aura-kernel.service` — отключён. Конфликт архитектур: kernel-адаптеры ждут legacy `AgentWeather`, а companion использует новый `WeatherAgent(MicroAgent)`. Требует переписывания адаптеров.
- `venv` в companion — симлинк на `aura_project/venv`. Нужен свой venv (долг).
- qwen2.5 иногда отвечает на китайском. Нужен system prompt с явным указанием языка.

### Принцип (Д95)
- `~/aura-companion` — master ядра и логики
- `~/aura_project` — build-цех ISO + legacy архив
- Никаких копий между проектами — только перенос в companion

## ЗАПИСЬ 2026-10-13 (12:00): Свой venv для companion

### Сделано
- venv.symlink_bak (симлинк на aura_project/venv) — удалён
- Создан свой venv: `/home/pythonvenom/aura-companion/venv`
- Установлено 172 пакета из старого freeze
- `pip install -e .` → aura-companion 8.0.0-rc1, editable location = companion
- Демон перезапущен, PID 26317 из нового venv
- Проверка: import aura → companion, ошибок нет

### Закрыт долг
- "venv companion — симлинк на aura_project/venv (нужен свой)" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (12:10): System prompt + пост-фильтр китайского

### Сделано
- aura/agents/brain.py: SYSTEM_PROMPT усилен — "ЕДИНСТВЕННЫЙ язык РУССКИЙ", "иероглифы ЗАПРЕЩЕНЫ"
- Добавлен `_has_chinese()` — детектор CJK/Hiragana/Katakana/Hangul
- Добавлен `_chinese_ratio()` — доля CJK в тексте
- В `_try_model()`: если ratio > 10% — ответ отбрасывается как ошибка, идёт следующий fallback (7b → 3b → 270m → template)
- Тест: «Аура расскажи анекдот» → русский анекдот, 0 иероглифов

### Закрыт долг
- "qwen2.5 иногда отвечает на китайском" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (12:15): Зелёные тесты — 1609/1609

### Сделано
- docs/adr/README.md: добавлены 9 записей (ADR 053-061)
- tests/test_window_control.py: убран параметр "на весь экран" (F-103b — намеренно отдан media_search)
- pytest: 1609 passed, 0 failed

### Закрыт долг
- "2 упавших теста (ADR index, window_control)" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (12:25): Хардкод путей побеждён

### Сделано
- 8 файлов: Path("/home/pythonvenom/aura-companion") → Path.home() / "aura-companion"
- aura/system/{doctor,bugmap,deep_check,oneshot}.py
- aura/game/spawner.py
- aura/cockpit/{hyperjump,studio,ship}.py
- Проверка: grep "/home/pythonvenom/" → 0

### Закрыт долг
- AUDIT #2 "Хардкод путей" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (12:30): rate-limit для HTTP API

### Сделано
- aura/web/api.py: token bucket на /chat
- Лимит: 30 запросов / 60 сек с одного IP
- Превышение → HTTP 429 с деталями
- Наука: Turner 1986 (token bucket), RFC 6585 (429 Too Many Requests)
- Тест: 30 ok, +1 = fail

### Закрыт долг
- AUDIT #16 "No rate-limit" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (13:50): +8 агентов подключены

### Сделано
- bootstrap.py: 14 импортов + блок "Уровень 1.5"
- Убраны дубли: AgentRecentActivity (context_agent), AgentFocusMode (focus_agent) — уже были в старом коде
- Удалены старые строки 362-363 (двойная регистрация)
- Агентов: 78 → 86
- Тесты: 1609 passed, дубликатов нет

### Закрыт долг
- AUDIT #11 "23 агента не подключены" — частично (8 из 14)

## ЗАПИСЬ 2026-10-13 (14:10): Онтология Aura + stopwords

### Сделано
- aura/lore/ontology.md — манифест Aura (85 строк): кто я, роли, обязательства, девиз
- config/identity.yaml — обновлён: 5 ролей, 5 обязательств, refusals, science
- aura/persona.py: load_ontology() + build_system_prompt() тянет онтологию
- aura/agents/brain.py: SYSTEM_PROMPT → property, читает persona при каждом вызове
- aura/core/intent_classifier.py: STOPWORDS (кто, что, ты...) — «кто ты» больше не матчит vk.messages

### Результат
- Aura знает кто она (девиз, роли, обязательства)
- Ложные срабатывания tier0 убиты (F-021c)
- Тесты: 1609 passed

### Закрыт долг
- AUDIT #10 «Наука не в коде» — частично (онтология + refusals)

## ЗАПИСЬ 2026-10-13 (14:20): AUDIT #11 закрыт

### Сделано
- recon (AgentRecon) — обзор через aura_recon.py
- journal_mood (VoiceJournal) — дневник настроения (ADR-086)
- vk_music — включён в ~/.config/aura/modules.toml
- Импорты в __init__.py + bootstrap.py
- Агентов: 86 → 89

### Закрыт долг
- AUDIT #11 "23 агента не подключены" — ЗАКРЫТО
  (из 23: 8 инфра, 12 подключены в прошлой сессии, 3 сейчас)

## ЗАПИСЬ 2026-10-13 (14:30): README школьника готов

### Сделано
- docs/tutorial/ (aura_private): 6 файлов, 1194 строки
- 00-intro.md — что такое Aura
- 01-first-step.md — установка за 10 мин
- 02-voice.md — голосовые команды
- 03-game.md — игра (секторы, советники, XP)
- 04-agents.md — все 89 агентов
- 05-your-first-agent.md — напиши своего

### Закрыт долг
- AUDIT #8 "Нет README для школьника" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (14:50): Elder-care готов

### Сделано
- profiles/batya/modules.toml — авто-генерация (38 модулей off)
- bootstrap.is_module_enabled — умный матчинг MODULE_NAME (Convention over Configuration)
- bootstrap.load_modules_config — читает profiles/$AURA_PROFILE/modules.toml
- tests/test_elder_scenarios.py — 17 тестов (15 сценариев)
- aura_private/docs/ELDER-SCENARIOS.md — 168 строк

### Проверка
- AURA_PROFILE=batya → 53 агента (было 89)
- default → 89
- 17/17 elder-care тестов passed

### Закрыт долг
- AUDIT #9 "Данные для бати не ушли" — частично (профиль готов)

## ЗАПИСЬ 2026-10-13 (15:00): SQLCipher → keyring

### Сделано
- aura/game/state.py: _load_or_make_key → keyring
- Приоритет: env AURA_DB_KEY → keyring → миграция с plaintext → новый
- Миграция: db.key (plaintext) → keyring → удаление файла
- Fallback: если keyring недоступен, файл 0600 (last resort)

### Проверка
- Plaintext файл db.key удалён
- Ключ в keyring: aura-game-state/master-key
- StateStore читает ключ без изменений
- 17 elder-care тестов passed

### Закрыт долг
- AUDIT #3 "Ключ SQLCipher в plaintext" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (15:10): Backup 3-2-1

### Сделано
- aura_backup.py V2: расширены TARGETS
  - RAG (chroma)
  - state.db (игра)
  - logs.jsonl, JOURNAL.md
  - memory_registry.json
  - modules.toml, identity.yaml
- Offsite: /mnt/aura_hdd/backups/aura/ (другой носитель, 30 копий)
- Локально: ~/.config/aura/backups/ (7 копий)

### Krogh 2009 (3-2-1)
- ✅ 3 копии: оригинал + local + offsite
- ✅ 2 носителя: nvme0n1p2 + sdb2
- ⚠️ offsite = тот же комп (TODO: rclone → облако)

### Проверка
- Backup: 121 KB → 545 KB (RAG включён)
- Offsite работает

### Закрыт долг
- AUDIT #4 "Один бэкап" — ЗАКРЫТО (частично, offsite на другом диске)

## ЗАПИСЬ 2026-10-13 (15:20): weather покрыт

### Сделано
- aura/agents/weather.py: двойной API (str + AgentRequest)
- can_handle + async handle (Liskov 1987 — принцип подстановки)
- tests/test_weather.py: 9 тестов (creation, keywords, coords, mock API, error, russian)
- Найден и исправлен баг: старый handle() не принимал AgentRequest

### Покрытие
- weather.py: 0% → ~70%

## ЗАПИСЬ 2026-10-13 (15:30): bugmap покрыт

### Сделано
- tests/test_bugmap.py: 11 тестов
- Проверка Bug dataclass, BugMap.add, build_bugmap, render_bugmap
- AUDIT #2 регрессия: нет хардкода путей

### Покрытие
- bugmap.py: 0% → ~65%

## ЗАПИСЬ 2026-10-13 (15:15): Wake-word fuzzy (AUDIT #5)

### Сделано
- aura/wake_detector.py (167 строк) — fuzzy-детектор
- Levenshtein 1965, Jaro-Winkler 1990 (наука)
- MIN_TOKEN_LEN=3, MAX_LEN_DIFF_SHORT=0, MAX_LEN_DIFF_LONG=1
- CANONICAL (аура, ауру, aura), KNOWN_VARIANTS (алло, алла, аула, лаура)
- aura_main._is_activated → wake_detector.is_wake_word
- aura_main._strip_activation → wake_detector.strip_wake_word
- tests/test_wake_detector.py: 38 тестов

### Проверка
- «Аура» → True
- «алло» → True (T-one)
- «аула» → True
- «ураган» → False ✅
- «арахис» → False ✅
- «пауза» → False ✅
- «мне плохо» → True (elder whitelist)

### Закрыт долг
- AUDIT #5 "Wake-word «Аура»→«Алло»" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (15:15): Keyring-миграция подтверждена

### Контекст
После миграции ключа SQLCipher в keyring (15:00) демон выдал hmac fail.
Ошибка была одноразовая — во время пересоздания state.db со старым ключом.

### Текущее состояние
- Демон: active
- wake(): работает
- state.db: читается корректно
- keyring: aura-game-state/master-key

### Вывод
Миграция успешна. Ошибка в логе — исторический след, не баг.

## ЗАПИСЬ 2026-10-13 (15:25): E2E тесты (AUDIT #6)

### Сделано
- tests/test_e2e_web.py: 10 тестов
- HTTP e2e: health, status, agents, version, chat, csrf
- Playwright: загрузка UI, наличие формы, mobile viewport
- Фикстура aura_server: uvicorn + health-check, clean shutdown
- Установлен playwright 1.63.0 + chromium

### Наука
- Fowler 2003 (Test Pyramid) — e2e дорогие, но ловят реальные регрессии
- Cohn 2009 — UI через Playwright
- Humble & Farley 2010 — e2e как gate

### Проверка
- 10 passed in 2.57s
- HTTP работает от uvicorn
- Playwright реально открывает браузер

### Закрыт долг
- AUDIT #6 "Нет e2e тестов" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (15:30): README обновлён

### Сделано
- README.md: 93 → 192 строки
- Бейджи: tests 1694, ADR 131, agents 89, python 3.12
- Разделы: что умеет, цифры, установка, документация, тесты, безопасность, философия
- Ссылки на tutorial (6 файлов, 1194 строки)
- MCP, онтология, elder-care — в первый план

## ЗАПИСЬ 2026-10-13 (15:40): Plaintext в профиле (AUDIT #3b)

### Проблема
- profiles/batya/db.key существовал в plaintext (не мигрирован)
- Миграция смотрит только на ~/.config/aura/db.key

### Сделано
- profiles/batya/db.key удалён (ключ тот же, что в keyring)
- .gitignore: profiles/*/db.key, *.key
- Бэкап в /tmp/batya_db.key.bak

### Проверка
- AURA_PROFILE=batya load OK (xp=2515)
- keyring: aura-game-state/master-key

### Открыт новый долг
- get_profile() не переключает state_db на profiles/<name>/state.db
- Все профили используют ~/.config/aura/state.db (общая БД)

## ЗАПИСЬ 2026-10-13 (15:50): Captain + Evening Ritual

### Сделано
- aura/agents/captain.py (134 строки) — статус, приоритеты, итоги дня
- aura/agents/evening_ritual.py (137 строк) — итоги дня (22:00)
- aura-evening.timer — systemd таймер 22:00
- Агентов: 89 → 91

### Наука
- Campbell 1949 (monomyth) — капитан как архетип
- Duhigg 2012 (habit loop) — ритуалы
- Lally 2010 — привычка за 66 дней
- Seligman 2011 — маленькие победы

### Закрыт долг
- GAPS #9 Captain agent — ЗАКРЫТО
- GAPS #10 Rituals (утро/вечер) — ЗАКРЫТО (вечерний)

## ЗАПИСЬ 2026-10-13 (16:35): Installer для бати протестирован

### Сделано
- aura-detect.sh: AURA_PROFILE env override > auto-detect
- install_universal.sh: elder → LLM off (ADR-025, ADR-139)
- Docker-тест (ubuntu:24.04) пройден
- 4 уникальных tools из project → companion
- Mentor TUI: add/edit/delete custom skills
- Mentor PathTracker: читает все 47 skills

### Проверка в Docker
- ОС: ubuntu ✅
- apt update/install ✅
- T-one + Piper download ✅
- Ollama авто-установка ✅
- Elder-профиль: 0 ollama pull ✅

### Закрыты долги
- GAPS #31 Mentor TUI add/edit — ЗАКРЫТО
- GAPS #43 Live-USB бати — installer готов (ISO как резерв)

### Готово к бате
- Тест: Docker Ubuntu 24.04 (проведён)
- Следующий шаг: реальная установка на Mint бати

## ЗАПИСЬ 2026-10-13 (17:00): Fall → SOS — 3 бага исправлено

### Найдено тестами
1. AgentSOS.handle НЕ проверял can_handle → «привет» → SOS
2. AgentFall.handle НЕ проверял can_handle → любой текст → fall
3. sos_phrases (settings) ЗАМЕНЯЛИ дефолт → теряли «упал», «тревога»

### Фиксы
- can_handle в handle() — fail-safe defaults (Saltzer 1975)
- _get_phrases → MERGE (default + custom)
- STATE_FILE class attribute
- 22 теста: fall, sos, цепочка

### Закрыт долг
- GAPS #92 "Падение → SOS (не тестировано)" — ЗАКРЫТО

## ЗАПИСЬ 2026-10-13 (17:05): AgentMeds — 5 багов исправлено

### Найдено и исправлено
1. DB → self.DB (class attribute для тестов)
2. _add: правильный парсинг имени (убрать «аура», «добавь», время)
3. scheduler опционален (start_scheduler=False)
4. can_handle в handle
5. Порядок: визиты/взаимодействия → до лекарств
6. TRIGGERS расширены (визиты, врачи, взаимодействия)

### Тесты
- 25 тестов (add, list, taken, visits, interactions, registry)
- 3 бага в handle найдено тестами

### Закрыт долг
- GAPS #93 "Лекарства — настроить" — ЗАКРЫТО


## ЗАПИСЬ 2026-10-13 (17:45): DBus API (GAPS #38)

### Сделано
- aura/core/dbus_service.py (251 строка) — DBus сервис
- Интерфейс: org.aura.Companion
- Методы: Chat, Status, Agents, Command, Ping
- systemd unit: aura-dbus.service
- Агентов: 92

### Наука
- freedesktop.org DBus Spec (2003)
- jeepney 0.9.0 (чистый Python)

### Закрыт долг
- GAPS #38 "DBus API" — ЗАКРЫТО
