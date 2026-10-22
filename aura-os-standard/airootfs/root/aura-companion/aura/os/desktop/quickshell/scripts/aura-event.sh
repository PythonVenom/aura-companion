#!/bin/bash
# Единый логгер событий для Aura
# Использование: aura-event.sh <user|system|aura> <текст события>

ROLE=$1
CONTENT=$2
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
HISTORY_FILE="$HOME/aura-companion/chat_history"

# Формируем запись в формате JSONL (JSON Lines - золотой стандарт для логов)
# Aura сможет это легко прочитать и распарсить
JSON_LINE="{\"role\": \"$ROLE\", \"content\": \"$CONTENT\", \"timestamp\": \"$TIMESTAMP\"}"

echo "$JSON_LINE" >> "$HISTORY_FILE"

# Если это сообщение от пользователя, дублируем его в chat_inbox для обработки ядром
if [ "$ROLE" == "user" ]; then
    echo "$CONTENT" > "$HOME/aura-companion/chat_inbox"
fi
