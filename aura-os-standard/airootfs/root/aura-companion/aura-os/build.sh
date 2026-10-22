#!/usr/bin/env bash
# Сборка Aura Live ISO.
# Требует: archiso (pacman -S archiso), root, ~10 ГБ свободного места.
# Наука: mkarchiso (archiso spec).

set -euo pipefail

PROFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${PROFILE_DIR}/out"
WORK_DIR="${PROFILE_DIR}/work"

log() { printf "\033[1;34m[aura-os]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

command -v mkarchiso >/dev/null || die "mkarchiso не найден. Установи: sudo pacman -S archiso"
[ "$EUID" -eq 0 ] || die "Нужны root-права (mkarchiso требует)"

log "Сборка Aura Live ISO..."
log "  Профиль: $PROFILE_DIR"
log "  Выход:   $OUT_DIR"

mkdir -p "$OUT_DIR" "$WORK_DIR"

mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"

log "Готово. ISO в $OUT_DIR"
ls -lh "$OUT_DIR"/*.iso
