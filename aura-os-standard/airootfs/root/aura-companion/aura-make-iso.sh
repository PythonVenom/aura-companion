#!/usr/bin/env bash
# Д42 Фаза 2 — Aura Live ISO builder (безопасный).
# Собирает ISO, НЕ пишет на флешку (dd делает юзер сам).
# Использование:
#   ./aura-make-iso.sh           # собрать Live ISO
#   ./aura-make-iso.sh --help
set -euo pipefail

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \?//'
}

for arg in "$@"; do
    case "$arg" in
        --help|-h) usage; exit 0 ;;
        *) echo "❌ Неизвестный аргумент: $arg" >&2; usage >&2; exit 1 ;;
    esac
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="$REPO/aura-os"

log()  { printf "\033[1;34m[iso]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[error]\033[0m %s\n" "$*" >&2; exit 1; }

# 1. Проверки
command -v mkarchiso >/dev/null || die "mkarchiso не найден: sudo pacman -S archiso"
[ -f "$PROFILE_DIR/build.sh" ] || die "aura-os/build.sh не найден"
[ -f "$PROFILE_DIR/profiledef.sh" ] || die "profiledef.sh не найден"

# 2. Предупреждения
log "Сборка Aura Live ISO"
log "  Профиль: $PROFILE_DIR"
log "  Требует: root, ~10 ГБ, 15-30 мин"
log ""
log "⚠️  Писать на флешку НЕ будем (защита от dd)."
log "   После сборки — команда будет показана."
log ""

# 3. Сборка (нужен sudo)
if [ "$EUID" -ne 0 ]; then
    log "Запускаю с sudo..."
    exec sudo "$0" "$@"
fi

cd "$PROFILE_DIR"
bash ./build.sh

# 4. Ищем свежий ISO
ISO_FILE=$(ls -t "$PROFILE_DIR/out/"*.iso 2>/dev/null | head -1)
if [ -z "$ISO_FILE" ]; then
    die "ISO не найден после сборки"
fi

ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)

# 5. Показываем команду для dd (юзер выполняет сам)
cat << FINAL

╔══════════════════════════════════════════════════════╗
║  ✅ ISO готов: $ISO_FILE
║  📦 Размер: $ISO_SIZE
╚══════════════════════════════════════════════════════╝

Записать на флешку (САМ, ОСТОРОЖНО!):

  1. Вставь флешку
  2. Найди её: lsblk
  3. Запиши (ЗАМЕНИ /dev/sdX!):

     sudo dd if="$ISO_FILE" of=/dev/sdX bs=4M status=progress oflag=sync

  ⚠️  Ошибка в /dev/sdX = стёртая система.
     Проверь ДВАЖДЫ (размер, модель).

Загрузиться: BIOS → F12 → флешка → Aura Live через 30 сек.
FINAL
