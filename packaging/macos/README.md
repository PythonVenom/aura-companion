# Aura для macOS

## Установка

### Homebrew (скоро)

    brew install --cask aura

### Из .app

1. Скачай `Aura.app` из Releases.
2. Перетащи в Applications.
3. Открой, разреши микрофон.

### Сборка из исходников

Требуется macOS 11+.

    git clone https://github.com/PythonVenom/aura-companion
    cd aura-companion/packaging/macos
    bash build.sh

Результат: `dist/Aura.app`.

## Что работает

- **TTS** — нативный `say -v Milena` (русский)
- **Clipboard** — `pbcopy` / `pbpaste`
- **Уведомления** — `osascript` (Notification Center)
- **Открытие файлов** — `open`
- **Микрофон** — через `ffmpeg` (avfoundation) или `sox`
- **LLM** — Ollama для macOS (Intel + Apple Silicon)

## Ограничения

- **Native messaging bridge** (Firefox) — только Linux-хост
- **KDE Connect** — только Linux
- **Целостность** — приложение нужно подписать + нотаризовать для Gatekeeper

## Наука

- PyInstaller BUNDLE (macOS)
- NSSpeechSynthesizer (Apple) — TTS
- osascript — уведомления
- codesign / notarization (Apple 2019)
- Homebrew Cask (2009)

## Roadmap

- v8.0: PyInstaller + build.sh (эта задача)
- v8.1: Homebrew Cask formula
- v8.2: Apple Silicon native + notarization
