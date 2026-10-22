#!/bin/bash
# Отправляем команду в Aura, чтобы она начала слушать
# (В зависимости от твоей архитектуры, тут может быть dbus-send или запись в файл)
echo "Аура, слушай" > ~/aura-companion/chat_inbox
# Или, если у тебя настроен D-Bus:
# dbus-send --session --type=method_call --dest=org.aura.Companion /org/aura/Companion org.aura.Companion.Listen
