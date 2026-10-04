# Changelog

## v2.5.0 — 2026-10-02 (Опора)

### Added
- CareAgent — напоминания (вода, еда, сон) — ADR-085
- VoiceJournal — дневник настроения — ADR-086
- Hands-Free Mode — голос без «Аура» — ADR-095
- Context Memory — «что делал 10 мин назад» — ADR-096
- Focus Mode — не отвлекать N минут — ADR-097
- ADR-093 Copilot Mode, ADR-094 Behavior Tree

### Tests
- 1255 → 1266 passed (+11)

## v2.0.0 — 2026-10-02

### Added
- Wake-word (openWakeWord) — ADR-083
- HTTP API FastAPI (localhost:8765) — ADR-079
- Web UI (universal HTML+JS, работает везде) — ADR-080
- SNI tray (pystray, 90% DE) — ADR-081
- GNOME Shell Extension — contrib/gnome-extension
- Cinnamon Applet — contrib/cinnamon-applet
- XFCE genmon plugin — contrib/xfce-plugin
- Logbook (бортовой журнал) — ADR-084
- Plugin System (manifest + manager + CLI + adapter) — ADR-090
- Egress Broker (whitelist + filter + budget) — ADR-091
- AgentDeepSeek plugin (DeepSeek API) — ADR-088
- Astra Linux adapter + ADR-092

### Changed
- bootstrap: плагины загружаются с префиксом `plugin_`
- aura_plugin CLI (list/install/remove/info)

### Fixed
- test_bootstrap: фильтр плагинов из core-порядка

### Tests
- 1205 → 1239 passed (+34)

## v1.1.0 — 2026-10-02

### Added
- KDE Plasma widget (org.aura.status): статус-кружок, 4 кнопки управления (Pause/Restart/Stop/Kill)
- Emergency row в виджете: PANIC, Mute mic, Unmute mic
- Чат с Aura прямо в виджете (TextField + история, file-based IPC)
- aura_ctl CLI: 9 подкоманд (pause, resume, restart, stop, kill, panic, mute, unmute, status)
- ChatBridge + ChatWatcher: file-based IPC через JSONL (ADR-069)
- VoiceGate: VAD webrtcvad перед ASR (Bug 72, ADR-075)
- Recon subsystem: структурированный сбор диагностики через .tasks файлы (ADR-068)
- ADR-067 Widget Control Panel, ADR-068 Recon, ADR-069 Chat Bridge, ADR-074 Bug 68, ADR-075 VAD, ADR-076 Emergency

### Fixed
- Bug 66 (partial): ASR num_threads 2→1, CPU 44%→19%
- Bug 69: hotkey pause flag path /tmp → ~/.cache/aura
- Bug 70: QML status path /tmp → ~/.cache/aura
- Bug 71: pause flag path в toggle_aura_pause.sh
- Bug 72: ASR ловил фоновую речь (VAD-гейт)
- Bug 73: chat latency 8 сек → 2 сек (drain queue до/после listen)

### Changed
- listener.listen timeout 8 → 2 сек в главном цикле (Bug 73)
- Plasma 6 widget: config.qml через KCM.SimpleKCM

### Tests
- 1144 → 1185 passed

## v1.0.0 — 2026-09-28

- Первый стабильный релиз. Beachhead MVP 100%.
- 1144 теста, 49 ADR, 37 агентов, CI + Release green.
