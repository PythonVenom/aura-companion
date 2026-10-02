# Changelog

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
