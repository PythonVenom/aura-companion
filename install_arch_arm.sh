#!/usr/bin/env bash
# Aura installer для Arch Linux ARM (Raspberry Pi 4/5)
set -euo pipefail

echo "=== Aura installer (Arch ARM) ==="
ARCH=$(uname -m)

if [ "$ARCH" != "aarch64" ]; then
    echo "Это не ARM64. Используй обычный install.sh"
    exit 1
fi

if ! command -v pacman >/dev/null; then
    echo "pacman не найден. Это не Arch."
    exit 1
fi

# Arch ARM: те же пакеты, что и x86
./install.sh

echo ""
echo "=== Готово (Arch ARM64) ==="
echo "Примечания:"
echo "- LLM работает на CPU"
echo "- 7B модель влезает в 8 ГБ RAM"
echo "- Piper/T-one работают нормально"
