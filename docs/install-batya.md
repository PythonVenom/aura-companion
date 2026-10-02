# Установка Aura — для бати

## Что нужно
Linux Mint 21/22 или Ubuntu 22.04+. Интернет. 3 ГБ. 10-15 мин.

## Установка

Открыть терминал (Ctrl+Alt+T):

curl -fsSL https://raw.githubusercontent.com/PythonVenom/aura-companion/master/install_universal.sh -o /tmp/aura.sh
bash /tmp/aura.sh

Скрипт спросит пароль sudo (один раз).

## После установки

systemctl --user start aura.service
xdg-open http://127.0.0.1:8765/ui

Сказать голосом: «Аура, который час».

## Если Aura залипла

python3 ~/aura_project/scripts/aura_ctl.py kill

## Логи

journalctl --user -u aura.service -f

## Что НЕ делать
- Не удалять ~/aura_project/
- Не запускать sudo без причины
