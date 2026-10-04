# ADR-050: aura health v0.1 — read-only диагностика

**Статус:** Accepted
**Дата:** 2026-09-30
**Контекст:** Инцидент «Аура молчит» (mute + AURA_BRAIN=0) показал,
что диагностика вручную = 10+ команд, копипаст, потери времени.
Bug 66 (утечка потоков listener'а, +1/мин) не виден в journal.

## Решение

`scripts/aura_health.py` — утилита сопровождения (НЕ агент).

**Границы v0.1:**
- Только read-only: pgrep, systemctl status, /proc, pactl, journalctl -n.
- НЕ чинит, НЕ рестартит, НЕ пишет в файлы Aura.
- НЕ трогает ~/.config/systemd/user/.
- Вывод: один экран текста (grep-friendly).

**Границы v0.1 (чего НЕ делает):**
- НЕ парсит 37 агентов.
- НЕ имеет плагинов, конфигов, GUI, трея.
- НЕ вызывает pytest/py_compile (это отдельные инструменты).

## Проверки v0.1

1. Процесс aura_main жив? PID, systemd state.
2. CPU-дельта (top -b -n 2 -d 3).
3. Потоки: текущее число (Bug 66 baseline).
4. Аудио: default source RUNNING? source-outputs count.
5. Journal: последние 80 строк, grep error/traceback.

## Последствия

- Утренний запуск: `python3 scripts/aura_health.py`.
- v0.2+ (TBD): сохранение baseline, детект утечки между запусками,
  авто-фикс (отдельный ADR, с подтверждением — правило №7).
