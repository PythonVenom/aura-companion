# Changelog

Все заметные изменения проекта Aura.

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Phases
- Фаза 13.4.1: детект всех чатов (Bug 2+3+4)
- Фаза 13.5: pending_read + awaiting_reply (Bug 1, 15)
- Фаза 13.6: ChatSense (неотвеченные, события, календарь)
- Фаза 13.7: AgentChecklist (голосовой чек-лист)
- Фаза 17: Platform Abstraction Layer (ADR-017)
- Фаза 17.1: VK Web + Telegram Web адаптеры (ADR-018)
- Фаза 17.2: Installation Experience (ADR-019)
- Фаза 18: media_state (единый пульт VLC/VK/MPRIS)

### Added
- VK Web адаптер (навигация: лента, сообщения, друзья, группы, музыка, видео)
- Telegram Web адаптер (list_chats, find_chat, open)
- AgentChecklist — голосовой чек-лист
- ChatSense — неотвеченные + парсинг событий + календарь
- media_state — помним последний активный плеер (VLC/VK/MPRIS)
- AT-SPI, MCP адаптеры (заготовки для Фаз 21-27)
- Platform Abstraction Layer (ADR-017)
- Site Adapters ADR-018
- 24-часовой прогон стабильности

### Fixed
- Bug 6: pending_read «да/нет» до сброса по «аура»
- Bug 7: finalize_send для Svelte (execCommand + полный Enter)
- Bug 8: chat до 3 слов в DM
- Bug 9: дубликат триггера (MAX меняет preview)
- Bug 10: speaker race + echo-cancel sink (троение)
- Bug 11: таймаут pending_read 60 → 180 сек
- Bug 12: LLM болтает после FSM
- Bug 13: свои сообщения не триггерят
- Bug 14: музыка помнит последний плеер (base, ph.2, ph.3, ph.4)
- Bug 15: контекст ответа в Максе (awaiting_reply)

### Tests
- 700 → 815+ passed

## [0.9.6] — 2026-09-28

### Добавлено
- **aura/wrappers/**: слой Wrappers (ADR-037)
  - base.py: AppWrapper ABC + WrapperError
  - grbl.py: GRBL 1.1 wrapper (ЧПУ, serial, whitelist)
  - registry.py: WrapperRegistry + autoload (graceful)
- CLI: `aura wrappers list|status`
- tests/test_wrappers_base.py (13 регрессионных)

## [0.9.5] — 2026-09-28

### Добавлено
- docs/professions.md: каталог 110+ профессий в 5 кластерах
- **ADR-037** Third-party API Wrappers (Blender, PS, DAW, ЧПУ)
- **ADR-038** Hardware Roadmap (Lite/Standard/Pro/Distributed)
- **ADR-039** Distributed Aura (federation, mDNS, CRDT)
- CLI: `aura agents`, `aura professions`
- tests/test_cli_agents.py (2)
- tests/test_orch_unique_names.py (4) — регрессия на dupes

### Исправлено
- **Bug 20**: 33→34 агента (collision names в registry)

## [0.9.4] — 2026-09-28

### Добавлено
- strategy-2026.md: 5 кластеров профессий + 30+ примеров
- ADR-036 Creative & Craftsman Vertical (5 агентов-кластеров)
- docs/adr/README.md + 036

### Концепция
- Aura выигрывает там, где **руки заняты** (не «удобнее», а единственный способ)
- 5 агентов на 30+ профессий (YAGNI)

## [0.9.3] — 2026-09-28

### Добавлено
- **ADR-032** JSON-RPC Protocol (транспорт, методы, ошибки, mTLS)
- **ADR-033** Bookkeeping Vertical (бухгалтеры, 5 млн РФ)
- **ADR-034** Smart Home (MQTT, Zigbee2MQTT, без облака)
- **ADR-035** Roadmap 2026 (формализация)
- **aura/doctor.py**: 8-пунктовая диагностика
- **CLI**: `aura doctor`, `aura adr`
- tests/test_doctor.py (4)
- tests/test_adr_index.py (4) — doc-test консистентности

## [0.9.2] — 2026-09-28

### Добавлено
- docs/strategy-2026.md: 11 вертикалов, roadmap, Pareto
- ADR-031 Ethics Policy (Reject List: слежка, биржа, диагнозы)
- MANIFESTO.md: раздел «Что Aura не делает»
- aura/nlp.py: adaptive max_dist (0/1/2 по длине)
- power.py: ASR-устойчивость (Bug 17)
- proactive.py: time_fired + health_due (Bug 19)
- cli.py: aura timer / reminder / timers / reminders

### Исправлено
- **Bug 18**: tests/conftest.py guard от опасных subprocess
  (systemctl/loginctl/poweroff/reboot — RuntimeError без мока)
- **Bug 17**: "выключит" / "перезагружу" распознаются (fuzzy)

### Изменено
- bootstrap: 34 агента (time_agent, health)

## [0.9.1] — 2026-09-28

### Добавлено
- TimeAgent: таймеры + будильники (AgentTimeAgent)
- HealthAgent: напоминания о лекарствах/воде/перерывах (AgentHealth)
- aura/nlp.py: fuzzy_match (Levenshtein ≤2) для ASR
- config_wizard: 5 вопросов (имя/ты-вы/характер/юмор/голос)
- settings: persona в DEFAULTS (name/address/style/humor/voice_gender)
- ADR-024 Android Deployment
- ADR-025 Aura Lite (512 МБ RAM)
- ADR-026 Medical Module (проект)
- ADR-027 TimeAgent
- ADR-028 Licensing Strategy
- ADR-029 Multi-client architecture
- ADR-030 Developer Mode (проект)

### Исправлено
- **power.py**: confirm для shutdown/reboot/logout/hibernate (Bug fix)
- settings.load(): deepcopy DEFAULTS (изоляция между тестами)

### Изменено
- bootstrap: 32 → 34 агента (time_agent, health)

## [0.9.0-alpha] — 2026-09-27

### Added
- Первый публичный релиз
- 26 агентов, 700 тестов, 16 ADR
- Голосовой цикл: активация, FSM, диалог
- Firefox bridge: вкладки, Макс (чтение + отправка)
- Локальная музыка (VLC + MPRIS)
- Proactive engine: morning_briefing, max_new_message
- MIT лицензия, GitHub public

[Unreleased]: https://github.com/PythonVenom/aura-companion/compare/v0.9.0-alpha...HEAD
[0.9.0-alpha]: https://github.com/PythonVenom/aura-companion/releases/tag/v0.9.0-alpha
