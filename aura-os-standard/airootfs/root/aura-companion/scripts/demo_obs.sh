#!/usr/bin/env bash
# Демо-сценарий для OBS (docs/demo.md).
# Показывает 6 сцен через CLI. Записывается через OBS поверх окна.
set -euo pipefail

cd ~/aura_project
source venv/bin/activate

hr() { echo ""; echo "════════════════════════════════════════════════"; echo ""; sleep 1; }
say() { echo ">>> $1"; sleep 2; }

clear
echo "════════════════════════════════════════════════"
echo "  Aura v1.0.0 — голосовой ИИ-компаньон"
echo "  37 агентов · 1079 тестов · MIT"
echo "════════════════════════════════════════════════"
sleep 3

hr; say "1. Время + погода"
python -m aura.cli check 2>&1 | tail -5

hr; say "2. Таймер"
python -m aura.cli timer 30s чай

hr; say "3. Метроном"
python -m aura.cli bpm 120

hr; say "4. Стройматериалы"
python -m aura.cli calc плитка 29

hr; say "5. Массаж"
python -m aura.cli massage start Демо 50

hr; say "6. Диктовка"
python -m aura.cli dictation text "спина L4-L5 напряжение"

hr
echo "GitHub: github.com/PythonVenom/aura-companion"
echo "Скачать: ./install.sh"
echo ""
