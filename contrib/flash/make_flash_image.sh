#!/usr/bin/env bash
# Сборка flash-образа Aura.
# Требует: archiso (pacman -S archiso), ~3 ГБ свободно.
set -euo pipefail

PROFILE="$HOME/.config/mkarchiso/aura-profile"
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$PROJECT/out"

echo "Aura flash image builder"
echo "Project: $PROJECT"
echo "Profile: $PROFILE"
echo ""

# Проверки
if ! command -v mkarchiso >/dev/null 2>&1; then
    echo "❌ archiso не установлен: sudo pacman -S archiso"
    exit 1
fi

if [ ! -d "$PROFILE" ]; then
    echo "❌ Профиль не найден: $PROFILE"
    echo "Создай: см. contrib/flash/mkarchiso-profile.txt"
    exit 1
fi

# Копирование проекта
echo "Копирую aura_project в профиль..."
rm -rf "$PROFILE/airootfs/root/aura_project"
cp -r "$PROJECT" "$PROFILE/airootfs/root/aura_project"
rm -rf "$PROFILE/airootfs/root/aura_project/venv"
rm -rf "$PROFILE/airootfs/root/aura_project/.git"

# Копирование auto-install
cp "$PROJECT/contrib/flash/install-aura.sh" \
   "$PROFILE/airootfs/root/install-aura.sh"
chmod +x "$PROFILE/airootfs/root/install-aura.sh"

# Сборка
echo "Сборка ISO (может занять 10-20 минут)..."
mkdir -p "$OUT"
sudo mkarchiso -v -w /tmp/aura-build -o "$OUT" "$PROFILE"

echo ""
echo "✅ Готово. ISO в $OUT"
ls -la "$OUT"/*.iso
