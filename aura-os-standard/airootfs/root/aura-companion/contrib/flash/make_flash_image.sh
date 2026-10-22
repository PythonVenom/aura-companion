#!/usr/bin/env bash
# Сборка flash-образа Aura (ADR-021 + ADR-047).
# Автоматизирует шаги 1-7 из mkarchiso-profile.txt.
set -euo pipefail

PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OVERLAY="$PROJECT/contrib/flash/overlay"
WORK="${AURA_FLASH_WORK:-$HOME/.cache/aura-flash}"
PROFILE="$WORK/profile"
OUT="$PROJECT/out"

echo "╔══════════════════════════════════════════════╗"
echo "║  Aura flash-image builder (ADR-021/047)      ║"
echo "╚══════════════════════════════════════════════╝"
echo "  Project: $PROJECT"
echo "  Work:    $WORK"
echo "  Output:  $OUT"
echo ""

# 1. Проверки
if ! command -v mkarchiso >/dev/null 2>&1; then
    echo "❌ mkarchiso не найден. Установи: sudo pacman -S archiso"
    exit 1
fi

if [ ! -d "$OVERLAY/airootfs" ]; then
    echo "❌ Overlay не найден: $OVERLAY"
    exit 1
fi

RELENG=/usr/share/archiso/configs/releng
if [ ! -d "$RELENG" ]; then
    echo "❌ releng-профиль не найден: $RELENG"
    exit 1
fi

# 2. Свежий профиль из releng
echo "→ Подготовка профиля из releng..."
rm -rf "$PROFILE"
mkdir -p "$WORK"
cp -r "$RELENG" "$PROFILE"

# 3. Overlay: добавить пакеты
echo "→ Добавление пакетов Aura..."
cat "$OVERLAY/packages.x86_64" >> "$PROFILE/packages.x86_64"

# 4. Overlay: systemd unit + wants
echo "→ Установка auto-install.service..."
cp -r "$OVERLAY/airootfs/." "$PROFILE/airootfs/"

# 5. Копия проекта (без venv/.git/pycache)
echo "→ Копирование aura_project в образ..."
mkdir -p "$PROFILE/airootfs/root/aura_project"
rsync -a --exclude='venv' --exclude='.git' --exclude='__pycache__' \
      --exclude='out' --exclude='*.pyc' \
      "$PROJECT/" "$PROFILE/airootfs/root/aura_project/"

# 6. install-aura.sh в корень образа
cp "$PROJECT/contrib/flash/install-aura.sh" "$PROFILE/airootfs/root/install-aura.sh"
chmod +x "$PROFILE/airootfs/root/install-aura.sh"

# 7. Сборка
echo "→ Сборка ISO (10-20 минут, нужен sudo)..."
mkdir -p "$OUT"
sudo mkarchiso -v -w "$WORK/mkarchiso-work" -o "$OUT" "$PROFILE"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Готово!                                      ║"
echo "╚══════════════════════════════════════════════╝"
ls -lh "$OUT"/archlinux-*.iso 2>/dev/null | tail -1
echo ""
echo "Запись на флешку:"
echo "  sudo dd if=$OUT/archlinux-*.iso of=/dev/sdX bs=4M status=progress"
