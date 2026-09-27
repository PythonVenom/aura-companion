# Аудит проекта Aura

Дата: 2026-09-28
Версия: v0.9.0-alpha

## Метрики

| Метрика | Значение |
|---|---|
| Тесты | 839 passed |
| Агенты | 27 |
| ADR | 19 |
| Лицензия | MIT |
| CI | зелёный |

## Компоненты

### Production-ready
- Голосовой цикл
- T-one ASR (RTF 0.058)
- Piper TTS (~300 мс)
- VLC/MPRIS
- ProactiveEngine (5 триггеров)
- ChatSense
- AgentChecklist
- Firefox bridge (Макс)
- Platform Abstraction Layer

### Beta
- VK Web адаптер
- Telegram Web адаптер
- calendar_reminder, upcoming_calendar
- 24/7 стабильность (в прогоне)

### Заготовки
- AT-SPI, MCP
- Windows/macOS PAL
- Flash-install

## Технический долг

1. VK/Telegram live-верификация — 🔴
2. Bug 15 (Анастасия) — 🔴
3. Speaker race — 🟡
4. ASR на шуме — 🟡

## Риски

1. Санкции — AMD/Intel
2. Hardware — Strix Halo
3. Один разработчик — bus factor = 1
4. ASR на шуме
