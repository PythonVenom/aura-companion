#!/data/data/com.termux/files/usr/bin/bash
# Aura installer для Android (Termux)
set -euo pipefail

echo "=== Aura installer (Android / Termux) ==="
echo "Project: $(pwd)"

# Termux packages
pkg update -y
pkg install -y python git ffmpeg termux-api

# venv не работает в Termux — используем системный python
pip install --upgrade pip
pip install -e .

echo ""
echo "=== Готово ==="
echo "Запусти: python -m aura_main"
echo ""
echo "ВНИМАНИЕ: На Android ограничено:"
echo "- Нет PipeWire (только termux-api)"
echo "- Нет MPRIS"
echo "- Firefox bridge — только через Termux:Firefox (TBD)"
