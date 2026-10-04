#!/usr/bin/env bash
# Aura universal installer — Debian/Ubuntu/Fedora/Arch/Alpine/macOS
# Использование:
#   curl -fsSL https://raw.githubusercontent.com/PythonVenom/aura-companion/master/install_universal.sh | bash
#   ./install_universal.sh --dry-run
#   ./install_universal.sh --help
set -euo pipefail

PROJECT_DIR="${AURA_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
VENV_DIR="$PROJECT_DIR/venv"
TONE_DIR="$PROJECT_DIR/sherpa-onnx-streaming-t-one-russian-2025-09-08"
VOICES_DIR="$PROJECT_DIR/voices"

TONE_URL="https://huggingface.co/csukuangfj/sherpa-onnx-streaming-t-one-russian-2025-09-08/resolve/main"
PIPER_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium"

DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --help|-h) sed -n '2,10p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *) echo "Неизвестный аргумент: $arg" >&2; exit 1 ;;
    esac
done

log()  { printf "\033[1;34m[install]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*" >&2; }
die()  { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }
run()  { if $DRY_RUN; then echo "[dry-run] $*"; else "$@"; fi; }

# === 1. Determine OS ===
if [ -f /etc/os-release ]; then . /etc/os-release; fi
OS="${ID:-unknown}"
case "$OS" in
    ubuntu|debian|linuxmint|pop) PKG="apt" ;;
    fedora|rhel|centos) PKG="dnf" ;;
    arch|manjaro|endeavouros) PKG="pacman" ;;
    alpine) PKG="apk" ;;
    *) PKG="unknown" ;;
esac
[ "$(uname -s)" = "Darwin" ] && PKG="brew"

log "ОС: $OS, пакетный менеджер: $PKG"

# === 2. Auto-detect hardware ===
[ -f "$PROJECT_DIR/contrib/aura-detect.sh" ] && . "$PROJECT_DIR/contrib/aura-detect.sh"

log "RAM: ${AURA_RAM_GB:-?} ГБ, CPU: ${AURA_CPU_CORES:-?} ядер, профиль: ${AURA_PROFILE:-medium}"

# === 3. Choose LLM model by profile ===
case "${AURA_PROFILE:-medium}" in
    minimal) LLM_MODEL=""; log "Профиль minimal: LLM отключён (AURA_BRAIN=0)" ;;
    low)     LLM_MODEL="qwen2.5:3b" ;;
    medium)  LLM_MODEL="qwen2.5:7b-instruct-q4_K_M" ;;
    full)    LLM_MODEL="qwen2.5:7b-instruct-q4_K_M" ;;
esac

# === 4. System packages ===
install_pkgs() {
    case "$PKG" in
        apt)    run sudo apt update
                run sudo apt install -y python3 python3-venv python3-pip git curl \
                    pipewire pipewire-pulse pipewire-audio wireplumber \
                    pulseaudio-utils playerctl vlc ffmpeg portaudio19-dev libsndfile1 ;;
        dnf)    run sudo dnf install -y python3 python3-pip git curl \
                    pipewire pipewire-pulseaudio wireplumber \
                    pulseaudio-utils playerctl vlc ffmpeg portaudio-devel ;;
        pacman) run sudo pacman -S --needed --noconfirm python python-pip git curl \
                    pipewire pipewire-pulse pipewire-audio wireplumber \
                    libpulse playerctl vlc ffmpeg portaudio ;;
        apk)    run sudo apk add --no-cache python3 py3-pip git curl \
                    pipewire pipewire-pulse wireplumber \
                    pulseaudio-utils playerctl vlc ffmpeg py3-virtualenv py3-numpy ;;
        brew)   run brew install python@3.12 git ffmpeg portaudio ;;
        *)      die "Неподдерживаемый дистрибутив" ;;
    esac
}
log "Установка системных пакетов..."
install_pkgs

# === 5. venv + deps ===
if [ ! -d "$VENV_DIR" ]; then
    log "Создаю venv..."
    run python3 -m venv "$VENV_DIR"
fi
log "Установка Python-зависимостей..."
if ! $DRY_RUN; then
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip >/dev/null
    pip install -e "$PROJECT_DIR"
fi

# === 6. T-one ===
if [ ! -f "$TONE_DIR/model.onnx" ]; then
    log "Скачиваю T-one (~144 МБ)..."
    run mkdir -p "$TONE_DIR"
    run curl -L --fail "$TONE_URL/model.onnx"  -o "$TONE_DIR/model.onnx"
    run curl -L --fail "$TONE_URL/tokens.txt" -o "$TONE_DIR/tokens.txt"
fi

# === 7. Piper voice ===
if [ ! -f "$VOICES_DIR/ru_RU-irina-medium.onnx" ]; then
    log "Скачиваю Piper voice (~63 МБ)..."
    run mkdir -p "$VOICES_DIR"
    run curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx"      -o "$VOICES_DIR/ru_RU-irina-medium.onnx"
    run curl -L --fail "$PIPER_URL/ru_RU-irina-medium.onnx.json" -o "$VOICES_DIR/ru_RU-irina-medium.onnx.json"
fi

# === 8. Ollama ===
if [ -n "${LLM_MODEL:-}" ]; then
    if ! command -v ollama >/dev/null; then
        warn "Ollama не установлен. Установи вручную: https://ollama.com/download"
    else
        log "Загружаю модель: $LLM_MODEL"
        run ollama pull "$LLM_MODEL" || warn "ollama pull failed — сделай вручную"
        run ollama pull nomic-embed-text || true
    fi
fi

# === 9. systemd unit (Linux only) ===
if [ "$(uname -s)" = "Linux" ] && [ -f "$PROJECT_DIR/contrib/aura.service.in" ]; then
    log "Устанавливаю systemd unit..."
    run mkdir -p "$HOME/.config/systemd/user"
    if ! $DRY_RUN; then
        sed "s|@PROJECT_DIR@|$PROJECT_DIR|g" "$PROJECT_DIR/contrib/aura.service.in" \
            > "$HOME/.config/systemd/user/aura.service"
        # Drop-in для профиля
        mkdir -p "$HOME/.config/systemd/user/aura.service.d"
        cat > "$HOME/.config/systemd/user/aura.service.d/profile.conf" <<CONF
[Service]
Environment="AURA_PROFILE=${AURA_PROFILE:-medium}"
Environment="AURA_RAM_GB=${AURA_RAM_GB:-8}"
CONF
        if [ "${AURA_PROFILE:-}" = "minimal" ]; then
            cat > "$HOME/.config/systemd/user/aura.service.d/brain-off.conf" <<CONF
[Service]
Environment="AURA_BRAIN=0"
CONF
        fi
        systemctl --user daemon-reload
        systemctl --user enable aura.service
    fi
fi

# === 10. Готово ===
cat << FINAL

╔══════════════════════════════════════════════╗
║  Установка Aura завершена                    ║
╚══════════════════════════════════════════════╝

Профиль железа: ${AURA_PROFILE:-unknown}
RAM: ${AURA_RAM_GB:-?} ГБ, CPU: ${AURA_CPU_CORES:-?} ядер
LLM модель: ${LLM_MODEL:-отключена}

Запустить:        systemctl --user start aura.service
Логи:             journalctl --user -u aura.service -f
Проверка:         source venv/bin/activate && python -m aura.config_wizard

FINAL
