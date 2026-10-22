# Установка Aura Companion

Aura — локальный голосовой помощник для доступности.
Работает без облака. Данные не покидают устройство.

## Быстрая установка

| Платформа | Команда |
|---|---|
| Arch Linux | ./install.sh |
| Ubuntu / Debian / Astra | ./install_ubuntu.sh |
| Fedora | ./install_fedora.sh |
| Alpine | ./install_alpine.sh |
| Universal Linux | ./install_universal.sh |
| WSL | ./install_wsl.sh |
| macOS | ./install_macos.sh |
| Windows (PS) | .\install_windows.ps1 |
| Android (Termux) | ./install_android.sh |
| ARM (RPi, Pine64) | ./install_arm.sh |
| Arch ARM | ./install_arch_arm.sh |

## Что нужно

Linux: pipewire, python 3.10+, 8 ГБ ОЗУ, 4 ГБ диска.
Windows: WSL2 + Ubuntu.
macOS: Homebrew, Python 3.10+.
Android: Termux из F-Droid.

TTS/ASR:
- speech-dispatcher + espeak-ng — голос
- Vosk-model-small-ru — распознавание (~50 MB, автоскачивание)

## После установки

source venv/bin/activate
python -m aura
aura --help

## Проверка

aura doctor
aura health

## Проблемы

Нет звука — sudo pacman -S pipewire pipewire-pulse
Не слышит — arecord -l
CI красный — pytest -q

См. docs/troubleshooting.md.
