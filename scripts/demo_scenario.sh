#!/usr/bin/env bash
# Демо-сценарий Aura (Linux). ~90 сек.
set -euo pipefail
cd "$(dirname "$0")/.."

hr() { echo ""; echo "════════════════════════════"; echo ""; sleep 1; }

clear
echo "════════════════════════════════════════"
echo "  Aura v1.0.0 — голосовой ИИ-компаньон"
echo "  37 агентов · 1115 тестов · 48 ADR"
echo "  Всё локально: ASR + LLM + TTS + RAG"
echo "════════════════════════════════════════"
sleep 4

hr; echo ">>> 1. Таймер"; sleep 1
python -m aura.cli timer 30s чай; sleep 3

hr; echo ">>> 2. Метроном"; sleep 1
python -m aura.cli bpm 120; sleep 3

hr; echo ">>> 3. Стройматериалы"; sleep 1
python -m aura.cli calc плитка 29; sleep 3

hr; echo ">>> 4. Массаж"; sleep 1
python -m aura.cli massage start Демо 50; sleep 3

hr; echo ">>> 5. Диктовка"; sleep 1
python -m aura.cli dictation text "спина L4-L5 напряжение"; sleep 3

hr
echo "GitHub: github.com/PythonVenom/aura-companion"
echo "1115 тестов · 48 ADR · всё локально"
sleep 4
