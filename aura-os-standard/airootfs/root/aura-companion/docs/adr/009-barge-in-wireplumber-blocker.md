# ADR-009: Barge-in — WirePlumber блокирует AEC default sink

## Дата
2026-09-22

## Статус
Принято (barge-in отключён, ждёт фикса AEC)

## Контекст

После ADR-007 (AEC через PipeWire echo-cancel) мы вернулись
к barge-in (ADR-006). Интегрировали `AgentBargeIn` в `aura_main.py`,
добавили gate против ложных срабатываний.

**Проверено:**
- AEC работает: RMS падает с 1770 до 10 при играющей музыке (мониторинг).
- WirePlumber 0.5.17.
- `pactl get-default-source` → `echo-cancel-source` ✅.
- `pactl get-default-sink` → `alsa_output...` ❌ (не echo-cancel-sink).

## Проблема

AEC вычитает из микрофона **сигнал, идущий в echo-cancel-sink**. Если
весь звук идёт в `alsa_output` (hardware), AEC не знает, что вычитать
→ эхо возвращается → VAD детектит голос Ауры → barge-in срабатывает
на себе.

**RMS тест подтвердил:** 1388 при молчащем пользователе и играющей
музыке. AEC не работает без правильного default sink.

## Что пробовали

1. `pactl set-default-sink echo-cancel-sink` — сбрасывается после
   рестарта WirePlumber.
2. `~/.config/pipewire/pipewire-pulse.conf.d/50-echo-cancel-default.conf`:
   `pulse.cmd` с `set-default-sink` — **не работает**.
   WirePlumber держит свой `default-nodes` state поверх.
3. `~/.config/wireplumber/wireplumber.conf.d/51-aura-aec.conf`:
   `wireplumber.settings.default-nodes.default-configured-audio-sink`
   — **не работает** (синтаксис 0.5 иной?).
4. Ручная правка `~/.local/state/wireplumber/default-nodes` —
   **не работает** (WirePlumber перезаписывает).
5. `chattr +i` на state — **не работает** (FS не поддерживает или
   нужен root).

**Результат:** все попытки не сработали.

## Решение

**Barge-in отключён в `aura_main.py` (закомментирован `barge_in.start()`).**

Код `barge_in.py` и интеграция **сохранены**. Это переключатель,
не откат. Возврат — после фикса AEC/WirePlumber.

**Почему:** ложное срабатывание barge-in хуже отсутствия. Аура
обрывает сама себя на полуслове. Для беты — неприемлемо.

## Что нужно для возврата

1. Изучить WirePlumber 0.5 конфиг API (это `~/.config/wireplumber/main.lua.d/`
   или новый формат). Найти правильный ключ для default sink.
2. ИЛИ: убрать WirePlumber, оставить чистый pipewire-pulse (радикально).
3. ИЛИ: при старте `aura_main.py` — `pactl set-default-sink echo-cancel-sink`
   (костыль, работает до рестарта).

## Связь

- ADR-006 — barge-in архитектура (провал без AEC)
- ADR-007 — AEC (source работает, sink не закреплён)
- ADR-009 (этот) — WirePlumber блокирует default sink

## Ссылки

- WirePlumber 0.5 documentation
- PipeWire `module-echo-cancel` requires sink_master + source_master
