# Архитектура Aura

## Обзор

Микрофон → T-one (ASR) → Orchestrator + FSM → Registry (27) → agents → Piper TTS → Динамики

## Слои

### 1. Input (голос)
- listener.py — T-one streaming ASR
- barge_in.py — VAD

### 2. Orchestrator
- aura_main.py — главный цикл
- dialog_fsm.py — FSM (idle / awaiting_command / pending_read / awaiting_reply)
- dialogue_manager.py — сценарии (ADR-013)

### 3. Routing
- aura/core/registry.py — реестр агентов
- tool_router.py — роутинг LLM
- brain.py — LLM (Ollama)

### 4. Agents (27)
Голос: listener, speaker, barge_in, music_ducker
Управление: power, window_manager, app_launcher, focus_switch
Медиа: music_local, vk_music, vk_web, media_pause, media_search
Общение: messenger, telegram
Proactive: ChatSense, calendar, checklist
Система: registry, updates, security, vault, journal

### 5. Platform Abstraction Layer (ADR-017)
- aura/platform/base.py — Protocol
- aura/platform/linux.py — PipeWire + systemd + MPRIS
- aura/platform/ubuntu.py — fallback
- windows.py, macos.py — заглушки

### 6. Bridge (Firefox)
- aura_firefox_host.py — native messaging
- firefox_extension/*.js — content scripts

### 7. Output (голос)
- speaker.py — Piper TTS (вечный воркер)

## State-файлы (/tmp)

- aura_fsm.json — FSM
- aura_media_state.json — last_active плеер
- aura_proactive.json — cooldown триггеров
- aura_calendar.json — события
- aura_chat_sense.json — reminded-чаты
- aura_status.json — UI-статус

## ADR (19)

001-019: см. docs/adr/

## Документация

- README.md / README.en.md
- MANIFESTO.md
- PARTNERSHIP.md
- docs/architecture.md
- docs/install-advanced.md
