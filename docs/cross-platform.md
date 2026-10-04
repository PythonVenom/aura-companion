# Cross-platform Aura

## Поддерживаемые платформы

| Платформа | Статус | Пакет | Установщик |
|---|---|---|---|
| Arch Linux | Production | pacman | install.sh |
| Ubuntu/Debian | Beta | apt | install_ubuntu.sh |
| Fedora/RHEL | Планируется | dnf | TBD |
| Windows 10+ | Alpha | choco/winget | install_windows.ps1 |
| macOS 12+ | Alpha | brew | install_macos.sh |
| Android (Termux) | Alpha | pkg | install_android.sh |

## Platform Abstraction Layer (ADR-017)

Все платформо-зависимые операции через PAL:

    aura/platform/
    ├── base.py       Protocol интерфейсы
    ├── linux.py      PipeWire + systemd + MPRIS
    ├── ubuntu.py     PipeWire/PulseAudio fallback
    ├── windows.py    WASAPI + WinAPI
    ├── macos.py      CoreAudio + AppleScript
    └── __init__.py   автовыбор

## Матрица фич по ОС

| Фича | Linux | Ubuntu | Windows | macOS | Android |
|---|---|---|---|---|---|
| Голосовой цикл | ✅ | ✅ | 🟡 | 🟡 | 🟡 |
| T-one ASR | ✅ | ✅ | ✅ | ✅ | 🟡 |
| Piper TTS | ✅ | ✅ | ✅ | ✅ | 🟡 |
| Ollama LLM | ✅ | ✅ | ✅ | ✅ | ❌ |
| Music (VLC) | ✅ | ✅ | 🟡 | 🟡 | ❌ |
| Firefox bridge | ✅ | ✅ | ✅ | ✅ | ❌ |
| systemd/launchd | ✅ | ✅ | 🟡 | ✅ | ❌ |
| MPRIS | ✅ | ✅ | ❌ | ❌ | ❌ |

## Roadmap портов

### Фаза 20.1 — Arch до 100% (текущая)
- 24/7 стабильность
- Polish UX

### Фаза 20.2 — Ubuntu/Debian (Q1 2027)
- install_ubuntu.sh
- PulseAudio fallback

### Фаза 21 — Windows (Q2 2027)
- WASAPI через pycaw
- WinAPI автозапуск

### Фаза 22 — Android (Q3 2027)
- Termux
- termux-api для TTS

### Фаза 23 — macOS (Q4 2027)
- CoreAudio через sounddevice
- AppleScript уведомления

## Fedora / RHEL / CentOS

Установщик: `./install_fedora.sh`

Пакеты: python3.12, pipewire, wireplumber, vlc, portaudio-devel.
Дистрибутив определяется через `/etc/os-release` (ID=fedora, rhel, centos).

## Alpine Linux

Установщик: `./install_alpine.sh`

Пакеты: py3-pip, py3-virtualenv, pipewire, vlc.
Особенность: musl libc — некоторые пакеты (например chromadb) могут требовать дополнительной сборки.

## ARM64 (Raspberry Pi 4/5)

Установщик: `./install_arm.sh` — автоопределяет дистрибутив.

Ограничения:
- LLM работает на CPU без GPU ускорения
- 7B модель влезает в 8 ГБ RAM
- Piper/T-one работают нормально

## WSL2 (Windows Subsystem for Linux)

Установщик: `./install_wsl.sh`

Требования:
- Windows 11 (для WSLg — GUI + микрофон)
- WSL 2.0+ с systemd (в `/etc/wsl.conf`: `systemd=true`)

Ограничения:
- Firefox bridge — только в Windows-браузере (не в Linux-браузере WSL)
- Уведомления через Windows (не Linux)
