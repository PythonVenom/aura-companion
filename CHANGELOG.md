# Changelog

Все заметные изменения проекта Aura.

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).
Версионирование: [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

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
