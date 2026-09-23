#!/usr/bin/env bash
# Aura backup — собирает ключевые конфиги и проект в архив.
#
# Что попадает:
#   - ~/aura_project/  (без venv и моделей)
#   - ~/.config/systemd/user/aura.service
#   - ~/.config/pipewire/pipewire-pulse.conf.d/
#   - ~/.local/state/wireplumber/default-nodes
#   - ~/.config/kglobalshortcutsrc
#   - ~/.local/share/applications/aura-pause.desktop
#   - ~/.local/share/plasma/plasmoids/org.aura.status/
#
# Что НЕ попадает (можно восстановить):
#   - venv/                 — pip install -e .
#   - sherpa-onnx-*/        — install.sh скачает
#   - voices/               — install.sh скачает
#   - ~/.ollama/            — ollama pull
#
# Использование:
#   ./contrib/backup_configs.sh              # архив в ~/
#   ./contrib/backup_configs.sh /mnt/disk    # архив на внешний диск

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${1:-$HOME}"
STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="$DEST_DIR/aura_backup_${STAMP}.tar.gz"

log() { printf "\033[1;34m[backup]\033[0m %s\n" "$*"; }

log "Проект: $PROJECT_DIR"
log "Архив:  $ARCHIVE"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# 1. Код проекта (без venv и моделей)
log "Копирую проект..."
mkdir -p "$TMP_DIR/aura_project"
rsync -a \
    --exclude='venv/' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='sherpa-onnx-*/' \
    --exclude='voices/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    "$PROJECT_DIR/" "$TMP_DIR/aura_project/"

# 2. Конфиги вне проекта
log "Копирую конфиги..."
mkdir -p "$TMP_DIR/home_config/systemd_user"
mkdir -p "$TMP_DIR/home_config/pipewire"
mkdir -p "$TMP_DIR/home_config/wireplumber"
mkdir -p "$TMP_DIR/home_config/applications"
mkdir -p "$TMP_DIR/home_config/plasma_plasmoids"

[ -f "$HOME/.config/systemd/user/aura.service" ] && \
    cp "$HOME/.config/systemd/user/aura.service" "$TMP_DIR/home_config/systemd_user/"
[ -d "$HOME/.config/pipewire/pipewire-pulse.conf.d" ] && \
    cp -r "$HOME/.config/pipewire/pipewire-pulse.conf.d" "$TMP_DIR/home_config/pipewire/"
[ -f "$HOME/.local/state/wireplumber/default-nodes" ] && \
    cp "$HOME/.local/state/wireplumber/default-nodes" "$TMP_DIR/home_config/wireplumber/"
[ -f "$HOME/.config/kglobalshortcutsrc" ] && \
    cp "$HOME/.config/kglobalshortcutsrc" "$TMP_DIR/home_config/"
[ -f "$HOME/.local/share/applications/aura-pause.desktop" ] && \
    cp "$HOME/.local/share/applications/aura-pause.desktop" "$TMP_DIR/home_config/applications/"
[ -d "$HOME/.local/share/plasma/plasmoids/org.aura.status" ] && \
    cp -r "$HOME/.local/share/plasma/plasmoids/org.aura.status" "$TMP_DIR/home_config/plasma_plasmoids/"

# 3. Метаданные
log "Собираю метаданные..."
{
    echo "Дата: $(date)"
    echo "Host: $(hostname)"
    echo "User: $USER"
    echo "Проект: $PROJECT_DIR"
    echo "git: $(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
} > "$TMP_DIR/BACKUP_INFO.txt"

# 4. Архив
log "Создаю архив..."
tar -czf "$ARCHIVE" -C "$TMP_DIR" .

SIZE="$(du -h "$ARCHIVE" | cut -f1)"
log "Готово: $ARCHIVE ($SIZE)"
log ""
log "Восстановить: ./contrib/restore_configs.sh $ARCHIVE"
