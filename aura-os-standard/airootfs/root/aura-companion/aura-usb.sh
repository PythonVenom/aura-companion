#!/usr/bin/env bash
# Д42 — Aura USB: сделать флешку portable.
# Использование:
#   ./aura-usb.sh /mnt/usb
#   ./aura-usb.sh /mnt/usb --download-models  # скачать ollama модели
set -euo pipefail

USB_PATH="${1:-}"
[ -z "$USB_PATH" ] && { echo "❌ Укажи путь: ./aura-usb.sh /mnt/usb" >&2; exit 1; }
[ ! -d "$USB_PATH" ] && { echo "❌ Папка не существует: $USB_PATH" >&2; exit 1; }

DOWNLOAD_MODELS=false
[ "${2:-}" = "--download-models" ] && DOWNLOAD_MODELS=true

log() { printf "\033[1;34m[usb]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

# Проверка места: 20 ГБ минимум
AVAIL_GB=$(df -BG "$USB_PATH" 2>/dev/null | awk 'NR==2 {gsub("G",""); print $4}')
if [ -n "$AVAIL_GB" ] && [ "$AVAIL_GB" -lt 20 ]; then
    die "Мало места: ${AVAIL_GB} ГБ (нужно ≥20)"
fi

log "Создаю структуру Aura на $USB_PATH"
mkdir -p "$USB_PATH/aura-project" \
         "$USB_PATH/aura-cache" \
         "$USB_PATH/aura-config" \
         "$USB_PATH/aura-models"

# Копируем проект (если запущен из репо)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$REPO_DIR/aura_main.py" ]; then
    log "Копирую проект из $REPO_DIR"
    rsync -a --exclude='.git' --exclude='venv' --exclude='__pycache__' \
          --exclude='.pytest_cache' --exclude='build' \
          "$REPO_DIR/" "$USB_PATH/aura-project/"
else
    log "Клонирую из GitHub"
    git clone --depth=1 \
        https://github.com/PythonVenom/aura-companion.git \
        "$USB_PATH/aura-project"
fi

# Опционально: скачать модели ollama
if $DOWNLOAD_MODELS && command -v ollama >/dev/null; then
    log "Скачиваю модели ollama"
    OLLAMA_MODELS="$USB_PATH/aura-models" ollama pull qwen2.5:7b-instruct-q4_K_M || \
        log "⚠️ ollama pull упал — пропускаю"
fi

# Готовим README на флешке
cat > "$USB_PATH/README-PORTABLE.txt" << 'TXT'
╔══════════════════════════════════════════════════════╗
║  Aura Portable — вставь в любой Linux-ПК и запусти   ║
╚══════════════════════════════════════════════════════╝

Запуск:
  cd <USB_PATH>
  ./aura-project/install_universal.sh --portable "$(pwd)"

Или напрямую:
  AURA_PROJECT_DIR="$(pwd)/aura-project" \
  AURA_CACHE_DIR="$(pwd)/aura-cache" \
  AURA_CONFIG_DIR="$(pwd)/aura-config" \
  python3 aura-project/aura_main.py

Все данные (профиль, ключи, RAG, логи) — на флешке.
При смене ПК — просто переставь флешку.
TXT

log "Готово: $USB_PATH"
log "Данные: $USB_PATH/README-PORTABLE.txt"
