#!/bin/bash
APP_NAME=$1
COMMAND=$2

# Проверяем, есть ли окно с таким именем в списке wmctrl
if wmctrl -l | grep -qi "$APP_NAME"; then
    # Если окно есть, активируем (разворачиваем) его
    wmctrl -a "$APP_NAME"
else
    # Если окна нет, запускаем приложение
    $COMMAND &
fi
