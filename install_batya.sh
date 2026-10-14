#!/usr/bin/env bash
# Установщик Aura для бати (elder-care).
# Без LLM. Минимум действий. Автостарт.
set -euo pipefail

log()  { printf "\033[1;34m[батя]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[ошибка]\033[0m %s\n" "$*" >&2; exit 1; }

# 1. Проверка ОС
[ -f /etc/os-release ] || die "Не Linux"
. /etc/os-release
log "ОС: ${NAME:-unknown}"

# 2. Пути
AURA_DIR="$HOME/aura"
VENV="$AURA_DIR/venv"

# 3. Определить пакетный менеджер
if command -v pacman >/dev/null; then
    PKG="pacman"
elif command -v apt >/dev/null; then
    PKG="apt"
elif command -v dnf >/dev/null; then
    PKG="dnf"
else
    die "Неизвестный пакетный менеджер"
fi
log "Пакетный менеджер: $PKG"

# 4. Системные пакеты (минимальный набор)
log "Установка системных зависимостей..."
case "$PKG" in
    pacman)
        sudo pacman -S --needed --noconfirm \
            python python-pip git curl \
            pipewire pipewire-pulse pipewire-audio wireplumber \
            libpulse playerctl vlc ffmpeg portaudio \
            espeak-ng at-spi2-core python-gobject \
            tesseract tesseract-data-rus grim
        ;;
    apt)
        sudo apt update
        sudo apt install -y python3 python3-venv python3-pip git curl \
            pipewire pipewire-pulse wireplumber \
            pulseaudio-utils playerctl vlc ffmpeg portaudio19-dev \
            espeak-ng at-spi2-core python3-gi \
            tesseract-ocr tesseract-ocr-rus grim
        ;;
    dnf)
        sudo dnf install -y python3 python3-pip git curl \
            pipewire pipewire-pulseaudio wireplumber \
            pulseaudio-utils playerctl vlc ffmpeg portaudio-devel \
            espeak-ng at-spi2-core python3-gobject \
            tesseract tesseract-langpack-rus grim
        ;;
esac

# 5. Клонирование/копирование проекта
if [ ! -d "$AURA_DIR" ]; then
    log "Клонирую Aura в $AURA_DIR"
    if [ -f "$(dirname "$0")/aura_main.py" ]; then
        # Локальный запуск (из репо)
        mkdir -p "$AURA_DIR"
        rsync -a --exclude='.git' --exclude='venv' \
              --exclude='__pycache__' --exclude='.pytest_cache' \
              "$(dirname "$0")/" "$AURA_DIR/"
    else
        git clone --depth=1 \
            https://github.com/PythonVenom/aura-companion.git "$AURA_DIR"
    fi
fi

# 6. venv + зависимости
if [ ! -d "$VENV" ]; then
    log "Создаю venv..."
    python3 -m venv "$VENV"
fi
log "Установка Python-зависимостей..."
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -e "$AURA_DIR" >/dev/null

# 7. Piper голос (скачать)
VOICES_DIR="$AURA_DIR/voices"
mkdir -p "$VOICES_DIR"
if [ ! -f "$VOICES_DIR/ru_RU-irina-medium.onnx" ]; then
    log "Скачиваю голос Ирины (~63 МБ)..."
    PIPER_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium"
    curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx" -o "$VOICES_DIR/ru_RU-irina-medium.onnx"
    curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx.json" -o "$VOICES_DIR/ru_RU-irina-medium.onnx.json"
fi

# 8. Профиль elder (без LLM)
mkdir -p "$HOME/.config/aura"
cat > "$HOME/.config/aura/settings.json" <<JSON
{
  "profile": "elder",
  "capability_profile": "elder",
  "tts_voice": "ru_RU-irina-medium",
  "tts_speed": 0.9,
  "volume": 100,
  "voice_volume_boost": 1.2,
  "notifications": true,
  "proactive_enabled": true,
  "language": "ru",
  "barge_in": true,
  "min_turn_silence": 2.0
}
JSON
log "Профиль elder активирован (LLM отключён)"

# 9. systemd unit
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/aura.service" <<SVC
[Unit]
Description=Aura Companion (батя)
After=pipewire.service

[Service]
Type=simple
WorkingDirectory=$AURA_DIR
Environment="AURA_PROFILE=elder"
Environment="AURA_BRAIN=0"
ExecStart=$VENV/bin/python $AURA_DIR/aura_main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
SVC

systemctl --user daemon-reload
systemctl --user enable aura.service
systemctl --user start aura.service

# 10. Готово
cat << FINAL

╔══════════════════════════════════════════════════════╗
║  ✅ Aura установлена для бати                        ║
╚══════════════════════════════════════════════════════╝

Батя, скажи громко:

  🗣️  «Аура, привет!»

Если не отвечает — позвони сыну.

Логи:      journalctl --user -u aura.service -f
Перезапуск: systemctl --user restart aura.service
Стоп:      systemctl --user stop aura.service

Полная инструкция: docs/INSTALL-ELDER.md
FINAL
