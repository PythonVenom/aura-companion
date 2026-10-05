#!/usr/bin/env bash
# Aura macOS — сборка .app.
# Наука: PyInstaller BUNDLE, codesign, Homebrew.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${HERE}/../.." && pwd)"
VENV="${ROOT}/.venv-macos"

log() { printf "\033[1;34m[aura-mac]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 не найден"
command -v brew >/dev/null || log "Homebrew не найден (опционально)"

[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

log "Устанавливаю зависимости..."
pip install --upgrade pip
pip install pyinstaller
pip install -e "$ROOT"

log "Сборка .app..."
cd "$HERE"
pyinstaller --clean --noconfirm aura.spec

APP="${HERE}/dist/Aura.app"
if [ -d "$APP" ]; then
    log "Готово: $APP"
    log "Открой: open '$APP'"
    log "Code sign (если есть Apple Developer ID):"
    log "  codesign --deep --force --sign 'Developer ID Application' '$APP'"
else
    die "Сборка не удалась."
fi
