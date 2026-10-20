#!/bin/bash
ACTION=$1
MESSAGE=$2

if [ "$ACTION" == "send" ]; then
    # Отправляем через логгер с ролью "user"
    ~/.config/quickshell/scripts/aura-event.sh "user" "$MESSAGE"
elif [ "$ACTION" == "read" ]; then
    # Показываем последние 5 записей (убираем лишние кавычки для красоты)
    tail -n 5 ~/aura-companion/chat_history 2>/dev/null | sed 's/{"role": "//; s/", "content": "/: /; s/", "timestamp": ".*}//g' || echo "История пуста"
fi
