# Установка Ауры — для разработчиков

## Требования

- Python 3.11+
- git
- Микрофон + динамики
- ~5 ГБ (модели)
- Опционально: Ollama, VLC, Firefox

## Ручная установка

Шаг 1. Клонировать:

    git clone https://github.com/PythonVenom/aura-companion ~/aura_project
    cd ~/aura_project
    python -m venv venv
    source venv/bin/activate
    pip install -e .

Шаг 2. Системные пакеты:

Arch:

    sudo pacman -S python pipewire pipewire-pulse pipewire-audio         wireplumber libpulse playerctl qt6-tools portaudio

Ubuntu:

    sudo apt install python3.12 python3-venv python3-pip         pipewire pipewire-pulse pipewire-audio wireplumber         pulseaudio-utils playerctl vlc portaudio19-dev libsndfile1

Шаг 3. Модели (T-one + Piper) — см. install.sh

Шаг 4. systemd:

    mkdir -p ~/.config/systemd/user
    sed "s|@PROJECT_DIR@|$(pwd)|g" contrib/aura.service.in         > ~/.config/systemd/user/aura.service
    systemctl --user daemon-reload
    systemctl --user enable --now aura.service

## PAL

См. docs/adr/017-platform-abstraction.md

## Тесты

    pytest tests/ -v
