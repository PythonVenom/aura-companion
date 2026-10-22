#!/bin/bash
set -e

echo "========================================"
echo "🚀 УСТАНОВКА AURA OS (Local-First AI)"
echo "========================================"

# 1. Проверка прав
if [ "$EUID" -eq 0 ]; then
  echo "❌ Не запускайте скрипт от имени root. Используйте обычного пользователя."
  exit 1
fi

# 2. Установка системных зависимостей (Arch Linux)
echo "📦 Проверка системных зависимостей..."
if command -v pacman &> /dev/null; then
    sudo pacman -S --needed --noconfirm base-devel python python-pip git mpv ffmpeg nodejs npm pipewire pipewire-pulse
else
    echo "⚠️ Вы не на Arch Linux. Установите зависимости вручную: python, pip, mpv, ffmpeg, nodejs, npm."
fi

# 3. Установка Ollama
echo "🧠 Проверка Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Скачиваю и устанавливаю Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama уже установлена."
fi

# 4. Загрузка LLM-моделей
echo "📥 Загрузка моделей Qwen 2.5 и Nomic-Embed..."
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull nomic-embed-text

# 5. Настройка Python-окружения
echo "🐍 Настройка Python venv..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchaudio soundfile edge-tts duckduckgo-search  # Доустанавливаем специфичные пакеты

# 6. Скачивание нейроголоса MMS-TTS (Meta)
echo "🎙️ Скачивание нейроголоса MMS-TTS (Meta)..."
./venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='facebook/mms-tts-rus', local_dir='~/.cache/huggingface/mms-tts-rus')"

# 6.1 Проверка голосовой модели Piper (фолбэк)
echo "🎙️ Проверка голосовой модели Piper..."
VOICE_DIR="$HOME/.local/share/aura/voices"
VOICE_FILE="$VOICE_DIR/ru_RU-irina-medium.onnx"

mkdir -p "$VOICE_DIR"
if [ ! -f "$VOICE_FILE" ]; then
    echo "Скачиваю голосовую модель Ирины..."
    wget -O "$VOICE_FILE" https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx
    wget -O "${VOICE_FILE}.json" https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json
else
    echo "✅ Голосовая модель на месте."
fi

# 7. Настройка Systemd-сервиса
echo "⚙️ Настройка Systemd..."
mkdir -p ~/.config/systemd/user
cat << SERVICE > ~/.config/systemd/user/aura.service
[Unit]
Description=Aura Ship AI
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python aura_main.py --daemon
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=AURA_WAKE=1
TimeoutStopSec=5
KillMode=mixed

[Install]
WantedBy=default.target
SERVICE

systemctl --user daemon-reload
systemctl --user enable aura.service

echo "========================================"
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo "Запустите Aura командой:"
echo "  systemctl --user start aura.service"
echo "Посмотреть логи:"
echo "  journalctl --user -u aura.service -f"
echo "========================================"
