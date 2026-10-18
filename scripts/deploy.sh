#!/bin/bash
set -e # Останавливаем скрипт при любой ошибке

# Конфигурация
APP_DIR="/opt/aura"
BLUE_DIR="$APP_DIR/blue"
GREEN_DIR="$APP_DIR/green"
CURRENT_LINK="$APP_DIR/current"
REPO_URL="https://github.com/PythonVenom/aura-companion.git"

echo "=== Aura Blue-Green Deployer ==="

# Определяем, какая версия сейчас активна
if [ -L "$CURRENT_LINK" ]; then
    CURRENT_TARGET=$(readlink -f "$CURRENT_LINK")
    if [[ "$CURRENT_TARGET" == *"blue"* ]]; then
        NEW_DIR="$GREEN_DIR"
        TARGET_NAME="Green"
    else
        NEW_DIR="$BLUE_DIR"
        TARGET_NAME="Blue"
    fi
else
    NEW_DIR="$BLUE_DIR"
    TARGET_NAME="Blue"
fi

echo "1. Подготовка $TARGET_NAME директории..."
rm -rf "$NEW_DIR"
git clone "$REPO_URL" "$NEW_DIR"

echo "2. Установка зависимостей (venv)..."
cd "$NEW_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -e .

echo "3. Запуск тестов..."
if pytest -q; then
    echo "✅ Тесты пройдены. Переключаем трафик на $TARGET_NAME."
    ln -sfn "$NEW_DIR" "$CURRENT_LINK"
    systemctl --user restart aura.service aura-dbus.service
    echo "🚀 Деплой успешен! Активна версия: $TARGET_NAME"
else
    echo "❌ Тесты упали. Откат (оставляем текущую версию)."
    exit 1
fi
