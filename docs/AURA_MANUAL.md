# 🦾 AURA OS — Руководство Капитана
Добро пожаловать на борт.
## 1. Как включить и выключить
*   Включить: systemctl --user start aura.service aura-dbus.service
*   Выключить: systemctl --user stop aura.service aura-dbus.service
*   Перезапустить: systemctl --user restart aura.service
## 2. Как с ней общаться
*   Текстом: echo '{"user": "Твой запрос"}' >> ~/.cache/aura/chat_inbox.jsonl
*   Голосом: Скажи "Аура".
*   Перебить: Скажи "Стоп".
## 3. Примеры команд
*   "Прочитай файл README.md"
*   "Найди в интернете новости про Илона Маска"
*   "Сколько пользователей в таблице users в базе test.db"
*   "Покажи открытые issues в репозитории pythonvenom/aura-companion"
## 4. Логи
journalctl --user -u aura.service -n 50 --no-pager
