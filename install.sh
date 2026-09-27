#!/usr/bin/env bash
# Aura installer — Arch Linux.
# Идемпотентный: повторный запуск не ломает.
#
# Использование:
#   ./install.sh              — установка
#   ./install.sh --dry-run    — показать, что будет сделано
#   ./install.sh --help       — справка

set -euo pipefail

# === Config ===
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
TONE_DIR="$PROJECT_DIR/sherpa-onnx-streaming-t-one-russian-2025-09-08"
VOICES_DIR="$PROJECT_DIR/voices"

TONE_URL="https://huggingface.co/csukuangfj/sherpa-onnx-streaming-t-one-russian-2025-09-08/resolve/main"
PIPER_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium"

SYSTEM_PACKAGES=(
    python
    python-pip
    pipewire
    pipewire-pulse
    pipewire-audio
    wireplumber
    libpulse
    playerctl
    qt6-tools
    base-devel
)

# === Args ===
# ─── Pre-install system check ───
if [ -f "aura/system_check.py" ]; then
    echo ""
    python3 -c "import sys; sys.path.insert(0, '.'); from aura.system_check import format_report; print(format_report())" 2>/dev/null || true
    echo ""
    read -p "Продолжить установку? [Y/n] " ans
    case "$ans" in
        n|N|no|NO) echo "Отменено."; exit 0 ;;
    esac
fi

DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --help|-h)
            sed -n '2,10p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Неизвестный аргумент: $arg" >&2; exit 1 ;;
    esac
done

# === Helpers ===
log()  { printf "\033[1;34m[install]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*" >&2; }
die()  { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }
run()  {
    if $DRY_RUN; then
        printf "\033[1;35m[dry-run]\033[0m %s\n" "$*"
    else
        "$@"
    fi
}

# === 1. Проверка Arch ===
[ -f /etc/arch-release ] || die "Только Arch Linux (не найден /etc/arch-release)"
command -v pacman >/dev/null || die "Не найден pacman"

log "Проект: $PROJECT_DIR"
log "Dry-run: $DRY_RUN"

# === 2. Системные пакеты ===
log "Установка системных пакетов..."
run sudo pacman -S --needed --noconfirm "${SYSTEM_PACKAGES[@]}"

# === 3. venv + зависимости Python ===
if [ ! -d "$VENV_DIR" ]; then
    log "Создаю venv..."
    run python -m venv "$VENV_DIR"
else
    log "venv уже есть — пропускаю"
fi

log "Установка Python-зависимостей..."
# shellcheck disable=SC1091
if ! $DRY_RUN; then
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip >/dev/null
    pip install -e "$PROJECT_DIR"
else
    echo "[dry-run] source $VENV_DIR/bin/activate && pip install -e $PROJECT_DIR"
fi

# === 4. Модель T-one ===
if [ ! -f "$TONE_DIR/model.onnx" ] || [ ! -f "$TONE_DIR/tokens.txt" ]; then
    log "Скачиваю модель T-one (~140 МБ)..."
    run mkdir -p "$TONE_DIR"
    run curl -L --fail "$TONE_URL/model.onnx"  -o "$TONE_DIR/model.onnx"
    run curl -L --fail "$TONE_URL/tokens.txt" -o "$TONE_DIR/tokens.txt"
else
    log "T-one уже есть — пропускаю"
fi

# === 5. Голос piper (ru_RU-irina) ===
if [ ! -f "$VOICES_DIR/ru_RU-irina-medium.onnx" ]; then
    log "Скачиваю piper voice irina (~60 МБ)..."
    run mkdir -p "$VOICES_DIR"
    run curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx"      -o "$VOICES_DIR/ru_RU-irina-medium.onnx"
    run curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx.json" -o "$VOICES_DIR/ru_RU-irina-medium.onnx.json"
else
    log "Piper voice уже есть — пропускаю"
fi

# === 6. Ollama ===
if ! command -v ollama >/dev/null; then
    warn "Ollama не установлен. Установи: sudo pacman -S ollama"
else
    log "Ollama найден"
    if ! systemctl is-active --quiet ollama; then
        log "Запускаю ollama.service..."
        run sudo systemctl enable --now ollama
    fi
fi

# === 7. systemd user unit ===
SERVICE_SRC="$PROJECT_DIR/contrib/aura.service.in"
SERVICE_DST="$HOME/.config/systemd/user/aura.service"

if [ -f "$SERVICE_SRC" ]; then
    log "Устанавливаю systemd unit..."
    run mkdir -p "$HOME/.config/systemd/user"
    if $DRY_RUN; then
        echo "[dry-run] sed s|@PROJECT_DIR@|$PROJECT_DIR|g  $SERVICE_SRC > $SERVICE_DST"
    else
        sed "s|@PROJECT_DIR@|$PROJECT_DIR|g" "$SERVICE_SRC" > "$SERVICE_DST"
        systemctl --user daemon-reload
        systemctl --user enable aura.service
    fi
else
    warn "Не найден $SERVICE_SRC — пропускаю systemd"
fi

# === 8. Итог ===
cat << FINAL

╔═══════════════════════════════════════════════════════════╗
║  Установка завершена                                      ║
╚═══════════════════════════════════════════════════════════╝

Осталось вручную:

  1. Ollama модели (только для LLM-функций):
       ollama pull qwen2.5:7b-instruct-q4_K_M   (~4.7 ГБ)
       ollama pull nomic-embed-text             (~270 МБ)

  2. VK-токен (опционально — для VK-музыки):
       echo 'ТВОЙ_ТОКЕН' > $PROJECT_DIR/vk_token.txt
       chmod 600 $PROJECT_DIR/vk_token.txt

  3. Hotkey паузы (опционально, KDE):
       System Settings → Shortcuts → Add Application → Aura Pause
       Назначить Ctrl+Alt+P или CapsLock+F8

  4. Запустить Ауру:
       systemctl --user start aura.service

  5. Смотреть логи:
       journalctl --user -u aura.service -f

  Документация: $PROJECT_DIR/README.md
  Проверка готовности: $PROJECT_DIR/docs/adr/010-definition-of-done-beta.md

FINAL
