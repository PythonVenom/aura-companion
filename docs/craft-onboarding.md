# Как мастеру начать с Aura

**Для:** ЧПУ-операторов, 3D-художников, дизайнеров, тату-мастеров,
музыкантов, автомехаников, врачей-процедурников.

## 5 минут

### 1. Установка (Arch)

    git clone https://github.com/PythonVenom/aura-companion ~/aura_project
    cd ~/aura_project
    ./install.sh

Установщик спросит 5 вопросов (имя, обращение, характер, юмор, голос).
**Для работы** — выбери профиль (см. ниже).

### 2. Профиль под профессию

    aura profile list
    aura profile set craft       # для ЧПУ, 3D, дизайнеров
    aura profile set medical     # для врачей/массажистов
    aura profile set dev         # для программистов
    aura profile set drive       # для водителей

### 3. Проверка

    aura doctor

## 3 сценария (проверены)

### A. ЧПУ (GRBL)

    # Подключить станок
    ls /dev/ttyUSB*  # найти порт
    
    # Голосом
    «Аура, статус станка»
    «Аура, homing»      # $H — безопасно
    
    # Опасное — с confirm (ADR-037)
    «Аура, перемести в X10 Y10»
    Аура: «⚠️ Движение G0 X10 Y10. Скажи да или нет»

### B. Blender (3D)

    # В Blender:
    blender --python scripts/aura_server.py
    
    # Голосом
    «Аура, состав сцены»
    «Аура, список объектов»
    «Аура, отрендери в /tmp/render.png»

### C. Figma (дизайн)

    # Получить token: https://www.figma.com/developers/api#access-tokens
    mkdir -p ~/.config/aura
    echo "figd_xxxxx" > ~/.config/aura/figma_token
    
    # Голосом
    «Аура, открой файл X»
    «Аура, экспортируй в PNG»

## Чего Aura НЕ делает (ADR-031)

- ❌ Не заменяет мастера
- ❌ Не даёт советов по технике безопасности на производстве
- ❌ Не управляет станком без confirm на опасных операциях

Aura — **инструмент**, решение — **за тобой**.

## Помощь

- `docs/professions.md` — 110+ профессий в 5 кластерах
- `docs/troubleshooting.md` — типовые проблемы
- `aura wrappers-hint` — подсказки по wrappers
- GitHub Issues — баги и предложения

## Обратная связь

Мастер? Расскажи, какие ещё команды нужны — GitHub Issues.
Aura строится под реальные боли, не под маркетинг.
