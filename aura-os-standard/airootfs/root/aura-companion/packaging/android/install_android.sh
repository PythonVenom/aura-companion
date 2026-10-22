#!/data/data/com.termux/files/usr/bin/bash
# Aura для Android (Termux).
# Наука: Termux (termux.dev), Termux:API, F-Droid, ARM64.
#
# Установка:
#   1. F-Droid → Termux + Termux:API
#   2. termux-setup-storage
#   3. bash install_android.sh

set -euo pipefail

log() { printf "\033[1;34m[aura-android]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

[ -d "/data/data/com.termux" ] || die "Не Termux. Установи из F-Droid."

if [ ! -d "$HOME/storage" ]; then
    log "Запрашиваю доступ к хранилищу..."
    termux-setup-storage || true
    sleep 2
fi

log "Обновляю pkg..."
pkg update -y && pkg upgrade -y

log "Устанавливаю базовые зависимости..."
pkg install -y \
    python python-pip git clang make rust binutils \
    openssl libffi libsndfile pulseaudio

log "Устанавливаю Termux:API..."
pkg install -y termux-api

pkg install -y espeak-ng || log "espeak-ng не установился — используем termux-tts-speak"

AURA_DIR="$HOME/aura-companion"
if [ ! -d "$AURA_DIR" ]; then
    log "Клонирую Aura..."
    git clone https://github.com/PythonVenom/aura-companion "$AURA_DIR"
fi
cd "$AURA_DIR"

log "Создаю venv..."
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .

log "Проверка..."
python -c "import aura; print('Aura OK')" || die "Aura не импортируется"

log "Готово. Запуск: source venv/bin/activate && python -m aura"
log "TTS: termux-tts-speak 'привет'"
log "Уведомления: termux-notification --title Aura --content 'тест'"
