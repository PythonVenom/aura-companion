#!/usr/bin/env bash
# #99 — Регистрация Aura native host для Chromium-браузеров.
# Chrome, Edge, Brave, Vivaldi, Opera.
set -euo pipefail

HOST_NAME="aura_bridge"
HOST_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/aura_bridge_host.py"
MANIFEST_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/chromium_extension/native_manifest.json"

log() { printf "\033[1;34m[host]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

[ -f "$HOST_SCRIPT" ] || die "Не найден $HOST_SCRIPT"
[ -x "$HOST_SCRIPT" ] || chmod +x "$HOST_SCRIPT"

# Список путей для разных Chromium-браузеров (Linux)
USER_HOME="$HOME"
declare -a TARGET_DIRS=(
    "$USER_HOME/.config/google-chrome/NativeMessagingHosts"
    "$USER_HOME/.config/chromium/NativeMessagingHosts"
    "$USER_HOME/.config/microsoft-edge/NativeMessagingHosts"
    "$USER_HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    "$USER_HOME/.config/vivaldi/NativeMessagingHosts"
    "$USER_HOME/.config/opera/NativeMessagingHosts"
)

# Готовим manifest
cat > "$MANIFEST_SRC" <<MANIFEST
{
  "name": "$HOST_NAME",
  "description": "Aura Companion bridge",
  "path": "$HOST_SCRIPT",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://REPLACE_WITH_EXTENSION_ID/"
  ]
}
MANIFEST

log "Manifest готов: $MANIFEST_SRC"
log "⚠️  После установки расширения в Chrome:"
log "   1. chrome://extensions → найти Aura Bridge → скопировать ID"
log "   2. Заменить REPLACE_WITH_EXTENSION_ID в manifest"
log "   3. Перезапустить этот скрипт"
log ""

INSTALLED=0
for dir in "${TARGET_DIRS[@]}"; do
    parent=$(dirname "$dir")
    if [ -d "$parent" ]; then
        mkdir -p "$dir"
        cp "$MANIFEST_SRC" "$dir/$HOST_NAME.json"
        log "✅ $dir"
        INSTALLED=$((INSTALLED + 1))
    fi
done

if [ "$INSTALLED" -eq 0 ]; then
    die "Не найдено ни одного Chromium-браузера в ~/.config"
fi

log ""
log "Установлено в $INSTALLED браузер(ов)"
log "Перезапусти браузер для активации."
