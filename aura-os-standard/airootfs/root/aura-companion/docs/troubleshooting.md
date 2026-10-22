# Troubleshooting Aura

## Аура не слышит

### 1. Проверить микрофон

    arecord -d 3 /tmp/test.wav && aplay /tmp/test.wav

Если не слышишь себя — микрофон не работает.

### 2. Поднять уровень

    alsamixer

F4 -> Capture -> стрелками до 100%.

### 3. Проверить PipeWire

    pactl info | grep "Default Source"

Default Source должен быть физическим микрофоном, не echo-cancel-source.

## Аура молчит

### 1. Проверить логи

    journalctl --user -u aura.service --since "2 minutes ago"

Ищи ошибки.

### 2. Проверить динамики

    speaker-test -t sine -l 1

## Firefox bridge не работает

### 1. Проверить расширение

Открой about:debugging#/runtime/this-firefox

Должно быть Aura Bridge.

### 2. Перезагрузить (правило MV2)

- Remove расширения
- Load Temporary Add-on
- Выбрать ~/aura_project/firefox_extension/manifest.json
- F5 на вкладке Макс

### 3. Проверить native host

    cat ~/.mozilla/native-messaging-hosts/aura_bridge.json
    ps aux | grep aura_firefox

## Троение звука

    pactl info | grep "Default Sink"

Если echo-cancel-sink — это баг. Исправь вручную:

    pactl set-default-sink alsa_output.pci-0000_00_1f.3.analog-stereo

## Аура не зачитывает сообщения

### 1. Проверить Макс в Firefox

Открой web.max.ru, авторизуйся.

### 2. Проверить логи Proactive

    journalctl --user -u aura.service | grep Proactive

### 3. Проверить таймаут

pending_read — 180 секунд. Если говоришь долго — может истечь.

## Чек-лист не работает

    cat ~/aura_private/CHECKLIST.md

Если файла нет — создай:

    mkdir -p ~/aura_private
    echo "# Чек-лист" > ~/aura_private/CHECKLIST.md

## Ошибка в install.sh

### 1. Проверить system_check

    cd ~/aura_project
    python3 -m aura.system_check

### 2. Dry-run

    ./install.sh --dry-run

### 3. Логи

    cat /tmp/aura_install.log

## Диагностика

### Health check

    cd ~/aura_project
    source venv/bin/activate
    python -m aura.cli health

Выведет JSON: статус сервиса, FSM, календарь.

### System check

    python -m aura.system_check

Покажет CPU, RAM, GPU, аудио, оценку LLM.

### Metrics

    python -m aura.metrics

Prometheus text format.
