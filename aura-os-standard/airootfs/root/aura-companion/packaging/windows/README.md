# Aura для Windows

## Установка (готовый билд)

1. Скачай `aura-setup.exe` из [Releases](../../releases).
2. Запусти, следуй инструкциям.
3. Aura в трее + автозагрузка.

## Сборка из исходников

Требуется:
- Windows 10/11
- Python 3.10+ ([python.org](https://python.org))
- PowerShell 7

    git clone https://github.com/PythonVenom/aura-companion
    cd aura-companion\packaging\windows
    powershell -ExecutionPolicy Bypass -File build.ps1

Результат: `dist\aura\aura.exe`.

## Что работает на Windows

- **Голосовой ввод/вывод** — через Windows Speech API (SAPI)
- **TTS** — через SAPI (встроенный в Windows)
- **LLM** — Ollama для Windows
- **Уведомления** — Toast notifications
- **Автозагрузка** — через реестр
- **Трей** — pystray + PIL

## Ограничения

- **Native messaging bridge** — Firefox не поддерживает native messaging на Windows в текущей версии Aura. Требуется WSL2 с Linux-хостом.
- **KDE Connect** — только Linux.
- **Умный дом** — через HomeAssistant (нужен HA сервер).

## Наука

- PyInstaller (PyInstaller docs)
- Windows Speech API (Microsoft SAPI 5.4)
- MSI/WiX (Microsoft, для installer)
- Registry autostart (Microsoft, CurrentVersion\Run)

## Roadmap

- v8.0: PyInstaller spec + PowerShell build (эта задача)
- v8.1: MSI installer (WiX)
- v8.2: Store версия (Microsoft Partner Center)
