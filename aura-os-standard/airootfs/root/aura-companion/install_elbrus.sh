#!/bin/bash
# Установка Aura на Эльбрус (E2K архитектура, ОС из реестра РФ).
# КРИТИЧНО: python3 на Эльбрусе имеет свои особенности (e2k).
set -e
echo "🚀 Aura installer — Эльбрус E2K"

# Проверка архитектуры
ARCH=$(uname -m)
if [ "$ARCH" != "e2k" ]; then
  echo "⚠️ Архитектура: $ARCH (ожидается e2k)."
fi

if ! command -v apt &>/dev/null; then
  echo "❌ apt не найден. Эльбрус = DEB-based."
  exit 1
fi

sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  portaudio19-dev libasound2-dev espeak-ng

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
# Некоторые wheel'ы могут отсутствовать для e2k — собираем из исходников
pip install --no-binary :all: numpy || pip install numpy
pip install -r requirements.txt

echo "✅ Aura установлена на Эльбрус. Запуск: .venv/bin/python aura_main.py"
