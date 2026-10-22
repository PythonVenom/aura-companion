# Aura для Android (Termux)

Полноценный Linux-окружение на Android без root.

## Установка

### 1. F-Droid

Установи из [F-Droid](https://f-droid.org):
- **Termux**
- **Termux:API**

### 2. Одна команда

    pkg install git -y
    git clone https://github.com/PythonVenom/aura-companion
    cd aura-companion/packaging/android
    bash install_android.sh

## Что работает

- **Голосовой ввод/вывод** — Android TTS через Termux:API
- **Уведомления** — нативные Android
- **Буфер обмена** — системный
- **Открытие URL/файлов** — нативные Android intents
- **Микрофон** — через termux-microphone-record
- **LLM** — Ollama для ARM64 (если есть)

## Ограничения

- **Native messaging bridge** (Firefox) — только через десктоп-хост
- **KDE Connect** — только Linux
- **Сложные сценарии** (T047/T048 — слепые) — ограничены Android-политикой

## Наука

- Termux (termux.dev) — Linux env без root
- Termux:API — доступ к Android intents
- Android NDK (Google 2015) — ARM64 Python
- F-Droid (2010) — repo без Play Store

## Roadmap

- v8.0: install_android.sh + AndroidPlatform (эта задача)
- v8.1: Termux widget для запуска голосом
- v8.2: Aura как Android service (foreground)
