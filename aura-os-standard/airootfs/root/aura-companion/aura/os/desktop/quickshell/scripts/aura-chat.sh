#!/bin/bash
ACTION=$1
MESSAGE=$2
INBOX="$HOME/.cache/aura/chat_inbox.jsonl"
HISTORY="$HOME/.cache/aura/chat_history.jsonl"

if [ "$ACTION" == "send" ]; then
    # Экранируем кавычки и отправляем в формате JSONL
    SAFE_MSG=$(echo "$MESSAGE" | sed 's/"/\\"/g')
    echo "{\"user\": \"$SAFE_MSG\"}" >> "$INBOX"
elif [ "$ACTION" == "read" ]; then
    # Читаем последние 10 строк истории и выводим в читаемом виде
    if [ -f "$HISTORY" ]; then
        tail -n 10 "$HISTORY" | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        u = d.get('user', '')
        a = d.get('aura', '')
        if u: print(f'Вы: {u}')
        if a: print(f'Aura: {a}')
    except: pass
"
    else
        echo "История пуста"
    fi
fi
