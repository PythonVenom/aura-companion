# ADR-034: Smart Home (MQTT)

**Дата:** 2026-09-28
**Статус:** Проект
**Связано:** strategy-2026.md

## Контекст

Home Assistant сложен для бабушки (YAML, entity_id).
Google Home / Alexa — облако → не для параноидальных.
Аура = голос + локально.

## Решение

**Aura Smart Home** — голосовой фасад над MQTT + Zigbee2MQTT.

### Агенты

- **LightAgent** — «свет на кухне», «выключи везде»
- **ClimateAgent** — «температура в спальне», «кондиционер 22»
- **SceneAgent** — «режим кино», «утро», «ушли»
- **SensorAgent** — «влажность в ванной»
- **LockAgent** — «закрой двери» (только подтверждение, ADR-015)

### Стек

- **MQTT** — paho-mqtt (Python)
- **Zigbee2MQTT** — мост для ламп/датчиков
- **Home Assistant** — опционально (Aura идёт как голосовой слой)
- **Matter/Thread** — позже (2027)

### Топики (convention)

    home/living_room/light/state    → on/off
    home/living_room/light/set      ← команды
    home/bedroom/climate/temp       → 22.5

### Команды

- «Аура, свет на кухне»
- «Аура, выключи весь свет»
- «Аура, режим кино» (димер 20%, шторы закрыть, TV on)
- «Аура, влажность?»
- «Аура, закрой входную дверь» → confirm (безопасность)

### Безопасность

- Двери/замки → **confirm** (как power)
- Whitelist устройств в settings.json
- Локальный брокер только (Mosquitto на localhost)

### НЕ делаем

- Облако (Tuya, Smart Life API) — privacy
- Автоматизации без согласия (YAGNI)

### Монетизация

- Free: до 10 устройств
- Pro: 490 ₽/мес — unlimited + сцены

## Связанные
- ADR-031 (Ethics)
- docs/strategy-2026.md (P2 Q3 2026)
