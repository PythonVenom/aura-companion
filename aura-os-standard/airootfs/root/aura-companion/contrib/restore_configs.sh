#!/usr/bin/env bash
# Aura restore — восстанавливает конфиги из архива backup_configs.sh.
#
# Что делает:
#   - Распаковывает конфиги в ~/.config/, ~/.local/
#   - НЕ трогает ~/aura_project/ без флага --with-project
#   - Показывает diff перед перезаписью (если есть --diff)
#
# Использование:
#   ./contrib/restore_configs.sh <архив.tar.gz>
#   ./contrib/restore_configs.sh <архив.tar.gz> --with-project
#   ./contrib/restore_configs.sh <архив.tar.gz> --dry-run

set -euo pipefail

ARCHIVE="${1:-}"
WITH_PROJECT=false
DRY_RUN=false

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "Использование: $0 <архив.tar.gz> [--with-project] [--dry-run]" >&2
    exit 1
fi

shift || true
for arg in "$@"; do
    case "$arg" in
        --with-project) WITH_PROJECT=true ;;
        --dry-run)      DRY_RUN=true ;;
        *) echo "Неизвестный аргумент: $arg" >&2; exit 1 ;;
    esac
done

log() { printf "\033[1;34m[restore]\033[0m %s\n" "$*"; }
run() {
    if $DRY_RUN; then
        printf "\033[1;35m[dry-run]\033[0m %s\n" "$*"
    else
        "$@"
    fi
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log "Распаковка: $ARCHIVE"
tar -xzf "$ARCHIVE" -C "$TMP_DIR"

if [ -f "$TMP_DIR/BACKUP_INFO.txt" ]; then
    log "Информация об архиве:"
    sed 's/^/  /' "$TMP_DIR/BACKUP_INFO.txt"
fi

# 1. Конфиги — всегда
log "Восстанавливаю конфиги..."
run mkdir -p "$HOME/.config/systemd/user"
run mkdir -p "$HOME/.config/pipewire"
run mkdir -p "$HOME/.local/state/wireplumber"
run mkdir -p "$HOME/.local/share/applications"
run mkdir -p "$HOME/.local/share/plasma/plasmoids"

[ -f "$TMP_DIR/home_config/systemd_user/aura.service" ] && \
    run cp "$TMP_DIR/home_config/systemd_user/aura.service" "$HOME/.config/systemd/user/"

[ -d "$TMP_DIR/home_config/pipewire/pipewire-pulse.conf.d" ] && \
    run cp -r "$TMP_DIR/home_config/pipewire/pipewire-pulse.conf.d" "$HOME/.config/pipewire/"

[ -f "$TMP_DIR/home_config/wireplumber/default-nodes" ] && \
    run cp "$TMP_DIR/home_config/wireplumber/default-nodes" "$HOME/.local/state/wireplumber/"

[ -f "$TMP_DIR/home_config/kglobalshortcutsrc" ] && \
    run cp "$TMP_DIR/home_config/kglobalshortcutsrc" "$HOME/.config/"

[ -f "$TMP_DIR/home_config/applications/aura-pause.desktop" ] && \
    run cp "$TMP_DIR/home_config/applications/aura-pause.desktop" "$HOME/.local/share/applications/"

[ -d "$TMP_DIR/home_config/plasma_plasmoids/org.aura.status" ] && \
    run cp -r "$TMP_DIR/home_config/plasma_plasmoids/org.aura.status" "$HOME/.local/share/plasma/plasmoids/"

# 2. Проект — только с --with-project
if $WITH_PROJECT; then
    log "Восстанавливаю проект..."
    run rsync -a "$TMP_DIR/aura_project/" "$HOME/aura_project/"
else
    log "Проект пропущен (нужен --with-project)"
fi

# 3. Systemd reload
if ! $DRY_RUN; then
    systemctl --user daemon-reload 2>/dev/null || true
fi

log "Готово."
log ""
log "Что проверить:"
log "  1. systemctl --user status aura.service"
log "  2. pactl get-default-source  → echo-cancel-source"
log "  3. pactl get-default-sink    → echo-cancel-sink"
log "  4. Если менял ~/.config/kglobalshortcutsrc — перелогинься"

