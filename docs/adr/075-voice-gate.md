# ADR-075: VoiceGate — VAD перед ASR

**Дата:** 2026-10-02
**Статус:** Принято

## Контекст

Bug 72: ASR (T-one) постоянно ловит фоновую речь (ТВ/музыка/чужой разговор)
и возвращает мусор. Journal за 10 мин: «джой», «так», «нагулялся», «давай ид».

## Решение

`aura/core/vad.py:VoiceGate` — обёртка над webrtcvad (уже в venv, barge_in).
- mode=2 (balanced): 3-frame окно, ≥2 speech → валидный
- aggressiveness=3 (строгий)
- frame_ms=30 (совместимо с listener blocksize=480 @ 16kHz)

Интеграция в `listener.listen()`:
- Перед accept_waveform: VAD-проверка `data.tobytes()`.
- VAD=False → skip accept_waveform (ASR не видит шум).
- При ошибке VAD — fallback (accept=True).

## Последствия

- Ложные активации от фоновой речи отсекаются
- CPU: ASR реже вызывает decode
- Минимальная инвазия: 1 блок в цикле listen

## Ссылки
- ADR-007 (AEC), ADR-052 (16kHz), Bug 72
