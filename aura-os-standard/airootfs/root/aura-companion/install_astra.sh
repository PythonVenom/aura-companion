#!/bin/bash
# Установка Aura на Astra Linux (DEB-based, ОС из реестра РФ).
# ADR-152 Tier0: Aura должна работать на Astra для гос-сектора.
set -e
echo "🚀 Aura installer — Astra Linux"

if ! [ -f /etc/astra_version ]; then
  echo "⚠️ Это не Astra Linux. /etc/astra_version не найден."
  echo "   Продолжаем на свой риск (APT должен быть доступен)."
fi

# Проверка apt
if ! command -v apt &>/dev/null; then
  echo "❌ apt не найден. Astra Linux должен быть DEB-based."
  exit 1
fi

# Системные пакеты
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  portaudio19-dev libasound2-dev espeak-ng \
  libgtk-3-0 gir1.2-gtk-3.0 \
  sqlcipher libsqlcipher0

# Venv
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Aura установлена на Astra Linux. Запуск: .venv/bin/python aura_main.py"
