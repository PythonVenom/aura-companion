#!/bin/bash
set -e

APP_DIR="$HOME/aura-deploy"
BLUE_DIR="$APP_DIR/blue"
GREEN_DIR="$APP_DIR/green"
CURRENT_LINK="$APP_DIR/current"
REPO_URL="https://github.com/PythonVenom/aura-companion.git"

echo "=== Aura Blue-Green Deployer (Local Test) ==="

if [ -L "$CURRENT_LINK" ]; then
    CURRENT_TARGET=$(readlink -f "$CURRENT_LINK")
    if [[ "$CURRENT_TARGET" == *"blue"* ]]; then
        NEW_DIR="$GREEN_DIR"; TARGET_NAME="Green"
    else
        NEW_DIR="$BLUE_DIR"; TARGET_NAME="Blue"
    fi
else
    NEW_DIR="$BLUE_DIR"; TARGET_NAME="Blue"
fi

echo "1. Подготовка $TARGET_NAME директории..."
mkdir -p "$APP_DIR"
rm -rf "$NEW_DIR"
git clone "$REPO_URL" "$NEW_DIR"

echo "2. Установка зависимостей (venv)..."
cd "$NEW_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -e . > /dev/null 2>&1

echo "3. Запуск тестов..."
if pytest -q; then
    echo "✅ Тесты пройдены. Переключаем трафик на $TARGET_NAME."
    ln -sfn "$NEW_DIR" "$CURRENT_LINK"
    echo "🚀 Деплой успешен! Активна версия: $TARGET_NAME"
    echo "Чтобы система использовала эту версию, обнови WorkingDirectory в aura.service"
else
    echo "❌ Тесты упали. Откат (оставляем текущую версию)."
    exit 1
fi
