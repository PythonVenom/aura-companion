#!/bin/bash
# Aura chat send helper — читает stdin, пишет в chat_inbox.jsonl
set -e
TEXT="$1"
TS=$(python3 -c "import time; print(time.time())")
printf "{\"user\":\"%s\",\"ts\":%s}\n" "$TEXT" "$TS" >> "$HOME/.cache/aura/chat_inbox.jsonl"
