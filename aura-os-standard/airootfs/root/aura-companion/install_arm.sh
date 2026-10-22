#!/usr/bin/env bash
# Aura installer для ARM64 (Raspberry Pi 4/5, ARM серверы)
set -euo pipefail

echo "=== Aura installer (ARM64) ==="
ARCH=$(uname -m)

if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "arm64" ]; then
    echo "Это не ARM64. Используй обычный install.sh"
    exit 1
fi

if command -v pacman >/dev/null; then
    ./install.sh
elif command -v apt >/dev/null; then
    ./install_ubuntu.sh
elif command -v dnf >/dev/null; then
    ./install_fedora.sh
elif command -v apk >/dev/null; then
    ./install_alpine.sh
else
    echo "Неизвестный дистрибутив"
    exit 1
fi

echo ""
echo "=== Готово (ARM64) ==="
echo "Примечание: LLM без GPU — медленнее."
