#!/usr/bin/env bash
# Aura installer для Windows Subsystem for Linux 2
set -euo pipefail

echo "=== Aura installer (WSL2) ==="

if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo "⚠️  Это не WSL. Используй обычный install.sh"
    exit 1
fi

# WSL2 использует Ubuntu/Debian чаще всего
if command -v apt >/dev/null; then
    ./install_ubuntu.sh
else
    echo "❌ Неизвестный дистрибутив в WSL"
    exit 1
fi

echo ""
echo "=== Готово (WSL2) ==="
echo "Примечания:"
echo "- Микрофон: работает через WSLg (Windows 11)"
echo "- systemd: нужен WSL 2.0+ (в /etc/wsl.conf: systemd=true)"
echo "- Firefox bridge: только в Windows-браузере, TBD"
